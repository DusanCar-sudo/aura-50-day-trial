#!/bin/bash
# publish_run.sh <session> — scrub secrets, rebuild dashboard, commit+push one batch
set -euo pipefail
cd ~/Downloads/aura-50-day-trial
S="$1"
python3 scripts/scrub_secrets.py "answers/session_${S}_"*.md "results/session_${S}.json" \
  "results/archimedes_audit_${S}.md" 2>/dev/null || true
python3 scripts/generate_dashboard.py
git add "results/session_${S}.json" "results/archimedes_audit_${S}.md" results/batches.json \
  "answers/session_${S}_"*.md index.html dashboard.html dashboard/index.html 2>/dev/null || true
git commit -m "feat: lfm3 sample batch ${S} + archimedes audit" || echo "nothing to commit for ${S}"
git push
echo "[$(date)] published ${S}" >> results/relay.log
