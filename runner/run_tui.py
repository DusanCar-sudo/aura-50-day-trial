#!/usr/bin/env python3
"""
Aura Benchmark TUI Runner — drives the REAL interactive TUI through a PTY,
one continuous session for all questions, exactly as a real user would type
them in. This is the runner for the actual 50-day trial.

Boundary detection (two-phase, the key fix over the first draft):
1. After sending a question, wait for the prompt marker to DISAPPEAR —
   confirming Aura actually started processing (not just echoing input).
2. Then wait for the prompt marker to REAPPEAR — confirming the response
   is complete and Aura is ready for the next question.

Usage:
    python3 runner/run_tui.py --session 1
    python3 runner/run_tui.py --session 2 --tier 4
    python3 runner/run_tui.py --session 2 --question t1-01
"""

import json
import os
import pty
import re
import select
import struct
import fcntl
import termios
import time
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import scorer
import recorder

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

LARGE_MODEL = "deepseek/deepseek-chat"

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

PROMPT_MARKER = "type a task"
STARTUP_TIMEOUT = 45
QUESTION_TIMEOUT = 240


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


def set_pty_size(fd, rows=50, cols=160):
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


class TuiSession:
    def __init__(self, model: str, cwd: Path):
        self.master_fd, slave_fd = pty.openpty()
        set_pty_size(slave_fd)
        env = os.environ.copy()
        env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] = "1"
        self.proc = subprocess.Popen(
            ["aura", "-m", model, "--auto"],
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            cwd=str(cwd), close_fds=True, env=env,
        )
        os.close(slave_fd)
        self._buffer = ""

    def _read_chunk(self, timeout: float) -> str:
        ready, _, _ = select.select([self.master_fd], [], [], timeout)
        if not ready:
            return ""
        try:
            data = os.read(self.master_fd, 8192)
            chunk = data.decode("utf-8", errors="replace")
            self._buffer += chunk
            return chunk
        except OSError:
            return ""

    def _read_until(self, marker: str, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            self._read_chunk(min(remaining, 0.5))
            if marker in strip_ansi(self._buffer):
                return True
            if self.proc.poll() is not None:
                return False
        return False

    def _read_until_gone(self, marker: str, timeout: float) -> bool:
        """Read until marker is NO LONGER in recent output."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._read_chunk(0.2)
            # Check only the last 2000 chars — marker may still appear in
            # older buffered output from startup/prior turns
            recent = strip_ansi(self._buffer[-2000:])
            if marker not in recent:
                return True
        return False

    def wait_ready(self, timeout: float = STARTUP_TIMEOUT):
        if not self._read_until(PROMPT_MARKER, timeout):
            raise TimeoutError(f"TUI never became ready after {timeout}s")

    def ask(self, question: str, timeout: float = QUESTION_TIMEOUT) -> str:
        """
        Two-phase boundary detection:
        1. Send question + Enter
        2. Wait for PROMPT_MARKER to disappear from recent output (Aura processing)
        3. Wait for PROMPT_MARKER to reappear (response complete)
        Return captured output for this turn only.
        """
        # Capture only this turn's output
        turn_start_len = len(self._buffer)

        os.write(self.master_fd, question.encode() + b"\r")

        # Phase 1: prompt disappears (Aura started working)
        if not self._read_until_gone(PROMPT_MARKER, 30):
            raise TimeoutError("Prompt never disappeared — input may not have been received")

        # Phase 2: prompt reappears (response complete)
        if not self._read_until(PROMPT_MARKER, timeout):
            raise TimeoutError(f"Response never completed after {timeout}s")

        turn_output = self._buffer[turn_start_len:]
        return strip_ansi(turn_output).strip()

    def quit(self):
        try:
            os.write(self.master_fd, b":q\r")
            time.sleep(2)
        except OSError:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        try:
            os.close(self.master_fd)
        except OSError:
            pass


def run_benchmark(session_number: int, tier=None, question_id=None):
    questions = load_questions(tier=tier, question_id=question_id)
    if not questions:
        print("No questions found.")
        return None

    print(f"Running {len(questions)} questions for session {session_number} "
          f"[TUI, one continuous session, accumulated memory] against {LARGE_MODEL}...")

    session = TuiSession(LARGE_MODEL, ROOT)
    print("Waiting for TUI startup...")
    try:
        session.wait_ready()
        print("TUI ready.")
    except TimeoutError as e:
        print(f"  ✗ TUI never became ready: {e}")
        session.quit()
        return None

    results = {
        "session": session_number,
        "model": LARGE_MODEL,
        "mode": "tui_continuous",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "questions": [],
    }

    try:
        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {q['id']}: {q['question'][:60]}...")
            start = time.time()
            try:
                answer = session.ask(q["question"])
                elapsed = round(time.time() - start, 2)
                verdict = scorer.score(q, answer)
                result = {
                    "id": q["id"], "tier": q["tier"], "question": q["question"],
                    "answer": answer, "score": verdict,
                    "elapsed_seconds": elapsed, "exit_code": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except TimeoutError as e:
                elapsed = round(time.time() - start, 2)
                result = {
                    "id": q["id"], "tier": q["tier"], "question": q["question"],
                    "answer": "", "score": {"verdict": "incorrect", "note": f"timed out: {e}"},
                    "elapsed_seconds": elapsed, "exit_code": -1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            results["questions"].append(result)
            mark = "✓" if result["score"]["verdict"] == "correct" else (
                "~" if result["score"]["verdict"] == "partial" else "✗")
            print(f"  {mark} {result['score']['verdict']} in {result['elapsed_seconds']}s")
    finally:
        session.quit()

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
    args = ap.parse_args()
    run_benchmark(args.session, tier=args.tier, question_id=args.question)
