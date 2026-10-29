# Full run: lfm3-1.7b, all 320 questions (10 batches)

Sessions 11015-11024, one batch of 32 distinct questions each, 320 unique question ids in total.
Escalation/verifier model: deepseek/deepseek-chat. Scorer verdicts from `runner/scorer.py`.

| Batch | Session | Answering model | Correct | Partial | Incorrect | Correct % | Avg s/question |
|---|---|---|---|---|---|---|---|
| 1 | 11015 | lfm3-1.7b | 20 | 11 | 1 | 62.5 | 125 |
| 2 | 11016 | lfm3-1.7b | 22 | 7 | 3 | 68.8 | 62 |
| 3 | 11017 | lfm3-1.7b | 20 | 10 | 2 | 62.5 | 68 |
| 4 | 11018 | lfm3-1.7b | 23 | 7 | 2 | 71.9 | 97 |
| 5 | 11019 | lfm3-1.7b | 10 | 19 | 3 | 31.3 | 47 |
| 6 | 11020 | lfm3-1.7b | 23 | 5 | 4 | 71.9 | 139 |
| 7 | 11021 | **lfm3-omni-2b** | 18 | 14 | 0 | 56.3 | 56 |
| 8 | 11022 | lfm3-1.7b | 19 | 11 | 2 | 59.4 | 128 |
| 9 | 11023 | lfm3-1.7b | 26 | 6 | 0 | 81.3 | 163 |
| 10 | 11024 | lfm3-1.7b | 9 | 17 | 6 | 28.1 | 92 |
| **Total** | | | **190** | **107** | **23** | **59.4** | |

Excluding batch 7 (omni), lfm3-1.7b alone: 172 / 288 correct = 59.7 %.

## Archimedes audit

All 320 answers carry the label `claims-true`: Archimedes never marked an answer "possible" or hedged.
190 of those claims held; 130 were false true-claims (scorer says partial or incorrect), 40.6 %.

## Caveats

- Verifier changed between batches: batches 1-3 used the old verifier, batches 4-10 the three-gate verifier.
- The scorer was fixed mid-trial (banner glyph filter, CRLF fix for tier-3 code answers).
- Machine RAM and swap load differed between batches (swap was full during batch 8); not controlled for.
- Batches 5 and 10 are low outliers; cause not investigated.
