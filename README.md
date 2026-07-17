# Aura 50-Day Trial

Daily, automated, unedited proof: does Aura's Ruby Alternator get
measurably better over 50 days of real use?

Every day a systemd timer runs the full Aura_Benchmark suite against
the current state of Ruby Alternator's accumulated episode/competence
history, and commits the raw result here — good day or bad day, nothing
is cherry-picked.

See CHARTER.md for the full architecture and success metrics.

## Structure
- `logs/` — one dated markdown entry per day (auto-generated numbers + manual notes)
- `results/` — raw benchmark JSON output per day
- `scripts/daily_run.sh` — the automation itself
