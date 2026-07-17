# Ruby Diamond Client — Standalone Rebuild & 50-Day Experiment Charter

## The actual research question
Does Aura — specifically the Ruby Alternator — get measurably better over
~50 days of real use? And separately: is the episode data it's already
capturing good enough to actually fine-tune the small model on, or is it
noise?

## Success metrics — defined before data collection starts
1. Benchmark trend — Tier 1-4 pass rate over repeated Aura_Benchmark runs
   across the 50 days. This is the primary objective line.
2. Ruby competence-by-category trend — is the success rate for
   implementation/research/review/refactor patterns moving up, flat, or
   down over time.
3. Verification-gate catch rate — how often the verification gate
   actually catches and escalates a bad Ruby answer, as a fraction of
   total Ruby attempts. A dropping catch rate over time is itself
   evidence Ruby is improving.
4. Fine-tune data adequacy bar — a concrete threshold decided in advance:
   enough labeled, verification-confirmed episodes per task category
   before a fine-tune attempt is considered justified rather than
   premature.

## Automation
`scripts/daily_run.sh`, triggered by a systemd timer at 06:00 daily,
runs the real (non-zero-memory) benchmark, commits the raw JSON result
and a short log entry, and pushes — automatically, no manual step,
no cherry-picking.

## Phased timeline
- Phase 0: charter + metrics locked (this document)
- Phase 1 (week 1-2): Ruby Diamond Client rebuilt as standalone MCP
  server + Honcho-style memory layer + task-prompt compression
- Phase 2 (week 2-3): kanban wired as a memory-layer view, council
  feature reconnected
- Phase 3 (ongoing): daily automated benchmark runs, real work flowing
  through the rebuilt client
- Phase 4 (~day 25): checkpoint — review trend, assess whether the
  fine-tune data bar is realistically reachable by day 50
- Phase 5 (~day 40-45): first real fine-tune attempt, if data bar met
- Phase 6 (~day 50): final writeup — trend graphs, honest results
