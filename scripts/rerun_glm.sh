#!/bin/bash
# rerun_glm.sh <session> [--list] — re-run on lfm3-1.7b every question whose rescue failed (402) or
# lost the model, with GLM as the large model; reload each batch because llama-server RSS grows until OOM.
set -uo pipefail
cd ~/Downloads/aura-50-day-trial
SESSION=$1
BATCH_SIZE=30
LOG="results/run_${SESSION}.log"
export AURA_BENCH_MODEL=nvidia/z-ai/glm-5.3-flash

mapfile -t BATCHES < <(python3 - <<'EOF' | xargs -n "$BATCH_SIZE" | tr ' ' ','
import json
import sys
sys.path.insert(0, "scripts")
import block_table as b

latest = {}
for session in (11025, 11026):
    for q in json.load(open(f"results/session_{session}.json"))["questions"]:
        latest[q["id"]] = q
for qid, q in latest.items():
    text = b.transcript(q)
    if b.NO_CREDIT.search(text) or b.MODEL_LOST.search(text):
        print(qid)
EOF
)

if [ "${2:-}" = "--list" ]; then
  printf '%s\n' "${BATCHES[@]}"
  exit 0
fi

echo "[$(date)] ${#BATCHES[@]} batches on $AURA_BENCH_MODEL" >> "$LOG"
for CHUNK in "${BATCHES[@]}"; do
  lms unload --all >/dev/null 2>&1
  /usr/local/bin/aura-ram-heal >> "$LOG" 2>&1
  lms load lfm3-1.7b --gpu max --context-length 32768 >> "$LOG" 2>&1
  python3 runner/run.py --session "$SESSION" --zero-memory --isolate --keep-going --resume \
    --question "$CHUNK" >> "$LOG" 2>&1
  python3 scripts/block_table.py "$SESSION" "results/full_${SESSION}_tables.md" >> "$LOG" 2>&1
done
lms unload --all >/dev/null 2>&1
echo "[$(date)] GLM re-run complete" >> "$LOG"
