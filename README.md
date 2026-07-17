# Aura 50-Day Trial

Daily, automated, unedited proof: does Aura's Ruby Alternator get
measurably better over 50 days of real use?

Every day a systemd timer runs the full Aura_Benchmark suite against
the current state of Ruby Alternator's accumulated episode/competence
history, and commits the raw result here — good day or bad day, nothing
is cherry-picked.

See CHARTER.md for the full architecture and success metrics.

## Case Studies

Real bugs, found and fixed, documented in full — not just pass-rate
numbers. Start here if you want to see how the system actually behaves,
not just whether it "passed":

- [2026-07-17 — Catching Ruby fabricating a function that doesn't exist](case-studies/2026-07-17-fabrication-catch.md)

## Structure
- `logs/` — one dated markdown entry per day (auto-generated numbers + manual notes)
- `results/` — raw benchmark JSON output per day
- `case-studies/` — real incidents: what broke, why, and how it was fixed
- `scripts/daily_run.sh` — the automation itself
