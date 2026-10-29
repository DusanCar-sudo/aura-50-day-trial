# Archimedes verification audit — session 11019

## t3-01 (tier 3) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 7.9s — generating…
✓  [archimedes] prompt=2539tok ttft=7.9s first-answer=33.7s out=265tok 9.3 tok/s reasoning=188tok content=77tok total=36.5s
✓ ./ (+3 lines) 1ms
✓ Found 25 results for "secrets|agents\.env|process.env" (showing first 20 of 25 matches): (+21 lines) 29ms
✓  Archimedes: first token after 3.2s — generating…
```

## t3-02 (tier 3) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2529tok ttft=1.4s first-answer=33.6s out=973tok 26.3 tok/s reasoning=829tok content=144tok total=38.3s
✓  Archimedes handled the task without escalation.
✓ Done
```

## t3-03 (tier 3) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2532tok ttft=1.5s first-answer=9.7s out=579tok 28.2 tok/s reasoning=230tok content=349tok total=22.1s
✓  Archimedes handled the task without escalation.
✓ Done
```

## t3-04 (tier 3) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 1.0s — generating…
✓  [archimedes] prompt=2542tok ttft=1.0s first-answer=8.4s out=290tok 30.0 tok/s reasoning=212tok content=78tok total=10.7s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11019/t3-04): /home/dusan/app/index.js. Use a path relative to the project root.
✓  Archimedes: first token after 1.9s — generating…
✓  [archimedes] prompt=2912tok ttft=1.9s first-answer=73.0s out=2100tok 25.9 tok/s reasoning=1920tok content=180tok total=82.8s
```

## t3-05 (tier 3) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 1.1s — generating…
✓  [archimedes] prompt=2540tok ttft=1.1s first-answer=7.6s out=313tok 28.9 tok/s reasoning=185tok content=128tok total=11.9s
✓ aura-code-src/src/agent/ (+12 lines) 2ms
✓  Archimedes: first token after 1.2s — generating…
✓  [archimedes] prompt=2781tok ttft=1.2s first-answer=2.8s out=127tok 25.4 tok/s reasoning=37tok content=90tok total=6.2s
```

## t30-01 (tier 30) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 5.9s — generating…
✓  [archimedes] prompt=2530tok ttft=5.9s first-answer=12.1s out=202tok 26.3 tok/s reasoning=153tok content=49tok total=13.6s
✓ Found 1 result for "stats\.ts":
✓  Archimedes: first token after 2.2s — generating…
✓  [archimedes] prompt=2784tok ttft=2.2s first-answer=18.6s out=378tok 22.1 tok/s reasoning=356tok content=22tok total=19.3s
```

## t30-02 (tier 30) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 6.1s — generating…
✓  [archimedes] prompt=2525tok ttft=6.1s first-answer=10.7s out=138tok 27.2 tok/s reasoning=118tok content=20tok total=11.2s
✓ Found 1 result for "stats\.ts":
✓  Archimedes: first token after 1.7s — generating…
✓  [archimedes] prompt=2722tok ttft=1.7s first-answer=8.2s out=129tok 17.2 tok/s reasoning=110tok content=19tok total=9.3s
```

## t30-03 (tier 30) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 12.6s — generating…
✓  [archimedes] prompt=2532tok ttft=12.6s first-answer=19.3s out=129tok 12.2 tok/s reasoning=71tok content=58tok total=23.2s
✓ No results for "formatStats"
✓  Archimedes: first token after 3.7s — generating…
✓  [archimedes] prompt=2706tok ttft=3.7s first-answer=9.6s out=113tok 13.5 tok/s reasoning=73tok content=40tok total=12.1s
```

## t30-04 (tier 30) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ (command completed with no output)
✓ Found 3 results for "No episodes|no episodes|episodes recorded": (+4 lines) 35ms
✓ Found 21 results for "stats": (+22 lines) 17ms
✓ command-palette.ts (+12 lines) 22ms
✓ aura-code-src/src/archimedes/episode-capture.ts (lines 1–145 of 145): (+146 lines) 1ms
✓ src/orchestration/strategy.ts:154:    return episodeStore.getEpisodeStats(this.projectRoot); (+16 lines) 23ms
```

## t30-05 (tier 30) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ (command completed with no output)
✓ Found 9 results for "totalTokens|total_tokens": (+10 lines) 41ms
✓ --- (+7 lines) 25ms
✓ ./aura-code-src/src/research/council.ts (+11 lines) 18ms
✓ aura-code-src/src/cli/help-data.ts:79:  '  /stats, /usage          Show token + cost usage this session',
✓ ./aura-code-src/src/kanban/pipeline.ts:621:    const statsPath = path.join(projectRoot, 'src/archimedes/stats.ts'); (+5 lines) 19ms
```

## t31-01 (tier 31) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 3ms
✓ total 4 (+9 lines) 57ms
✓ { (+43 lines) 23ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 0ms
✓ env.ts (+8 lines) 26ms
✓ aura-code-src/src/providers/resilient.ts (lines 120–170 of 175): (+52 lines) 0ms
```

## t31-02 (tier 31) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+6 lines) 11ms
✓ { (+57 lines) 35ms
✓ written
✓ == TS == (+29 lines) 4482ms
✓ /bin/sh: line 1: cd: /tmp/aura-bench/session_11019/t31-02/line-readers: No such file or directory
```

## t31-03 (tier 31) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 4 (+10 lines) 31ms
✓ { (+62 lines) 37ms
✓ src (+5 lines) 26ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
✓ written
```

## t31-04 (tier 31) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 4 (+6 lines) 23ms
✓ aura-code-src/src/util/load-env.ts (+71 lines) 33ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 3ms
✓ src (+3 lines) 25ms
✓ import * as fs from 'fs'; (+62 lines) 2239ms
```

## t31-05 (tier 31) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 3ms
✓ total 4 (+6 lines) 45ms
✓ { (+61 lines) 24ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 0ms
✓ aura-code-src/src/util/env.ts (78 lines): (+79 lines) 0ms
✓ /usr/bin/node (+10 lines) 404ms
```

## t32-01 (tier 32) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 3ms
✓ total 4 (+9 lines) 34ms
✓ { (+43 lines) 31ms
✓ import { ApiError } from './errors.js'; (+56 lines) 27ms
✓ ./tools/index.ts (+5 lines) 32ms
✓ import * as fs from 'fs'; (+58 lines) 15ms
```

## t32-02 (tier 32) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ aura-code-src/src/util/ (+3 lines) 3ms
✓ aura-code-src/
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
✓ . (+30 lines) 33ms
✓ src/tools: (+22 lines) 21ms
✓ ✓ Created aura-code-src/src/util/debounce.ts (87 lines)
```

## t32-03 (tier 32) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 4 (+6 lines) 22ms
✓ { (+49 lines) 28ms
✓ total 0 (+7 lines) 25ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
✓ written (+7 lines) 37ms
```

## t32-05 (tier 32) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 4 (+6 lines) 27ms
✓ { (+49 lines) 26ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
✓ aura-code-src/src/agent/affect.ts (+44 lines) 22ms
✓ . (+40 lines) 25ms
```

## t33-01 (tier 33) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ { (+45 lines) 21ms
✓ tools: (+32 lines) 40ms
✓ ./server/index.ts:29:  const token = process.env.AURA_SERVER_TOKEN || crypto.randomBytes(24).toString('hex'); (+31 lines) 31ms
✓ import * as fs from 'fs'; (+38 lines) 18ms
✗  Loop ended after 5 turns (cap: 5).
```

## t33-02 (tier 33) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
Task: Write a function that hashes a password using bcrypt or argon2 and verifies it. Show in TypeScript, Python, and Go.
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 4 (+5 lines) 32ms
✓ aura-code-src/src/util/load-env.ts (+42 lines) 34ms
✓ src (+3 lines) 38ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
```

## t33-03 (tier 33) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
Task: Write a function that signs a JWT token and verifies it. Show in TypeScript, Python, and Go.
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+6 lines) 24ms
✓ .aura.json (14 lines): (+15 lines) 1ms
✓ .aura/token-log.jsonl (3 lines): (+4 lines) 0ms
✓ aura-code-src/src/util/load-env.ts (+51 lines) 25ms
```

## t33-04 (tier 33) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+5 lines) 39ms
✓ aura-code-src/src/util/load-env.ts (+48 lines) 20ms
✓ permissions.ts
✓ 97:  /** Strategy body. `opts.permissions` is guaranteed set and sanitized. */ (+31 lines) 18ms
✓ ok
```

## t34-01 (tier 34) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+9 lines) 29ms
✓ { (+48 lines) 79ms
✓ go
✓ settled #1 (+24 lines) 848ms
✓ settled #19 (+11 lines) 882ms
```

## t34-02 (tier 34) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+5 lines) 25ms
✓ aura-code-src/src/util/load-env.ts (+59 lines) 35ms
✓ aura-code-src/src/util/retry.ts (76 lines): (+77 lines) 1ms
✓ src (+5 lines) 24ms
✓ ok
```

## t34-03 (tier 34) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+5 lines) 28ms
✓ aura-code-src/src/util/load-env.ts (+48 lines) 15ms
✓ /usr/bin/go (+7 lines) 82ms
✓ ✓ Created counter/go/main.go (64 lines)
✓ ✓ Created counter/rust/src/main.rs (73 lines)
```

## t34-05 (tier 34) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+10 lines) 64ms
✓ aura-code-src/src/util/load-env.ts (+48 lines) 20ms
✓ import { ApiError } from './errors.js'; (+44 lines) 18ms
✓ ok
✓ id=1 value="RAW-1" len=5 (+6 lines) 1149ms
```

## t35-01 (tier 35) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
I'll write all five implementations into the project as runnable files, then verify each one actually runs.
✓ ./ (+3 lines) 2ms
✓ ✓ Created binary-search/binary_search.ts (61 lines)
✓ ✓ Created binary-search/binary_search.py (58 lines)
✓ ✓ Created binary-search/binary_search.go (82 lines)
✓ ✓ Created binary-search/binary_search.rs (78 lines)
```

## t35-02 (tier 35) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ total 4 (+7 lines) 23ms
✓ { (+64 lines) 20ms
✓ written
✓ total 4 (+11 lines) 2489ms
✓ === PY ===
```

## t35-03 (tier 35) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 1ms
✓ . (+7 lines) 35ms
✓ { (+46 lines) 25ms
✓ written (+4 lines) 33ms
✓ /bin/sh: line 1: cd: /tmp/aura-bench/session_11019/t35-03/aura-code-src/src/util/floyd: No such file or directory
✓ /tmp/aura-bench/session_11019/t35-03/floyd (+6 lines) 25ms
```

## t35-04 (tier 35) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
I'll write merge sort in all four languages, then verify each one actually runs and sorts correctly.
✓ ./ (+3 lines) 1ms
✓ /usr/bin/node (+10 lines) 109ms
✓ ✓ Created merge-sort/mergeSort.ts (90 lines)
✓ ✓ Created merge-sort/merge_sort.py (84 lines)
✓ ✓ Created merge-sort/merge_sort.go (108 lines)
```

## t35-05 (tier 35) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓ ./ (+5 lines) 2ms
✓ total 0 (+48 lines) 44ms
✓ v26.12.0 (+4 lines) 2255ms
✓ /mnt/bigdata/aura/projects/trie
✓ written
✗  Loop ended after 5 turns (cap: 5).
```

## Confidence vs truth matrix
| claim | correct | partial | wrong |
|---|---|---|---|
| claims-true | 8 | 19 | 5 |
