#!/usr/bin/env python3
"""Live view of a running trial: verdict, which layer answered, and Aura's own speed line.

  watch -n 5 -t python3 scripts/live.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = {"correct": "✓", "partial": "~", "incorrect": "✗"}
# Aura prints this per model call, e.g. "prompt=6334tok ttft=28.8s ... out=368tok 26.3 tok/s"
SPEED = re.compile(r"prompt=(\d+)tok ttft=([\d.]+)s.*?out=(\d+)tok ([\d.]+) tok/s")


def layer(text: str) -> str:
    if "without escalation" in text:
        return "LOCAL answered"
    if "exceeded its" in text:  # Aura's "Archimedes exceeded its 180s deadline"
        return "BIG (local timed out)"
    if "escalating" in text:
        return "BIG (local crashed)" if "Provider error" in text else "BIG (local rejected)"
    return "?"


def speed(text: str) -> str:
    m = SPEED.search(text)
    return f"{m[4]:>5} tok/s, read {m[1]} tok, wrote {m[3]} tok" if m else "no local speed line"


def main() -> None:
    live = json.loads((ROOT / "results" / "live.json").read_text())
    path = ROOT / "results" / f"session_{live['session']}.json"
    qs = json.loads(path.read_text())["questions"] if path.exists() else []
    print(f"Session {live['session']}  {live['status'].upper()}  {live['done']}/{live['total']}   "
          f"✓ {live['correct']}  ~ {live['partial']}  ✗ {live['incorrect']}\n")
    for q in sorted(qs, key=lambda q: (q["tier"], q["id"])):
        text = q.get("answer", "") + q.get("stderr", "")
        v = q["score"]["verdict"]
        print(f" {MARK.get(v, '?')} {q['id']:7} {v:9} {q['elapsed_seconds']:>6.0f}s  "
              f"{layer(text):23} {speed(text)}")
    cur = live.get("current")
    if cur and live["status"] == "running":
        print(f"\n … now: {cur['id']}  {cur['question'][:80]}")


if __name__ == "__main__":
    main()
