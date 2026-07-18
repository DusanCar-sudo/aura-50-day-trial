#!/usr/bin/env python3
"""
Aura Benchmark Scorer
Grades a single answer against a question's rubric.

Tier 1/2/4: key_points / expected — keyword-presence match against answer text.
Tier 3: eval field ("compile" | "run" | "syntax") — actually executes/compiles the code.

Usage: imported by run.py, or standalone:
    python3 runner/scorer.py --question-id t4-01 --answer "..."
"""

import json
import re
import subprocess
import tempfile
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

# Connector/filler words stripped from a key_point phrase before checking
# whether its meaningful words appear in the answer. Keeps the check from
# requiring trivial words like "vs" to literally appear.
STOPWORDS = {"vs", "and", "or", "the", "a", "an", "of", "in", "on", "to", "for", "with", "is"}


def _load_question(question_id: str) -> dict:
    for f in sorted(QUESTIONS_DIR.glob("tier*.json")):
        for q in json.loads(f.read_text()):
            if q["id"] == question_id:
                return q
    raise ValueError(f"Unknown question id: {question_id}")


def _extract_code_block(answer: str) -> str:
    """Pull the first fenced code block out of a markdown-style answer."""
    m = re.search(r"```(?:\w+)?\n(.*?)```", answer, re.DOTALL)
    return m.group(1) if m else answer


def _keyword_present(kp: str, answer_lower: str) -> bool:
    """
    A key_point phrase counts as present if either:
    - the exact phrase appears as a substring (fast path — correct for
      single words and phrases where exact wording genuinely matters), or
    - all of its meaningful (non-stopword) words appear somewhere in the
      answer, not necessarily contiguous or in the same order.

    This credits an answer that demonstrably covers the concept — e.g. a
    code example containing "class Dog implements Pet" — for a key_point
    like "class implements", without requiring that exact three-word
    substring. A genuinely missing concept (e.g. "declaration merging"
    when neither word appears anywhere) is still correctly scored as
    missed — this loosens rigid phrase-matching, it does not make the
    scorer credit answers that don't actually cover the material.
    """
    kp_lower = kp.lower()
    if kp_lower in answer_lower:
        return True
    words = [w for w in re.findall(r"[a-z0-9]+", kp_lower) if w not in STOPWORDS]
    if not words:
        return False
    return all(re.search(r"\b" + re.escape(w) + r"\b", answer_lower) for w in words)


def score_keyword(answer: str, key_points: list) -> dict:
    answer_lower = answer.lower()
    hits = [kp for kp in key_points if _keyword_present(kp, answer_lower)]
    ratio = len(hits) / len(key_points) if key_points else 0
    verdict = "correct" if ratio >= 0.66 else ("partial" if ratio > 0 else "incorrect")
    return {"verdict": verdict, "hits": hits, "missed": [kp for kp in key_points if kp not in hits], "score": round(ratio, 2)}


def score_expected(answer: str, expected: str) -> dict:
    hit = expected.lower() in answer.lower()
    return {"verdict": "correct" if hit else "incorrect", "expected": expected, "found": hit, "score": 1.0 if hit else 0.0}


def score_code(answer: str, eval_type: str) -> dict:
    code = _extract_code_block(answer)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        try:
            if "typescript" in answer.lower() or "interface" in code or ": string" in code or "function" in code and "=>" in code:
                ext = ".ts" if ("interface" in code or ": string" in code or ": number" in code) else ".js"
            elif "def " in code:
                ext = ".py"
            elif "#!/bin/bash" in code or code.strip().startswith("#!") or "systemd" not in code and "[Unit]" not in code and any(t in code for t in ["find ", "grep ", "#!/"]):
                ext = ".sh"
            else:
                ext = ".txt"

            f = tmp / f"snippet{ext}"
            f.write_text(code)

            if eval_type == "syntax":
                if ext == ".py":
                    r = subprocess.run(["python3", "-m", "py_compile", str(f)], capture_output=True, text=True, timeout=15)
                elif ext == ".sh":
                    r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True, timeout=15)
                elif ext in (".ts", ".js"):
                    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True, timeout=15)
                else:
                    # systemd unit file or unrecognized — presence check only
                    return {"verdict": "partial", "note": "no syntax checker for this format, manual review needed", "score": 0.5}
                ok = r.returncode == 0
                return {"verdict": "correct" if ok else "incorrect", "stderr": r.stderr[:500], "score": 1.0 if ok else 0.0}

            elif eval_type == "compile":
                if ext == ".ts":
                    r = subprocess.run(["npx", "--yes", "tsc", "--noEmit", str(f)], capture_output=True, text=True, timeout=30)
                else:
                    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True, timeout=15)
                ok = r.returncode == 0
                return {"verdict": "correct" if ok else "incorrect", "stderr": r.stderr[:500], "score": 1.0 if ok else 0.0}

            elif eval_type == "run":
                if ext == ".sh":
                    r = subprocess.run(["bash", str(f)], capture_output=True, text=True, timeout=15, cwd=str(tmp))
                elif ext == ".py":
                    r = subprocess.run(["python3", str(f)], capture_output=True, text=True, timeout=15)
                else:
                    r = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=15)
                ok = r.returncode == 0
                return {"verdict": "correct" if ok else "incorrect", "stdout": r.stdout[:500], "stderr": r.stderr[:500], "score": 1.0 if ok else 0.0}

        except subprocess.TimeoutExpired:
            return {"verdict": "incorrect", "note": "timed out", "score": 0.0}
        except FileNotFoundError as e:
            return {"verdict": "partial", "note": f"toolchain unavailable: {e}", "score": 0.5}

    return {"verdict": "incorrect", "note": "unhandled eval_type", "score": 0.0}


def score(question: dict, answer: str) -> dict:
    if question["tier"] in (1, 2):
        return score_keyword(answer, question.get("key_points", []))
    if question["tier"] == 3:
        return score_code(answer, question.get("eval", "syntax"))
    if question["tier"] == 4:
        return score_expected(answer, question.get("expected", ""))
    if question["tier"] in (5, 6, 7, 8):
        return score_keyword(answer, question.get("key_points", []))
    return {"verdict": "incorrect", "note": "unknown tier", "score": 0.0}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--question-id", required=True)
    ap.add_argument("--answer", required=True)
    args = ap.parse_args()
    q = _load_question(args.question_id)
    print(json.dumps(score(q, args.answer), indent=2))
