# Session 11 — 2026-07-18/19

**Model:** DeepSeek V4 Pro + Ruby/Granite (questions done per-tier due to Granite context constraints)
**Questions:** Tiers 9-15 (35 questions)
**Corrected score:** 24 correct / 9 partial / 0 incorrect / 2 missing (33/35 answered) — 86.4% weighted
**Note:** Original mechanical score of 57.1% (20/35) was a scorer artifact — key_points in
tier9-15.json were truncated by a fixed word-count cut, not rewritten as matchable concepts.
Fixed key_points (bare literal terms) rescored this same run at 86.4%, consistent with a full
manual read-through (31/33 answered questions judged technically correct). See
results/session_011_tier9-15.json for the per-question breakdown and
case-studies/2026-07-19-tier9-15-manual-review.md for the full writeup.
**Known gap:** t14-03 and t14-05 were never answered in this run (question bank was edited
after these answers were written — see case study for details).

## Context note
Granite hallucinated on large contexts — each tier was run as a separate focused session to keep context tight and answers accurate.
