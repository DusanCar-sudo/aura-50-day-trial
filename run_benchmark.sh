#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

SESSION="${1:-}"
if [ -z "$SESSION" ]; then
  LAST=$(python3 -c "
import json, pathlib
idx = pathlib.Path('results/index.json')
print(max((e['session'] for e in json.loads(idx.read_text())), default=0) if idx.exists() else 0)
")
  SESSION=$((LAST + 1))
  echo "No session number given — auto-assigning session ${SESSION}."
fi

python3 runner/run.py --session "$SESSION"
