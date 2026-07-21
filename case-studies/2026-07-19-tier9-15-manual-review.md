# Manual Review: Tier 9–15 Answers, Run 2 (Post Granite-Context-Fix)

**Date:** 2026-07-19
**Type:** Manual quality read-through — NOT scorer output
**Status:** Unscored — pending real `key_points`-based scoring

## Why this isn't an official score

`Aura_Benchmark`'s `scorer.py` and the `tier9.json`–`tier19.json`
`key_points` arrays live locally in `/run/media/dusan/DATA1/Aura_Benchmark`
and have never been committed — that repo has zero commits as of this
writing. No automated scoring pipeline has been run against these
answers. What follows is a human/manual read of the answer text for
technical correctness, done as a stopgap so this run isn't lost, not a
replacement for `score_keyword`.

**Do not treat the percentages below as comparable to session pass
rates** (e.g. session 010's 90%). Those come from `scorer.py`; this
does not.

## Context

Prior session's tiers 9–19 run scored 37.3% via `scorer.py`, but that
was attributed to scorer strictness (verbose `key_points` failing to
substring-match), not answer quality — real quality was estimated at
~70%. Separately, it was discovered that Ruby's local Granite model was
failing on tasks with large context, which could also depress answer
quality independent of the scorer issue.

This is "Run 2" — generated after the Granite context-handling fix,
tiers 9–15 only (61-19 not yet reviewed).

## Review results

| Tier | Topic | Answers present | Manual verdict |
|---|---|---|---|
| 9 | Vision pipeline | 5/5 | 5/5 correct |
| 10 | Multi-agent / council | 5/5 | 5/5 correct |
| 11 | Ecosystem (Aura/AgentMesh/etc) | 5/5 | 5/5 correct |
| 12 | Benchmark integrity | 5/5 | 5/5 correct |
| 13 | Context & concurrency | 5/5 | 5/5 correct |
| 14 | Security | 3/5 | 3/3 correct, **2 missing (t14-04, t14-05)** |
| 15 | Measurement pitfalls | 5/5 | 5/5 correct |

**31/31 present answers read as technically correct** on a manual
pass — accurate mechanism-level reasoning, not just correct-sounding
prose. Notable strengths: t13-01 and t13-03 correctly reason through
*timing* (between-turn compaction checks, cache invalidation) rather
than just naming the problem; t9-01 through t9-05 correctly trace the
`--image` flag gap through the actual code path instead of describing
it abstractly.

**Gap:** t14-04 and t14-05 were not included in the uploaded
`tier14answ.md` — unclear whether they weren't generated in Run 2 or
were dropped before upload. Needs follow-up before this tier is
considered complete.

## Next steps (unchanged from prior handoff, still blocking)

1. Rewrite `key_points` in `tier9.json`–`tier19.json` to short 2–5 word
   phrases so `score_keyword` can actually match real answers.
2. Run `scorer.py` for real against these Run 2 answers once (1) is
   done — this manual review is not a substitute.
3. Fill the t14-04 / t14-05 gap.
4. Once scored for real, decide whether Run 2 gets recorded as an
   official session (tiers 9–19 haven't been part of `daily_run.sh`'s
   automated tiers 1–8 pipeline yet — that integration is still open).
