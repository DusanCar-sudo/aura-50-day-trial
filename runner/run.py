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
MODEL = "deepseek/deepseek-chat"

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


def load_questions(tier=None, question_id=None):
    questions = []
    for f in sorted(QUESTIONS_DIR.glob("tier*.json")):
        questions.extend(json.loads(f.read_text()))
    if tier:
        questions = [q for q in questions if q["tier"] == tier]
    if question_id:
        questions = [q for q in questions if q["id"] == question_id]
    return questions


def build_command(question: dict, zero_memory: bool) -> list:
    cmd = [
        "aura",
        "-m", MODEL,
        "--auto",
        "--readonly",
        "--max-turns", str(question.get("max_turns", 3)),
    ]
    if zero_memory:
        cmd.append("--new-session")
    cmd.append(question["question"])
    return cmd


def run_question(question: dict, zero_memory: bool) -> dict:
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
    deadline = start + 180
    try:
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                proc.kill()
                timed_out = True
                break
            ready, _, _ = select.select([master_fd], [], [], remaining)
            if not ready:
                proc.kill()
                timed_out = True
                break
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                # Slave side closed — process finished.
                break
            if not chunk:
                break
            chunks.append(chunk)
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
        raise subprocess.TimeoutExpired(cmd, 180)

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


def run_benchmark(session_number: int, tier=None, question_id=None, zero_memory=False):
    questions = load_questions(tier=tier, question_id=question_id)
    if not questions:
        print("No questions found.")
        return None

    mode = "ZERO MEMORY (--new-session)" if zero_memory else "accumulated memory"
    print(f"Running {len(questions)} questions for session {session_number} [{mode}] against {MODEL} (escalation target; Ruby's local model comes from .aura.json)...")

    results = {
        "session": session_number,
        "model": MODEL,
        "zero_memory": zero_memory,
        "timestamp": datetime.utcnow().isoformat(),
        "questions": [],
    }

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
        try:
            result = run_question(q, zero_memory)
        except subprocess.TimeoutExpired:
            result = {
                "id": q["id"], "tier": q["tier"], "question": q["question"],
                "answer": "", "score": {"verdict": "incorrect", "note": "timed out"},
                "elapsed_seconds": 180, "exit_code": -1,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except FileNotFoundError:
            print("  ✗ 'aura' binary not found on PATH — aborting run.")
            return None
        results["questions"].append(result)
        recorder.append_answer_md(session_number, result["id"], result.get("answer", ""))
        mark = "✓" if result["score"]["verdict"] == "correct" else ("~" if result["score"]["verdict"] == "partial" else "✗")
        print(f"  {mark} {result['score']['verdict']} in {result['elapsed_seconds']}s")
        if result.get("exit_code", 0) != 0:
            print(f"    stderr: {result.get('stderr', '')[:200]}")

    out_file = recorder.save_session(results)
    print(f"\nResults saved to {out_file}")

    total = len(results["questions"])
    correct = sum(1 for q in results["questions"] if q["score"]["verdict"] == "correct")
    print(f"Pass rate: {correct}/{total} ({round(100*correct/total,1)}%)")

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--tier", type=int, default=None)
    ap.add_argument("--question", default=None)
    ap.add_argument("--zero-memory", action="store_true", help="Use --new-session to force Aura to ignore accumulated memory (Session 0 baseline)")
    args = ap.parse_args()

    run_benchmark(args.session, tier=args.tier, question_id=args.question, zero_memory=args.zero_memory)
