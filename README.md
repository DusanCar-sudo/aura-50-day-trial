# Aura 50-Day Trial

Daily, automated, unedited proof: does Aura's Ruby Alternator get
measurably better over 50 days of real use?

## 📊 Live Dashboard
**[View live charts →](https://dusancar-sudo.github.io/aura-50-day-trial/)**

Pass rate trend, verification catch rate, and Ruby competence by category —
updated automatically every day. No download needed.

## What is this?
Every day a systemd timer runs the full Aura benchmark suite (60 questions,
tiers 1-8) against the current state of Ruby Alternator's accumulated
episode/competence history, and commits the raw result here — good day or
bad day, nothing is cherry-picked.

See [CHARTER.md](CHARTER.md) for the full architecture and success metrics.

## Case Studies
Real bugs, found and fixed, documented in full:
- [2026-07-17 — Catching Ruby fabricating a function that doesn't exist](case-studies/2026-07-17-fabrication-catch.md)

## Structure
- `logs/` — one dated entry per day
- `results/` — raw benchmark JSON + session notes per day
- `case-studies/` — real incidents: what broke, why, how it was fixed
- `scripts/daily_run.sh` — the automation itself
- `dashboard.html` — the live dashboard source (auto-regenerated daily)
