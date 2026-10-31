#!/bin/bash
# chain_batches.sh — runs remaining batches 6-10 sequentially after the current
# session 11019 finishes; each batch: fresh model load, run, audit, publish.
set -uo pipefail
cd ~/Downloads/aura-50-day-trial
LOG=results/chain.log
echo "[$(date)] chain start, waiting for 11019" >> $LOG

# wait for batch 5 (11019) to complete its 32 questions
while true; do
  N=$(python3 -c "
import json
try: print(len(json.load(open('results/session_11019.json')).get('questions',[])))
except Exception: print(0)" 2>/dev/null)
  [ "${N:-0}" -ge 32 ] && break
  sleep 60
done
python3 scripts/archimedes_audit.py 11019 >> $LOG 2>&1
scripts/publish_run.sh 11019 >> $LOG 2>&1

for PAIR in 11020:6 11021:7 11022:8 11023:9 11024:10; do
  SESSION=${PAIR%%:*}; BATCH=${PAIR##*:}
  # build the next 32 unseen ids
  Q=$(python3 - <<EOF
import json, glob
b = json.load(open('results/batches.json'))
done = set()
for v in list(b.get('done', {}).values()):
    done |= set(v)
for k in b:
    if k.startswith('batch'):
        done |= set(b[k])
ids = []
for f in sorted(glob.glob('questions/tier*.json')):
    for q in json.load(open(f)):
        ids.append(q if isinstance(q, str) else q.get('id'))
batch = [i for i in dict.fromkeys(ids) if i not in done][:32]
b['batch${BATCH}_${SESSION}'] = batch
json.dump(b, open('results/batches.json','w'), indent=2)
print(','.join(batch))
EOF
)
  echo "[$(date)] batch ${BATCH} -> session ${SESSION}" >> $LOG
  # fresh model each batch to dodge the Vulkan degradation
  lms unload --all >/dev/null 2>&1
  lms load lfm3-1.7b --gpu max --context-length 32768 >/dev/null 2>&1
  python3 runner/run.py --session "$SESSION" --zero-memory --isolate --keep-going \
    --question "$Q" >> "results/run_${SESSION}.log" 2>&1
  python3 scripts/archimedes_audit.py "$SESSION" >> $LOG 2>&1
  scripts/publish_run.sh "$SESSION" >> $LOG 2>&1
done
echo "[$(date)] chain complete — 10 batches done, run full-run rollup" >> $LOG
