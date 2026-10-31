#!/bin/bash
# full_run_17b.sh <session> — all 320 questions on lfm3-1.7b in 20-tier blocks;
# each block: RAM clean, fresh model load, run, refresh comparison table.
set -uo pipefail
cd ~/Downloads/aura-50-day-trial
SESSION=$1
LOG="results/run_${SESSION}.log"
TABLE="results/full_${SESSION}_tables.md"

sed -i "s/\"modelName\": \"lfm3[^\"]*\"/\"modelName\": \"lfm3-1.7b\"/" .aura.json
for BLOCK in 1 21 41; do
  echo "[$(date)] tiers ${BLOCK}-$((BLOCK + 19)) start" >> "$LOG"
  lms unload --all >/dev/null 2>&1
  /usr/local/bin/aura-ram-heal >> "$LOG" 2>&1
  lms load lfm3-1.7b --gpu max --context-length 32768 >> "$LOG" 2>&1
  python3 runner/run.py --session "$SESSION" --zero-memory --isolate --keep-going --resume \
    --tier "$(seq -s, "$BLOCK" $((BLOCK + 19)))" >> "$LOG" 2>&1
  python3 scripts/block_table.py "$SESSION" "$TABLE" >> "$LOG" 2>&1
done
lms unload --all >/dev/null 2>&1
echo "[$(date)] full run complete" >> "$LOG"
