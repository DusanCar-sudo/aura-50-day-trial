#!/bin/bash
# rerun_unreached.sh <from_session> <new_session> <wait_pid> — after the full run exits,
# re-run on lfm3-1.7b every question that never reached the model or lost it mid-answer.
set -uo pipefail
cd ~/Downloads/aura-50-day-trial
FROM=$1
SESSION=$2
WAIT_PID=$3
LOG="results/run_${SESSION}.log"

while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 60; done

IDS=$(python3 scripts/block_table.py "$FROM" --unreached)
if [ -z "$IDS" ]; then
  echo "[$(date)] nothing to re-run" >> "$LOG"
  exit 0
fi
echo "[$(date)] re-running $(echo "$IDS" | tr ',' '\n' | wc -l) questions" >> "$LOG"
lms unload --all >/dev/null 2>&1
/usr/local/bin/aura-ram-heal >> "$LOG" 2>&1
lms load lfm3-1.7b --gpu max --context-length 32768 >> "$LOG" 2>&1
python3 runner/run.py --session "$SESSION" --zero-memory --isolate --keep-going --resume \
  --question "$IDS" >> "$LOG" 2>&1
python3 scripts/block_table.py "$SESSION" "results/full_${SESSION}_tables.md" >> "$LOG" 2>&1
lms unload --all >/dev/null 2>&1
echo "[$(date)] re-run complete" >> "$LOG"
