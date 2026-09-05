#!/bin/bash
# daily_run.sh — Aura 50-Day Trial automation (charter: CHARTER.md §Automation)
# Runs the full Aura_Benchmark suite (real accumulated memory, NOT
# --zero-memory) — good day or bad day, no cherry-picking.
#
# Since 2026-09-05 this is a thin wrapper over ~/.local/bin/aura-trial-run.sh,
# so the scheduled daily run and the manual/split runs share one code path.
# aura-trial-run.sh adds the steps the old inline version lacked, each of
# which caused a real outage:
#   - memory preflight  (session 10003 was OOM-killed 34 min in, losing the run)
#   - LM Studio startup + model warm-load (server was down when needed)
#   - secret scrubbing before commit (session 10002 leaked a live API key into
#     a recorded transcript and GitHub blocked the push for 9 days)

set -euo pipefail

BENCHMARK_DIR="/run/media/dusan/DATA1/Aura_Benchmark"
TRIAL_REPO="$HOME/aura-50-day-trial"
RUNNER="$HOME/.local/bin/aura-trial-run.sh"

# Auto-assign the next session number from the benchmark project's raw store.
LAST_SESSION=$(ls "$BENCHMARK_DIR"/results/session_*.json 2>/dev/null \
  | sed -E 's/.*session_([0-9]+)\.json/\1/' | sort -n | tail -1)
NEXT_SESSION=$((10#${LAST_SESSION:-0} + 1))

echo "[$(date)] daily_run: delegating to aura-trial-run.sh — session ${NEXT_SESSION}, full suite"
exec "$RUNNER" "$NEXT_SESSION" "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60" "daily full suite"
