#!/usr/bin/env python3
"""
Aura 50-Day Trial — dashboard generator.
Injects real session data into trial_dashboard.html template.
Run from the aura-50-day-trial repo root.
"""
import json
import glob
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
TEMPLATE_FILE = ROOT / "scripts" / "trial_dashboard.html"
OUTPUT_FILE = ROOT / "dashboard.html"

def load_sessions():
    sessions = []
    for f in sorted(RESULTS_DIR.glob("session_[0-9]*.json")):
        try:
            data = json.loads(f.read_text())
            questions = data.get("questions", [])
            total = len(questions)
            if total == 0:
                continue
            correct = sum(1 for q in questions if q.get("verdict") == "correct" or q.get("score", {}).get("verdict") == "correct")
            partial = sum(1 for q in questions if q.get("verdict") == "partial" or q.get("score", {}).get("verdict") == "partial")
            incorrect = total - correct - partial
            score = round(100 * (correct + partial * 0.5) / total, 1)
            tiers = {}
            for q in questions:
                t = q.get("tier", 0)
                v = q.get("verdict") or q.get("score", {}).get("verdict", "incorrect")
                if t not in tiers:
                    tiers[t] = {"correct": 0, "partial": 0, "total": 0}
                tiers[t]["total"] += 1
                if v == "correct": tiers[t]["correct"] += 1
                elif v == "partial": tiers[t]["partial"] += 1
            sessions.append({
                "session": data.get("session"),
                "model": data.get("model", "unknown"),
                "timestamp": data.get("timestamp", ""),
                "total": total, "correct": correct, "partial": partial,
                "incorrect": incorrect, "score": score,
                "tiers": tiers, "mode": data.get("mode", "headless"),
            })
        except Exception as e:
            print(f"Warning: {f}: {e}")
    return sessions

def load_ruby_stats():
    snapshots = []
    for f in sorted(RESULTS_DIR.glob("ruby-stats-*.json")):
        try:
            data = json.loads(f.read_text())
            date = f.name.replace("ruby-stats-", "").replace(".json", "")
            snapshots.append({
                "date": date,
                "catchRate": data.get("verificationCatchRate"),
                "episodeStats": data.get("episodeStats", {}),
                "competence": data.get("competence", []),
            })
        except Exception as e:
            print(f"Warning: {f}: {e}")
    return snapshots

def main():
    sessions = load_sessions()
    ruby_snapshots = load_ruby_stats()
    template = TEMPLATE_FILE.read_text()
    html = template.replace(
        "const SESSIONS = __SESSIONS_JSON__;",
        f"const SESSIONS = {json.dumps(sessions)};"
    ).replace(
        "const RUBY_SNAPSHOTS = __RUBY_SNAPSHOTS_JSON__;",
        f"const RUBY_SNAPSHOTS = {json.dumps(ruby_snapshots)};"
    )
    OUTPUT_FILE.write_text(html)
    print(f"Dashboard written: {OUTPUT_FILE} ({len(sessions)} sessions, {len(ruby_snapshots)} ruby-stats)")

if __name__ == "__main__":
    main()
