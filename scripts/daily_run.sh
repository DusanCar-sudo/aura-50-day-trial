#!/bin/bash
# daily_run.sh — Aura 50-Day Trial automation
# Runs the full Aura_Benchmark suite (real accumulated memory, NOT
# --zero-memory), captures Ruby competence/episode stats, regenerates
# the dashboard, commits everything — good day or bad day, no cherry-picking.

set -euo pipefail

BENCHMARK_DIR="/run/media/dusan/DATA1/Aura_Benchmark"
AURA_CODE_DIR="/mnt/bigdata/aura/aura-code"
TRIAL_REPO="$HOME/aura-50-day-trial"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$TRIAL_REPO/logs/${DATE}.md"

# ── Step 1: run the benchmark ────────────────────────────────────────
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
  echo "[$(date)] ERROR: expected result file $RESULT_FILE not found."
  exit 1
fi
cp "$RESULT_FILE" "$TRIAL_REPO/results/"

PASS_RATE=$(python3 -c "
import json
with open('$RESULT_FILE') as f:
    data = json.load(f)
qs = data.get('questions', [])
total = len(qs)
correct = sum(1 for q in qs if q.get('score', {}).get('verdict') == 'correct')
partial = sum(1 for q in qs if q.get('score', {}).get('verdict') == 'partial')
print(f'{correct}/{total} correct, {partial}/{total} partial')
")

# ── Step 2: capture Ruby competence/episode stats ────────────────────
cd "$AURA_CODE_DIR"
npm run build > /tmp/daily_build_${DATE}.log 2>&1
node scripts/dump-ruby-stats.mjs > "$TRIAL_REPO/results/ruby-stats-${DATE}.json"

# ── Step 3: write the daily log entry ────────────────────────────────
cat > "$LOG_FILE" << LOGEOF
# Day — ${DATE}

**Session:** ${NEXT_SESSION}
**Result:** ${PASS_RATE}

<!-- Add manual notes below this line -->

LOGEOF

# ── Step 4: regenerate the dashboard ─────────────────────────────────
cd "$TRIAL_REPO"
python3 scripts/generate_dashboard.py

# ── Step 5: commit and push everything ───────────────────────────────
git add "results/session_$(printf '%03d' "$NEXT_SESSION").json" \
        "results/ruby-stats-${DATE}.json" \
        "logs/${DATE}.md" \
        "index.html"
git commit -m "Day ${DATE}: session ${NEXT_SESSION} — ${PASS_RATE}"
git push origin master

echo "[$(date)] Done. Committed and pushed session ${NEXT_SESSION} + dashboard."
