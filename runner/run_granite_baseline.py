#!/usr/bin/env python3
"""
Granite 4.1:3b baseline runner — Session 0, zero memory.
Hits Ollama directly (no Aura agent loop involved), scores with scorer.py,
writes results/session_000_granite_baseline.json + updates results/index.json.

Run this ON YOUR MACHINE where Ollama is running:
    python3 runner/run_granite_baseline.py
"""

import json
import time
import urllib.request
import sys
from datetime import datetime
from pathlib import Path

import scorer
import recorder

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "granite4.1:3b"


def load_all_questions():
    questions = []
    for f in sorted(QUESTIONS_DIR.glob("tier*.json")):
        questions.extend(json.loads(f.read_text()))
    return questions


def check_ollama():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as r:
            tags = json.loads(r.read())
        names = [m["name"] for m in tags.get("models", [])]
        if not any(MODEL in n for n in names):
            print(f"✗ {MODEL} not found in Ollama. Available: {names}")
            sys.exit(1)
        print(f"✓ {MODEL} is available.")
    except Exception as e:
        print(f"✗ Can't reach Ollama at localhost:11434 — is it running? ({e})")
        sys.exit(1)


def ask_granite(prompt: str) -> tuple[str, float]:
    start = time.time()
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    elapsed = round(time.time() - start, 2)
    return data.get("response", ""), elapsed


def run():
    check_ollama()
    questions = load_all_questions()
    print(f"Running {len(questions)} questions against {MODEL} (session 0, zero memory)...\n")

    results = {
        "session": 0,
        "label": "granite_baseline_zero_memory",
        "model": MODEL,
        "timestamp": datetime.utcnow().isoformat(),
        "questions": [],
    }

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']} (tier {q['tier']}): {q['question'][:60]}...")
        try:
            answer, elapsed = ask_granite(q["question"])
        except Exception as e:
            answer, elapsed = "", 0
            print(f"  ✗ request failed: {e}")

        verdict = scorer.score(q, answer)
        record = {
            "id": q["id"],
            "tier": q["tier"],
            "question": q["question"],
            "answer": answer,
            "score": verdict,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.utcnow().isoformat(),
        }
        results["questions"].append(record)
        mark = "✓" if verdict["verdict"] == "correct" else ("~" if verdict["verdict"] == "partial" else "✗")
        print(f"  {mark} {verdict['verdict']} in {elapsed}s")

    # write with the fixed session_000 filename recorder.py doesn't know about
    out_file = ROOT / "results" / "session_000_granite_baseline.json"
    out_file.write_text(json.dumps(results, indent=2))
    recorder._update_index(out_file.name, results)

    total = len(results["questions"])
    correct = sum(1 for q in results["questions"] if q["score"]["verdict"] == "correct")
    tier4 = [q for q in results["questions"] if q["tier"] == 4]
    tier4_correct = sum(1 for q in tier4 if q["score"]["verdict"] == "correct")

    print(f"\nSaved to {out_file}")
    print(f"Overall: {correct}/{total} correct")
    print(f"Tier 4 (memory — expected to fail): {tier4_correct}/{len(tier4)} correct")
    if tier4_correct > 0:
        print("⚠ Granite got a Tier 4 question right with zero memory — check for lucky guesses or leaked context.")


if __name__ == "__main__":
    run()
