#!/bin/bash
# daily_run.sh — Aura 50-Day Trial automation
# Runs the full Aura_Benchmark suite (real accumulated memory, NOT
# --zero-memory — we want to see the effect of accumulated competence
# over time), commits the raw result, no matter good or bad.

set -euo pipefail

BENCHMARK_DIR="/run/media/dusan/DATA1/Aura_Benchmark"
TRIAL_REPO="$HOME/aura-50-day-trial"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$TRIAL_REPO/logs/${DATE}.md"

cd "$BENCHMARK_DIR"

LAST_SESSION=$(ls results/session_*.json 2>/dev/null | sed -E 's/.*session_([0-9]+)\.json/\1/' | sort -n | tail -1)
if [ -z "$LAST_SESSION" ]; then
  NEXT_SESSION=1
else
  NEXT_SESSION=$((10#$LAST_SESSION + 1))
fi

echo "[$(date)] Running session $NEXT_SESSION (accumulated memory, all tiers)"

python3 runner/run.py --session "$NEXT_SESSION" 2>&1 | tee "/tmp/daily_run_${DATE}.log"

RESULT_FILE="results/session_$(printf '%03d' "$NEXT_SESSION").json"

if [ ! -f "$RESULT_FILE" ]; then
  echo "[$(date)] ERROR: expected result file $RESULT_FILE not found — benchmark run may have failed."
  exit 1
fi

cp "$RESULT_FILE" "$TRIAL_REPO/results/"

PASS_RATE=$(python3 -c "
import json
try:
    with open('$RESULT_FILE') as f:
        data = json.load(f)
    qs = data.get('questions', [])
    total = len(qs)
    correct = sum(1 for q in qs if q.get('score', {}).get('verdict') == 'correct')
    partial = sum(1 for q in qs if q.get('score', {}).get('verdict') == 'partial')
    print(f'{correct}/{total} correct, {partial}/{total} partial')
except Exception as e:
    print(f'(could not parse: {e})')
")

cat > "$LOG_FILE" << LOGEOF
# Day — ${DATE}

**Session:** ${NEXT_SESSION}
**Result:** ${PASS_RATE}

<!-- Add manual notes below this line -->

LOGEOF

cd "$TRIAL_REPO"
git add "results/session_$(printf '%03d' "$NEXT_SESSION").json" "logs/${DATE}.md"
git commit -m "Day ${DATE}: session ${NEXT_SESSION} — ${PASS_RATE}"
git push origin master

echo "[$(date)] Done. Committed and pushed session ${NEXT_SESSION}."
