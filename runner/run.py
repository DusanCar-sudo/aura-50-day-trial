#!/usr/bin/env python3
"""
Aura Benchmark Runner — runs through the actual Aura agent, not naked Ollama.

Session 0 (zero memory):  --new-session forces Aura to ignore accumulated history/memory.
Session 1+ (real memory): default session behavior, Aura's persistent memory applies.

Usage:
    python3 runner/run.py --session 1
    python3 runner/run.py --session 0 --zero-memory
    python3 runner/run.py --session 2 --tier 4
    python3 runner/run.py --session 2 --question t4-01
"""

import json
import time
import subprocess
import argparse
import os
import pty
import select
import re
import fcntl
import termios
import struct
import threading
from datetime import datetime
from pathlib import Path

import scorer
import recorder

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

# This is the TOP-LEVEL / escalation ("papa") model passed via -m.
# It is NOT Ruby's local model — Ruby's local model (granite4.1:3b) comes
# from this project's .aura.json "ruby.modelName" config, and is only used
# when .aura.json has "ruby": { "enabled": true, ... }.
# Setting this to the local model too (as it was before) makes Ruby
# escalate to itself, which defeats the point of the alternator entirely.
MODEL = os.environ.get("AURA_BENCH_MODEL", "deepseek/deepseek-chat")


LIVE_JSON = ROOT / "results" / "live.json"
LIVE_JS = ROOT / "results" / "live.js"

# Banner TTL (seconds): how long the dashboard LIVE banner stays visible after
# the last heartbeat. Generous while running (dashboard polls every 10s),
# longer once finished so the final result can be reviewed before it fades.
LIVE_TTL_RUNNING = 300  # question can take minutes; heartbeat refreshes every 30s
LIVE_TTL_DONE = 900


def _archimedes_model() -> str:
    """Local first-attempt model from .aura.json (shown on the live banner)."""
    try:
        cfg = json.loads((ROOT / ".aura.json").read_text())
        return cfg.get("archimedes", {}).get("modelName", "unknown")
    except Exception:
        return "unknown"


def write_live_state(results: dict, questions: list, current=None,
                     started_epoch: float = None, status: str = "running") -> None:
    """
    Write results/live.json + results/live.js so the dashboard can show live
    per-tier question results while a benchmark run is in progress.

    live.js is a tiny JS file setting window.LIVE = {...}; — the dashboard
    polls it via a cache-busted <script> tag, which works from file:// too
    (no CORS, unlike fetch).
    """
    qs = results.get("questions", [])
    total = len(questions)
    done = len(qs)
    correct = sum(1 for q in qs if q["score"]["verdict"] == "correct")
    partial = sum(1 for q in qs if q["score"]["verdict"] == "partial")
    incorrect = done - correct - partial

    tiers: dict = {}
    for q in qs:
        t = str(q["tier"])
        e = tiers.setdefault(t, {"correct": 0, "partial": 0, "incorrect": 0})
        e[q["score"]["verdict"]] += 1

    elapsed = round(time.time() - started_epoch, 1) if started_epoch else 0
    eta = round(elapsed / done * (total - done), 1) if done and total > done else None

    state = {
        "status": status,
        "session": results["session"],
        "model": results["model"],
        "archimedes": _archimedes_model(),
        "started_at": results.get("timestamp"),
        "updated_at": datetime.utcnow().isoformat(),
        "banner_ttl": LIVE_TTL_DONE if status == "done" else LIVE_TTL_RUNNING,
        "current": {"id": current["id"], "tier": current["tier"], "question": current["question"][:80]}
                   if current else None,
        "total": total,
        "done": done,
        "correct": correct,
        "partial": partial,
        "incorrect": incorrect,
        "pass_rate": round(correct / total, 3) if total else 0,
        "elapsed_seconds": elapsed,
        "eta_seconds": eta,
        "tiers": tiers,
        "questions": [
            {"id": q["id"], "tier": q["tier"], "verdict": q["score"]["verdict"],
             "score": q["score"].get("score", 0.0), "elapsed_seconds": q.get("elapsed_seconds", 0)}
            for q in qs
        ],
    }
    (ROOT / "results").mkdir(exist_ok=True)
    LIVE_JSON.write_text(json.dumps(state, indent=2))
    LIVE_JS.write_text("window.LIVE = " + json.dumps(state) + ";\n")


def start_live_heartbeat(state: dict) -> threading.Thread:
    """
    Refresh results/live.json every 30s while a question is in flight, so the
    dashboard banner TTL never expires mid-question (questions take minutes;
    write_live_state is only called once per completed question otherwise).
    """
    def tick():
        while state.get("alive"):
            time.sleep(30)
            if state.get("alive"):
                try:
                    write_live_state(state["results"], state["questions"],
                                     current=state.get("current"),
                                     started_epoch=state["started_epoch"],
                                     status="running")
                except Exception:
                    pass
    t = threading.Thread(target=tick, daemon=True)
    t.start()
    return t

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    """Strip ANSI escape/color/cursor codes from PTY-captured output."""
    return ANSI_ESCAPE.sub('', text)


def set_pty_size(fd, rows=50, cols=160):
    """
    pty.openpty() creates a PTY with an UNSET (effectively 0x0) window size
    by default. Aura's renderer computes bar/padding widths from the
    terminal's column count (e.g. '░'.repeat(width - offset) for the
    context bar) — with width at 0, that goes negative, and JS's
    String.repeat() throws RangeError: Invalid count value on any
    negative number. Setting a real size here fixes it at the source.
    """
    winsize = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def _proc_read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return "<unreadable>"


def dump_child_state(pid: int) -> str:
    """
    Snapshot of what the (alive but silent) child is blocked on, from /proc.
    wchan/syscall distinguish "waiting on a socket read" (network call in
    flight, e.g. a queued Ollama request) from "waiting on stdin/pipe" or
    a futex. Open fds show which sockets/files are actually held.
    """
    lines = []
    status = _proc_read(f"/proc/{pid}/status")
    state = next((l for l in status.splitlines() if l.startswith("State:")), "State: ?")
    lines.append(f"    pid {pid}: {state.strip()}  wchan={_proc_read(f'/proc/{pid}/wchan')}")
    lines.append(f"    syscall: {_proc_read(f'/proc/{pid}/syscall')}")
    fds = []
    try:
        for fd in sorted(os.listdir(f"/proc/{pid}/fd"), key=int):
            try:
                fds.append(f"{fd}->{os.readlink(f'/proc/{pid}/fd/{fd}')}")
            except OSError:
                pass
    except OSError:
        fds.append("<unreadable>")
    lines.append("    fds: " + "  ".join(fds))
    # TCP sockets: map inodes to remote endpoints so "stuck on a socket"
    # becomes "stuck on a socket to 127.0.0.1:11434 (Ollama)".
    inodes = {f.split("socket:[")[1].rstrip("]") for f in fds if "socket:[" in f}
    if inodes:
        conns = []
        for tcp in (f"/proc/{pid}/net/tcp", f"/proc/{pid}/net/tcp6"):
            for line in _proc_read(tcp).splitlines()[1:]:
                parts = line.split()
                if len(parts) > 9 and parts[9] in inodes:
                    def hexaddr(a):
                        h, p = a.split(":")
                        if len(h) == 8:
                            ip = ".".join(str(int(h[i:i+2], 16)) for i in (6, 4, 2, 0))
                        else:
                            ip = h  # ipv6, leave raw
                        return f"{ip}:{int(p, 16)}"
                    conns.append(f"{hexaddr(parts[1])} -> {hexaddr(parts[2])} st={parts[3]}")
        if conns:
            lines.append("    tcp: " + "  ".join(conns))
    kids = _proc_read(f"/proc/{pid}/task/{pid}/children").split()
    for k in kids:
        kstate = next((l for l in _proc_read(f"/proc/{k}/status").splitlines()
                       if l.startswith("State:")), "State: ?")
        lines.append(f"    child {k}: {kstate.strip()}  wchan={_proc_read(f'/proc/{k}/wchan')}")
    return "\n".join(lines)


def load_questions(tier=None, question_id=None):
    questions = []
    for f in sorted(QUESTIONS_DIR.glob("tier*.json")):
        questions.extend(json.loads(f.read_text()))
    if tier:
        tiers = [int(t.strip()) for t in str(tier).split(",") if t.strip()]
        questions = [q for q in questions if q["tier"] in tiers]
    if question_id:
        questions = [q for q in questions if q["id"] == question_id]
    return questions


def build_command(question: dict, zero_memory: bool) -> list:
    cmd = [
        "aura",
        "-m", MODEL,
        "--auto",
        "--max-turns", str(question.get("max_turns", 3)),
    ]
    # Tiers 1-30 safe in readonly; tiers 31+ need write access
    if question.get("tier", 0) <= 30:
        cmd.append("--readonly")
    if zero_memory:
        cmd.append("--new-session")
    cmd.append(question["question"])
    return cmd


def run_question(question: dict, zero_memory: bool, trace: bool = False) -> dict:
    """
    Spawns Aura through a real PTY, not a plain pipe. Aura's terminal-aware
    renderer produces literal '?' placeholder characters for streamed
    content when it detects no real TTY (e.g. under plain subprocess.run
    with capture_output=True) — a PTY makes it behave the same as when
    run directly by hand in a terminal.
    """
    start = time.time()
    cmd = build_command(question, zero_memory)

    master_fd, slave_fd = pty.openpty()
    set_pty_size(slave_fd)

    env = os.environ.copy()
    # Aura_Benchmark isn't a git repo — silence the resulting
    # "not a git repository" warning from cluttering captured output.
    env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"

    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=str(ROOT),
        close_fds=True,
        env=env,
    )
    os.close(slave_fd)

    chunks = []
    timed_out = False
    # Archimedes's local model generates at ~15 tok/s warm; a full inner
    # attempt (up to min(--max-turns, 15) turns at 60-150s each) plus the
    # DeepSeek escalation can legitimately take 6-9 minutes. 180s/300s
    # produced false timeouts that looked like model failures.
    deadline = start + 600
    # PTY-read tracing: an LLM call in flight produces zero PTY output, so a
    # silent child is not necessarily hung — but past ~30s of silence we dump
    # its /proc state to tell "blocked on a socket to Ollama/API" apart from
    # "blocked on stdin" or a genuine wedge.
    total_bytes = 0
    window_bytes = 0
    window_start = start
    last_data = start
    next_stall_report = 30.0
    try:
        while True:
            now = time.time()
            remaining = deadline - now
            if remaining <= 0:
                proc.kill()
                timed_out = True
                break
            if trace and now - window_start >= 5.0:
                print(f"    [trace t+{now - start:6.1f}s] {window_bytes}B in last "
                      f"{now - window_start:.1f}s ({total_bytes}B total)", flush=True)
                window_bytes = 0
                window_start = now
            # Wake at least every 5s so stall detection runs even with no data.
            ready, _, _ = select.select([master_fd], [], [], min(remaining, 5.0))
            if not ready:
                silent = time.time() - last_data
                if silent >= next_stall_report:
                    if proc.poll() is None:
                        print(f"    [stall] no PTY output for {silent:.0f}s "
                              f"(child pid {proc.pid} alive, {total_bytes}B so far):", flush=True)
                        print(dump_child_state(proc.pid), flush=True)
                    next_stall_report += 30.0
                continue
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                # Slave side closed — process finished.
                break
            if not chunk:
                break
            chunks.append(chunk)
            total_bytes += len(chunk)
            window_bytes += len(chunk)
            last_data = time.time()
            next_stall_report = 30.0
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        timed_out = True

    if timed_out:
        # Preserve whatever output was captured before the kill — losing it
        # made timeout runs undebuggable (empty answer, no trace of what
        # the agent was doing when the deadline hit).
        raise subprocess.TimeoutExpired(cmd, 600, output=b"".join(chunks))

    raw_output = b"".join(chunks).decode("utf-8", errors="replace")
    answer = strip_ansi(raw_output).strip()

    verdict = scorer.score(question, answer)
    elapsed = round(time.time() - start, 2)

    # stdout/stderr are merged on a PTY — no clean separation possible.
    # Best-effort: surface the tail of output as "stderr" only on failure,
    # for debugging, not as a true separate stream.
    stderr_field = answer[-500:] if proc.returncode != 0 else ""

    return {
        "id": question["id"],
        "tier": question["tier"],
        "question": question["question"],
        "command": " ".join(cmd),
        "answer": answer,
        "stderr": stderr_field,
        "score": verdict,
        "elapsed_seconds": elapsed,
        "exit_code": proc.returncode,
        "timestamp": datetime.utcnow().isoformat(),
    }


def run_benchmark(session_number: int, tier=None, question_id=None, zero_memory=False,
                  trace=False, resume=False, keep_going=False):
    all_questions = load_questions(tier=tier, question_id=question_id)
    if not all_questions:
        print("No questions found.")
        return None

    mode = "ZERO MEMORY (--new-session)" if zero_memory else "accumulated memory"
    print(f"Running {len(all_questions)} questions for session {session_number} [{mode}] against {MODEL} (escalation target; Ruby's local model comes from .aura.json)...")

    results = {
        "session": session_number,
        "model": MODEL,
        "zero_memory": zero_memory,
        "timestamp": datetime.utcnow().isoformat(),
        "questions": [],
    }

    questions = all_questions
    if resume:
        prior_file = ROOT / "results" / f"session_{session_number:03d}.json"
        if prior_file.exists():
            prior = json.loads(prior_file.read_text())
            prior_qs = [q for q in prior.get("questions", []) if q.get("score")]
            done_ids = {q["id"] for q in prior_qs}
            # Drop recovery metadata — a resumed run finishes the session for real.
            results.pop("interrupted", None)
            results["questions"] = prior_qs
            results["resumed_from"] = prior_file.name
            questions = [q for q in all_questions if q["id"] not in done_ids]
            print(f"Resuming session {session_number}: {len(prior_qs)} already answered "
                  f"(from {prior_file.name}), {len(questions)} to go.")
        else:
            print(f"--resume: no {prior_file.name} to resume from — starting fresh.")

    started_epoch = time.time()
    live_state = {
        "alive": True,
        "results": results,
        "questions": all_questions,
        "started_epoch": started_epoch,
        "current": questions[0] if questions else None,
    }
    write_live_state(results, all_questions, current=live_state["current"],
                     started_epoch=started_epoch, status="running")
    heartbeat = start_live_heartbeat(live_state)

    # Session 10003 lost 3 hours to a dead escalation backend: every question
    # came back "verification error: HTTP 402 Insufficient Balance" from the
    # first one, but the runner kept going. Abort after N consecutive provider
    # failures — the checkpoint file keeps what was genuinely answered.
    provider_down_re = re.compile(r"Provider error[^\n]*HTTP 40[12]|Insufficient Balance")
    consecutive_provider_errors = 0
    abort_reason = None

    for i, q in enumerate(questions, 1):
        live_state["current"] = q
        print(f"[{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        try:
            result = run_question(q, zero_memory, trace=trace)
        except subprocess.TimeoutExpired as e:
            partial = strip_ansi((e.output or b"").decode("utf-8", errors="replace")).strip()
            result = {
                "id": q["id"], "tier": q["tier"], "question": q["question"],
                "answer": partial, "score": {"verdict": "incorrect", "note": "timed out"},
                "elapsed_seconds": 600, "exit_code": -1,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except FileNotFoundError:
            print("  ✗ 'aura' binary not found on PATH — aborting run.")
            abort_reason = "'aura' binary not found on PATH"
            recorder.save_session(results)
            live_state["alive"] = False
            write_live_state(results, all_questions, current=None,
                             started_epoch=started_epoch, status="aborted")
            return None
        results["questions"].append(result)
        recorder.append_answer_md(session_number, result["id"], result.get("answer", ""))
        mark = "✓" if result["score"]["verdict"] == "correct" else ("~" if result["score"]["verdict"] == "partial" else "✗")
        print(f"  {mark} {result['score']['verdict']} in {result['elapsed_seconds']}s")
        if result.get("exit_code", 0) != 0:
            print(f"    stderr: {result.get('stderr', '')[:200]}")

        # Checkpoint after every question: a crashed/OOM-killed run leaves a
        # valid partial session_*.json (verdicts + answers), not just live.json.
        recorder.save_session(results)

        if not keep_going and provider_down_re.search(result.get("answer", "")):
            consecutive_provider_errors += 1
            if consecutive_provider_errors >= 5:
                abort_reason = ("escalation provider down — 5 consecutive answers with "
                                "provider errors (HTTP 401/402/Insufficient Balance)")
                break
        else:
            consecutive_provider_errors = 0

        next_q = questions[i] if i < len(questions) else None
        live_state["current"] = next_q
        write_live_state(results, all_questions, current=next_q,
                         started_epoch=started_epoch, status="running")

    if abort_reason:
        results["aborted"] = {"reason": abort_reason,
                              "completed": len(results["questions"]),
                              "total_planned": len(all_questions),
                              "timestamp": datetime.utcnow().isoformat()}
        live_state["alive"] = False
        write_live_state(results, all_questions, current=None,
                         started_epoch=started_epoch, status="aborted")
        out_file = recorder.save_session(results)
        print(f"\n✗ ABORTED after {len(results['questions'])}/{len(all_questions)}: {abort_reason}")
        print(f"Partial results saved to {out_file}")
        print(f"Finish later with: python3 runner/run.py --session {session_number} --resume")
        return results

    live_state["alive"] = False
    write_live_state(results, all_questions, current=None,
                     started_epoch=started_epoch, status="done")
    out_file = recorder.save_session(results)
    print(f"\nResults saved to {out_file}")

    total = len(results["questions"])
    correct = sum(1 for q in results["questions"] if q["score"]["verdict"] == "correct")
    print(f"Pass rate: {correct}/{total} ({round(100*correct/total,1)}%)")

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--tier", default=None, help="Tier number or comma list, e.g. 3,4")
    ap.add_argument("--question", default=None)
    ap.add_argument("--zero-memory", action="store_true", help="Use --new-session to force Aura to ignore accumulated memory (Session 0 baseline)")
    ap.add_argument("--trace", action="store_true", help="Log PTY bytes/sec windows (stall detection with /proc dumps is always on)")
    ap.add_argument("--resume", action="store_true", help="Skip questions already answered in results/session_NNN.json (finished an interrupted run)")
    ap.add_argument("--keep-going", action="store_true", help="Do not abort on consecutive provider errors (default: abort after 5)")
    args = ap.parse_args()

    run_benchmark(args.session, tier=args.tier, question_id=args.question,
                  zero_memory=args.zero_memory, trace=args.trace,
                  resume=args.resume, keep_going=args.keep_going)
