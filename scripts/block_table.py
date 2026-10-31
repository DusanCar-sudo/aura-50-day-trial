#!/usr/bin/env python3
"""block_table.py <session> [out.md] — success per 20-tier block, each compared to the previous block."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK_SIZE = 20
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
TRIED = re.compile(r"^\W*Trying Archimedes", re.M)
ALONE = re.compile(r"^\W*Archimedes handled the task without escalation", re.M)
NO_CREDIT = re.compile(r"^\W*Provider error[^\n]*Insufficient Balance", re.M)
MODEL_LOST = re.compile(r"^\W*Provider error: (Type)?Error: terminated", re.M)


def block_label(index: int) -> str:
    return f"{index * BLOCK_SIZE + 1}-{(index + 1) * BLOCK_SIZE}"


def transcript(q: dict) -> str:
    return ANSI.sub("", f"{q.get('stderr') or ''}\n{q.get('answer') or ''}")


def unreached_ids(questions: list) -> list:
    """Questions the model never saw, or lost mid-answer: their scores say nothing about it."""
    return [q["id"] for q in questions
            if not TRIED.search(transcript(q)) or MODEL_LOST.search(transcript(q))]


def build_table(questions: list) -> str:
    blocks: dict = {}
    for q in questions:
        blocks.setdefault((int(q["tier"]) - 1) // BLOCK_SIZE, []).append(q)

    rows = ["| Tiers | Done | Correct | Partial | Incorrect | Correct % | vs previous "
            "| Reached 1.7B | 1.7B alone (correct) | Rescue failed (402) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    previous_pct = None
    for index in sorted(blocks):
        block = blocks[index]
        verdicts = [q["score"]["verdict"] for q in block]
        texts = [transcript(q) for q in block]
        alone = [q for q, text in zip(block, texts) if ALONE.search(text)]
        alone_correct = sum(q["score"]["verdict"] == "correct" for q in alone)
        correct = verdicts.count("correct")
        pct = 100 * correct / len(verdicts)
        delta = "—" if previous_pct is None else f"{pct - previous_pct:+.1f} pts"
        rows.append(f"| {block_label(index)} | {len(verdicts)} | {correct} | {verdicts.count('partial')} "
                    f"| {verdicts.count('incorrect')} | {pct:.1f}% | {delta} "
                    f"| {sum(bool(TRIED.search(t)) for t in texts)} | {len(alone)} ({alone_correct}) "
                    f"| {sum(bool(NO_CREDIT.search(t)) for t in texts)} |")
        previous_pct = pct
    return "\n".join(rows)


def main() -> None:
    session = int(sys.argv[1])
    data = json.loads((ROOT / "results" / f"session_{session:03d}.json").read_text())
    if sys.argv[2:] == ["--unreached"]:
        print(",".join(unreached_ids(data["questions"])))
        return
    text = f"# Session {session}: {data.get('archimedes') or data.get('model')}\n\n{build_table(data['questions'])}\n"
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
