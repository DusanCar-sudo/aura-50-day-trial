#!/usr/bin/env python3
"""
Archimedes verification audit — pairs what the model claimed/verified per
question against the scorer's ground truth, for tuning Archimedes.

Usage: python3 scripts/archimedes_audit.py <session>   e.g. 11015
Reads: answers/session_<N>_<date>.md + results/session_<N>.json
Writes: results/archimedes_audit_<N>.md
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Lines in an answer that look like a verification act or a truth/possibility claim.
VERIFY_RE = re.compile(
    r"verif|confirm|checked|validated|✓|✗|❌|✅|"
    r"is (?:indeed )?(?:true|false|correct|incorrect|valid|invalid|possible|impossible)|"
    r"cannot (?:verify|confirm)|unable to (?:verify|confirm)|plausible|not possible",
    re.I,
)


def parse_answers(answers_file: Path) -> dict:
    """Split answers markdown into {qid: answer_body}."""
    sections = {}
    current = None
    body = []
    for line in answers_file.read_text(errors="replace").splitlines():
        m = re.match(r"^## (t\d+-\d+)\s*$", line)
        if m:
            if current:
                sections[current] = "\n".join(body)
            current = m.group(1)
            body = []
        elif current:
            body.append(line)
    if current:
        sections[current] = "\n".join(body)
    return sections


def extract_verifications(answer: str) -> list:
    """Pull the lines that look like Archimedes verification acts/claims."""
    seen = []
    for line in answer.splitlines():
        s = line.strip()
        if s and VERIFY_RE.search(s) and len(s) < 400:
            if s not in seen:
                seen.append(s)
    return seen[:8]  # cap noise per question


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: archimedes_audit.py <session>")
    session = sys.argv[1]
    results_file = ROOT / "results" / f"session_{session}.json"
    if not results_file.exists():
        sys.exit(f"missing {results_file}")
    results = json.loads(results_file.read_text())

    answers = {}
    for f in sorted((ROOT / "answers").glob(f"session_{session}_*.md")):
        answers.update(parse_answers(f))

    def confidence(verifs):
        text = " ".join(verifs).lower()
        if any(k in text for k in ("verified", "confirm", "✅", "✓", "is true", "is correct")):
            return "claims-true"
        if any(k in text for k in ("cannot verify", "unable", "✗", "❌", "is false", "incorrect")):
            return "claims-false/unverified"
        if "possible" in text:
            return "claims-possible"
        return "no-explicit-verification"

    rows = []
    for q in results.get("questions", []):
        qid = q["id"]
        verdict = q.get("score", {}).get("verdict", "?")
        verifs = extract_verifications(answers.get(qid, ""))
        rows.append({"id": qid, "tier": q.get("tier"), "verdict": verdict,
                     "verifs": verifs, "conf": confidence(verifs)})

    out = [f"# Archimedes verification audit — session {session}", ""]
    tally = {}
    for r in rows:
        key = r["verdict"] if r["verdict"] in ("correct", "partial") else "wrong"
        tally.setdefault(r["conf"], {"correct": 0, "partial": 0, "wrong": 0})
        tally[r["conf"]][key] += 1
        match = ""
        if r["conf"] == "claims-true":
            match = " — **TRUE-CLAIM HELD**" if r["verdict"] == "correct" else " — **FALSE TRUE-CLAIM**"
        out.append(f"## {r['id']} (tier {r['tier']}) — scorer: {r['verdict']} — {r['conf']}{match}")
        if r["verifs"]:
            out.append("```")
            out.extend(r["verifs"])
            out.append("```")
        else:
            out.append("_(no explicit verification language)_")
        out.append("")

    out.append("## Confidence vs truth matrix")
    out.append("| claim | correct | partial | wrong |")
    out.append("|---|---|---|---|")
    for c in sorted(tally):
        t = tally[c]
        out.append(f"| {c} | {t['correct']} | {t['partial']} | {t['wrong']} |")
    out.append("")

    dest = ROOT / "results" / f"archimedes_audit_{session}.md"
    dest.write_text("\n".join(out))
    print(f"wrote {dest} ({len(rows)} questions)")


if __name__ == "__main__":
    main()
