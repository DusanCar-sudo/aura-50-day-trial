#!/usr/bin/env python3
"""10% stratified sample of the 320-question benchmark, projected back to 100%.

  python3 scripts/sample10.py pick                       # writes sample_10pct.json + prints run command
  python3 scripts/sample10.py project results/session_N.json
  python3 scripts/sample10.py backtest                   # sample vs every past full run

Strata are bands of 5 tiers (1-5, 6-10, ... 56-60). Each band gets ~10% of its
questions, spread across its tiers. Projection = sum(band size x band pass rate).
"""
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = ROOT / "sample_10pct.json"
BAND = 5
FRACTION = 0.10
SEED = 50  # fixed so the same 32 questions are picked every time


def band_of(tier: int) -> str:
    lo = (tier - 1) // BAND * BAND + 1
    return f"{lo}-{lo + BAND - 1}"


def load_all() -> list:
    qs = []
    for f in sorted((ROOT / "questions").glob("tier*.json")):
        qs.extend(json.loads(f.read_text()))
    return qs


def allocate(sizes: dict, total: int) -> dict:
    """Largest-remainder split of `total` across bands, at least 1 each."""
    raw = {b: n * total / sum(sizes.values()) for b, n in sizes.items()}
    alloc = {b: max(1, math.floor(r)) for b, r in raw.items()}
    for b in sorted(raw, key=lambda b: raw[b] - math.floor(raw[b]), reverse=True):
        if sum(alloc.values()) >= total:
            break
        alloc[b] += 1
    return alloc


def pick() -> dict:
    rng = random.Random(SEED)
    bands = {}
    for q in sorted(load_all(), key=lambda q: (q["tier"], q["id"])):
        bands.setdefault(band_of(q["tier"]), []).append(q)
    sizes = {b: len(v) for b, v in bands.items()}
    alloc = allocate(sizes, round(sum(sizes.values()) * FRACTION))
    chosen = []
    for b, qs in bands.items():
        by_tier = {}
        for q in qs:
            by_tier.setdefault(q["tier"], []).append(q)
        tiers = sorted(by_tier)
        rng.shuffle(tiers)
        # one question per tier before any tier gets a second
        for i in range(alloc[b]):
            chosen.append(rng.choice([q for q in by_tier[tiers[i % len(tiers)]] if q not in chosen]))
    chosen.sort(key=lambda q: (q["tier"], q["id"]))
    return {
        "seed": SEED,
        "band_sizes": sizes,
        "band_sample": alloc,
        "ids": [q["id"] for q in chosen],
        "questions": [{"id": q["id"], "tier": q["tier"], "band": band_of(q["tier"]),
                       "question": q["question"]} for q in chosen],
    }


def project(session: dict, sample: dict) -> dict:
    """Stratified estimate of the full-run correct rate from the sampled answers."""
    by_id = {q["id"]: q for q in session["questions"] if q.get("score")}
    sizes, total = sample["band_sizes"], sum(sample["band_sizes"].values())
    est = var = score_est = 0.0
    rows, missing = [], []
    for b, n_band in sizes.items():
        ids = [q["id"] for q in sample["questions"] if q["band"] == b]
        got = [by_id[i] for i in ids if i in by_id]
        missing += [i for i in ids if i not in by_id]
        if not got:
            continue
        n = len(got)
        p = sum(q["score"]["verdict"] == "correct" for q in got) / n
        avg = sum(q["score"].get("score", 0) for q in got) / n
        w = n_band / total
        est += w * p
        score_est += w * avg
        if n > 1:
            var += w * w * p * (1 - p) / (n - 1) * (1 - n / n_band)
        rows.append((b, n, n_band, p))
    margin = 1.96 * math.sqrt(var)
    return {"correct_pct": est * 100, "margin_pct": margin * 100, "avg_score_pct": score_est * 100,
            "projected_correct": round(est * total), "total": total, "rows": rows, "missing": missing}


def actual(session: dict) -> float:
    qs = [q for q in session["questions"] if q.get("score")]
    return 100 * sum(q["score"]["verdict"] == "correct" for q in qs) / len(qs)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pick"
    if cmd == "pick":
        sample = pick()
        SAMPLE_FILE.write_text(json.dumps(sample, indent=2) + "\n")
        print(f"{len(sample['ids'])} questions -> {SAMPLE_FILE.name}")
        print(f"python3 runner/run.py --session <N> --question {','.join(sample['ids'])}")
        return
    sample = json.loads(SAMPLE_FILE.read_text())
    if cmd == "project":
        r = project(json.loads(Path(sys.argv[2]).read_text()), sample)
        for b, n, nb, p in r["rows"]:
            print(f"  tiers {b:>6}: {p * n:.0f}/{n} correct  -> counts for {nb} questions")
        print(f"Projected 100%: {r['correct_pct']:.1f}% correct (+/- {r['margin_pct']:.1f}), "
              f"~{r['projected_correct']}/{r['total']}; avg score {r['avg_score_pct']:.1f}%")
        if r["missing"]:
            print(f"  not answered yet: {', '.join(r['missing'])}")
    elif cmd == "backtest":
        for f in sorted((ROOT / "results").glob("session_*.json")):
            s = json.loads(f.read_text())
            if len([q for q in s.get("questions", []) if q.get("score")]) < 300:
                continue
            r = project(s, sample)
            print(f"{f.stem:>14}: actual {actual(s):5.1f}%  projected {r['correct_pct']:5.1f}% "
                  f"+/- {r['margin_pct']:.1f}")


if __name__ == "__main__":
    main()
