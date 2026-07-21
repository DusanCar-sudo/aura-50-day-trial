# Session 10 — 2026-07-18

**Model:** GLM-5.2 (zhipu-coding/glm-5.2) + Ruby Alternator (granite4.1:3b local)
**Mode:** TUI real session, one continuous run
**Questions:** All 60 (tiers 1-8 — first run with new tiers 5-8)
**Result:** 49/60 correct, 10/60 partial, 1/60 incorrect
**Score:** 54.0/60 (90.0%)
**Session stats:** 8 turns, 15 tool calls, 223,997 tokens, $0.26

## Notes
- First session using GLM-5.2 as the large model
- First session to include new tiers 5-8 (Ruby Alternator architecture, source code reasoning, safety judgment, synthesis)
- Tier 5 (Ruby Alternator): 10/10 perfect
- Tier 6 (source code deep dive): 9/10
- Tier 7 (safety/judgment): 8/10
- Tier 8 (synthesis/analysis): 0 wrong, 6 partial, 4 correct
- t3-01 scored incorrect by keyword matcher despite correct TypeScript code produced
- Ruby Alternator active throughout — Granite 4.1 3B handling what it could, GLM-5.2 escalation target
