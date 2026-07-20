# Aura Benchmark

Live benchmark tracking whether Aura improves over sessions.

**The claim:** Engineering experience should accumulate instead of disappearing.
**The proof:** Run the same 20 questions every N sessions. Watch the numbers move.

## Questions
- **Tier 1** (5): Factual — should answer instantly, 1 turn, no tools
- **Tier 2** (5): Reasoning — diagnosis, 1-2 turns
- **Tier 3** (5): Code generation — must produce working code, actually compiled/run/syntax-checked by scorer.py
- **Tier 4** (5): Memory — only Aura with accumulated sessions can answer these

## Setup
```bash
mkdir -p /mnt/bigdata/aura/projects/aura-benchmark
cd /mnt/bigdata/aura/projects/aura-benchmark
# copy this folder's contents in
git init
git add .
git commit -m "Initial benchmark project structure"
git remote add origin https://github.com/DusanCar-sudo/aura-benchmark.git
git push -u origin master
```
Enable GitHub Pages: Settings → Pages → Source: master branch → /dashboard folder.

## Run
```bash
./run_benchmark.sh          # auto-assigns next session number
./run_benchmark.sh 3        # explicit session number
python3 runner/run.py --session 2 --tier 4   # single tier
python3 runner/run.py --session 2 --question t4-01   # single question
```

## Baseline (session 0 — no memory)
```bash
mv ~/.aura/memory ~/.aura/memory.bak
python3 runner/run.py --session 0
mv ~/.aura/memory.bak ~/.aura/memory
```
The gap between session 0 and session 1+ is the proof.

## Verify before first real run
`runner/run.py` calls `aura --auto "<question>"` and reads stdout. Confirm that flag
actually exists on your current Aura CLI — it was assumed, not verified against the
real interface.

## Results
All results are public and unedited — `results/session_NNN.json` + `results/index.json`
(read by the dashboard). Wins and failures both posted. No cherry-picking, no skipped
questions, no mid-run question edits.
