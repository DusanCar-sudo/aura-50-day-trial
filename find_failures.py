#!/usr/bin/env python3
"""
Scans results/session_*.json for questions scored 'partial' or 'incorrect'
(including timeouts, which score as 'incorrect' with note 'timed out').
Outputs a deduplicated list (latest result per question id wins) plus a
ready-to-run bash script that reruns each one individually.

Usage:
  python3 find_failures.py --results-dir results --out-script rerun_failures.sh
"""
import argparse
import json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--out-script", default="rerun_failures.sh")
    ap.add_argument("--start-session", type=int, default=900,
                     help="First session number to use for reruns")
    ap.add_argument("--include-verdicts", nargs="+",
                     default=["incorrect", "partial"],
                     help="Which verdicts count as failures to rerun")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    files = sorted(results_dir.glob("session_*.json"), key=lambda f: f.stat().st_mtime)

    # id -> (verdict, note, source_file, tier) — later files overwrite earlier
    # so we always keep the MOST RECENT result for each question id
    latest = {}
    for f in files:
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            print(f"  [skip] couldn't parse {f}")
            continue
        for q in data.get("questions", []):
            qid = q.get("id")
            tier = q.get("tier")
            verdict = q.get("score", {}).get("verdict")
            note = q.get("score", {}).get("note", "")
            if qid and tier is not None:
                latest[qid] = (tier, verdict, note, f.name)

    failures = {
        qid: info for qid, info in latest.items()
        if info[1] in args.include_verdicts
    }

    print(f"Scanned {len(files)} result files, {len(latest)} unique questions total")
    print(f"Found {len(failures)} questions with verdict in {args.include_verdicts}")

    # group by tier for a readable summary
    by_tier = {}
    for qid, (tier, verdict, note, src) in failures.items():
        by_tier.setdefault(tier, []).append((qid, verdict, note, src))

    print("\nBreakdown by tier:")
    for tier in sorted(by_tier):
        items = by_tier[tier]
        print(f"  tier {tier}: {len(items)} failing — {[i[0] for i in items]}")

    # write the rerun script
    lines = ["#!/bin/bash", "set -e", ""]
    session = args.start_session
    for tier in sorted(by_tier):
        for qid, verdict, note, src in by_tier[tier]:
            note_part = f" / {note}" if note else ""
            echo_text = f"--- {qid} (was {verdict}{note_part}, from {src}) ---"
            lines.append(f'echo "{echo_text}"')
            lines.append(f"python3 runner/run.py --session {session} --question {qid}")
            session += 1
            lines.append("")

    Path(args.out_script).write_text("\n".join(lines))
    Path(args.out_script).chmod(0o755)
    print(f"\nWrote rerun script: {args.out_script} ({session - args.start_session} reruns, "
          f"sessions {args.start_session}-{session - 1})")

if __name__ == "__main__":
    main()
