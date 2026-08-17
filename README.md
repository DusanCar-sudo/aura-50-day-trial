# Aura 50-Day Trial

> ## 🟢 Benchmark testing restarted — 2026-08-01
>
> **Status: restarted.** Session 8004 completed the full 320-question benchmark
> with **180/320 correct (56.2%)**, the best full-run result so far.
>
> Session 8005 then re-ran the healthy tier 3+4 slice after scorer fixes and
> scored **8/10 correct (80%)**. Previous full-run comparison:
> S223 31.9% → S9999 11.9% → S10000 11.9% → S10001 38.1% → **S8004 56.2%**.
>
> The earlier pause notice has been retired. The dashboard now includes the
> restarted runs so the comparison is visible from the live charts.

Daily, automated, unedited proof: does Aura's Archimedes Alternator get
measurably better over 50 days of real use?

## 📊 Live Dashboard
**[View live charts →](https://dusancar-sudo.github.io/aura-50-day-trial/)**

Pass rate trend, verification catch rate, and Archimedes competence by category —
updated automatically every day. No download needed.

## Setup
- **Large model (cloud):** DeepSeek Chat (`deepseek/deepseek-chat`) — the escalation target the benchmark runs against (`runner/run.py`)
- **Local model (Archimedes Alternator):** `gemma-archimedes-gen2` — a local fine-tune of Gemma-4-E2B, 4.6B parameters, Q4_K_M, served by Ollama on an AMD Radeon 680M iGPU (`.aura.json`)
- **Archimedes Alternator:** local model attempts every task first, gets verified by the large model, escalates on failure or low competence

> **Note:** earlier revisions of this README described the setup as GLM-5.2 plus
> Granite 4.1 3B on CPU. Both changed during the trial — the local model moved to
> the `gemma-archimedes-gen2` fine-tune and the escalation target to DeepSeek Chat —
> and the README wasn't updated at the time. Corrected 2026-07-26 to match what the
> code actually runs. Published results were produced by the configuration described
> above, not the one previously documented here.

## What is this?
Every day a systemd timer runs the full Aura benchmark suite (115 questions,
tiers 1-19) against the current state of Archimedes Alternator's accumulated
episode/competence history, and commits the raw result here — good day or
bad day, nothing is cherry-picked.

See [CHARTER.md](CHARTER.md) for the full architecture and success metrics.

## Case Studies
Real incidents — infrastructure failures, bugs found, fixes applied:
- [2026-07-17 — Ollama port collision: why sessions 002 and 008 scored near zero](case-studies/2026-07-17-ollama-port-collision.md)
- [2026-07-17 — Catching Archimedes fabricating a function that doesn't exist](case-studies/2026-07-17-fabrication-catch.md)

## Structure
- `logs/` — one dated entry per day
- `results/` — raw benchmark JSON + session notes per day
- `case-studies/` — real incidents: what broke, why, how it was fixed
- `scripts/daily_run.sh` — the automation itself
- `index.html` — the live dashboard (auto-regenerated daily)
