#!/usr/bin/env python3
"""
Aura Benchmark Recorder
Persists a session's results and maintains results/index.json,
which the static dashboard reads (GitHub Pages can't list a directory).
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
INDEX_FILE = RESULTS_DIR / "index.json"


def save_session(results: dict) -> Path:
    session_number = results["session"]
    out_file = RESULTS_DIR / f"session_{session_number:03d}.json"
    out_file.write_text(json.dumps(results, indent=2))
    _update_index(out_file.name, results)
    return out_file


def _update_index(filename: str, results: dict) -> None:
    index = []
    if INDEX_FILE.exists():
        index = json.loads(INDEX_FILE.read_text())
        index = [e for e in index if e["file"] != filename]  # replace if rerun

    questions = results.get("questions", [])
    total = len(questions)
    correct = sum(1 for q in questions if q.get("score", {}).get("verdict") == "correct")
    partial = sum(1 for q in questions if q.get("score", {}).get("verdict") == "partial")
    tier4 = [q for q in questions if q.get("tier") == 4]
    tier4_correct = sum(1 for q in tier4 if q.get("score", {}).get("verdict") == "correct")

    index.append({
        "file": filename,
        "session": results["session"],
        "timestamp": results.get("timestamp", datetime.utcnow().isoformat()),
        "total": total,
        "correct": correct,
        "partial": partial,
        "pass_rate": round(correct / total, 3) if total else 0,
        "tier4_score": f"{tier4_correct}/{len(tier4)}" if tier4 else "0/0",
        "avg_seconds": round(sum(q.get("elapsed_seconds", 0) for q in questions) / total, 2) if total else 0,
    })

    index.sort(key=lambda e: e["session"])
    INDEX_FILE.write_text(json.dumps(index, indent=2))
