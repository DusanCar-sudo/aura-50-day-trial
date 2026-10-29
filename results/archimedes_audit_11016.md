# Archimedes verification audit — session 11016

## t1-01 (tier 1) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 3.0s — generating…
✓  [archimedes] prompt=2517tok ttft=3.0s first-answer=18.3s out=1183tok 33.7 tok/s reasoning=532tok content=651tok total=38.1s
⚠  Archimedes's answer failed verification (The answer contains factual errors about TypeScript (e.g., claiming interfaces cannot be extended directly, cannot be assigned, and that types "can be used as a value"), and no tools were called to verify anything.) — escalating.
I'll verify the key claims against real TypeScript behavior rather than trusting the prior answer.
✓ /usr/bin/node (+3 lines) 49ms
```

## t1-02 (tier 1) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.6s — generating…
✓  [archimedes] prompt=2518tok ttft=4.6s first-answer=14.0s out=536tok 32.6 tok/s reasoning=304tok content=232tok total=21.0s
⚠  Archimedes's answer failed verification (misstates commit types (should be pick/reword/edit/squash/fixup) and falsely claims Git "automatically re-runs" commits after saving without user action.) — escalating.
✓ Done
```

## t1-04 (tier 1) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2517tok ttft=4.2s first-answer=10.6s out=251tok 33.4 tok/s reasoning=213tok content=38tok total=11.7s
✓  Archimedes handled the task without escalation.
✓ Done
```

## t1-05 (tier 1) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2515tok ttft=4.4s first-answer=10.4s out=348tok 33.4 tok/s reasoning=200tok content=148tok total=14.8s
✓  Archimedes handled the task without escalation.
✓ Done
```

## t10-01 (tier 10) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.3s — generating…
✓  [archimedes] prompt=2551tok ttft=4.3s first-answer=8.0s out=270tok 33.5 tok/s reasoning=124tok content=146tok total=12.4s
✓ Found 9 results for "ruby diamond client|council|multi-agent|bots from different providers": (+10 lines) 37ms
✓  Archimedes: first token after 2.0s — generating…
✓  [archimedes] prompt=3033tok ttft=2.0s first-answer=3.2s out=137tok 33.3 tok/s reasoning=39tok content=98tok total=6.1s
```

## t10-02 (tier 10) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
Task: Contrast Aura's Ruby Alternator (small model attempts, gets verified, escalates on failure) with a council-debate model (N models argue, one is picked). Which approach spends fewer tokens on a typical Tier 1 factual question, and why?
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2561tok ttft=4.2s first-answer=8.8s out=233tok 34.1 tok/s reasoning=157tok content=76tok total=11.0s
✓ Found 16 results for "alternator|Alternator" (showing first 15 of 16 matches): (+16 lines) 32ms
✓ Found 7 results for "council|debate|argu": (+8 lines) 22ms
```

## t10-03 (tier 10) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2541tok ttft=4.4s first-answer=7.6s out=122tok 33.8 tok/s reasoning=102tok content=20tok total=8.0s
✓ No results for "lean_agent"
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2684tok ttft=1.4s first-answer=2.7s out=79tok 33.8 tok/s reasoning=40tok content=39tok total=3.7s
```

## t10-04 (tier 10) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.1s — generating…
✓  [archimedes] prompt=2563tok ttft=4.1s first-answer=6.6s out=219tok 35.4 tok/s reasoning=88tok content=131tok total=10.3s
✓ aura-code-src/src/orchestration/ (+7 lines) 2ms
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t10-04): /mpa-mnt/bigdata/aura/aura-code-src/src/orchestration. Use a path relative to the project root.
✓  Archimedes: first token after 1.4s — generating…
```

## t10-05 (tier 10) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2542tok ttft=4.4s first-answer=6.8s out=200tok 33.7 tok/s reasoning=80tok content=120tok total=10.3s
✓ No results for "Honcho|honcho"
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2710tok ttft=1.4s first-answer=3.9s out=132tok 33.8 tok/s reasoning=78tok content=54tok total=5.3s
```

## t11-01 (tier 11) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2524tok ttft=4.2s first-answer=9.4s out=211tok 34.9 tok/s reasoning=175tok content=36tok total=10.3s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t11-01): /mnt/bigdata/aura/aura-code/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2795tok ttft=1.5s first-answer=4.5s out=141tok 34.1 tok/s reasoning=93tok content=48tok total=5.6s
```

## t11-02 (tier 11) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2526tok ttft=4.4s first-answer=7.1s out=105tok 33.6 tok/s reasoning=84tok content=21tok total=7.6s
✓ Found 1 result for "inferTaskCategory":
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2682tok ttft=1.4s first-answer=2.6s out=83tok 33.6 tok/s reasoning=36tok content=47tok total=3.9s
```

## t11-03 (tier 11) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
Task: In episode-capture.ts, what properties of the parsed JSON object does loadEpisodes inspect to verify it is a valid episode?
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
The user wants to know about `loadEpisodes` function in `episode-capture.ts`, specifically which properties of the parsed JSON object it inspects to verify if it's a valid episode. I need to find this file and read its contents.
✓  [archimedes] prompt=2533tok ttft=4.4s first-answer=6.4s out=98tok 33.7 tok/s reasoning=60tok content=38tok total=7.3s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t11-03): /mnt/bigdata/aura/aura-code/src. Use a path relative to the project root.
```

## t11-04 (tier 11) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2528tok ttft=4.4s first-answer=6.5s out=132tok 33.4 tok/s reasoning=68tok content=64tok total=8.4s
✓ Found 14 results for "durationMs": (+15 lines) 32ms
✓ Found 2 results for "alternator\.ts": (+3 lines) 19ms
✓  Archimedes: first token after 2.3s — generating…
```

## t12-01 (tier 12) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.3s — generating…
✓  [archimedes] prompt=2530tok ttft=4.3s first-answer=6.3s out=82tok 34.4 tok/s reasoning=62tok content=20tok total=6.7s
✓ Found 3 results for "AlternatorOptions": (+4 lines) 36ms
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2729tok ttft=1.5s first-answer=3.0s out=77tok 34.3 tok/s reasoning=46tok content=31tok total=3.7s
```

## t12-02 (tier 12) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2531tok ttft=4.4s first-answer=9.4s out=183tok 33.7 tok/s reasoning=161tok content=22tok total=9.9s
✓ Found 1 result for "buildArchimedesProvider":
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2774tok ttft=1.5s first-answer=2.1s out=62tok 33.9 tok/s reasoning=15tok content=47tok total=3.3s
```

## t12-03 (tier 12) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.6s — generating…
✓  [archimedes] prompt=2522tok ttft=4.6s first-answer=7.0s out=111tok 33.7 tok/s reasoning=74tok content=37tok total=7.9s
✓ Found 3 results for "initialHistory": (+4 lines) 35ms
✓ Found 16 results for "alternator" (showing first 15 of 16 matches): (+16 lines) 23ms
✓  Archimedes: first token after 2.6s — generating…
```

## t12-04 (tier 12) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2527tok ttft=4.2s first-answer=6.3s out=113tok 34.0 tok/s reasoning=70tok content=43tok total=7.6s
✓ Found 3 results for "AlternatorOptions": (+4 lines) 36ms
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2687tok ttft=1.4s first-answer=2.7s out=69tok 34.1 tok/s reasoning=38tok content=31tok total=3.4s
```

## t12-05 (tier 12) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.3s — generating…
✓  [archimedes] prompt=2525tok ttft=4.3s first-answer=6.6s out=206tok 33.8 tok/s reasoning=78tok content=128tok total=10.4s
✓ Found 4 results for "alternator.*run|run.*alternator": (+5 lines) 33ms
✓  Archimedes: first token after 1.7s — generating…
✓  [archimedes] prompt=2817tok ttft=1.7s first-answer=3.1s out=108tok 33.7 tok/s reasoning=45tok content=63tok total=5.0s
```

## t13-01 (tier 13) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 3.9s — generating…
✓  [archimedes] prompt=2523tok ttft=3.9s first-answer=5.8s out=81tok 35.2 tok/s reasoning=61tok content=20tok total=6.2s
✓ Found 1 result for "competence.ts":
✓  Archimedes: first token after 1.2s — generating…
✓  [archimedes] prompt=2666tok ttft=1.2s first-answer=6.3s out=202tok 35.1 tok/s reasoning=169tok content=33tok total=7.0s
```

## t13-02 (tier 13) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.5s — generating…
✓  [archimedes] prompt=2527tok ttft=4.5s first-answer=7.1s out=115tok 33.7 tok/s reasoning=79tok content=36tok total=7.9s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t13-02): /mnt/bigdata/aura/aura-code/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2702tok ttft=1.4s first-answer=2.6s out=67tok 34.1 tok/s reasoning=35tok content=32tok total=3.4s
```

## t13-03 (tier 13) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2529tok ttft=4.2s first-answer=6.2s out=81tok 33.8 tok/s reasoning=62tok content=19tok total=6.6s
✓ Found 1 result for "tasksSimilar":
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2661tok ttft=1.4s first-answer=1.8s out=41tok 34.5 tok/s reasoning=10tok content=31tok total=2.5s
```

## t13-04 (tier 13) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.5s — generating…
✓  [archimedes] prompt=2534tok ttft=4.5s first-answer=7.8s out=195tok 33.6 tok/s reasoning=103tok content=92tok total=10.3s
✓ No results for "model-selector"
✓ Found 1 result for "competence.ts":
✓  Archimedes: first token after 1.6s — generating…
```

## t13-05 (tier 13) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.2s — generating…
✓  [archimedes] prompt=2533tok ttft=4.2s first-answer=11.8s out=308tok 33.8 tok/s reasoning=255tok content=53tok total=13.3s
✓ No results for "jaccard|Jaccard|jacard"
✓  Archimedes: first token after 1.3s — generating…
✓  [archimedes] prompt=2613tok ttft=1.3s first-answer=3.4s out=86tok 33.6 tok/s reasoning=65tok content=21tok total=3.8s
```

## t14-01 (tier 14) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.3s — generating…
✓  [archimedes] prompt=2540tok ttft=4.3s first-answer=7.8s out=142tok 34.9 tok/s reasoning=118tok content=24tok total=8.3s
✓ Found 7 results for "DEFAULT_ARCHIMEDES_CONFIG": (+8 lines) 35ms
✓  Archimedes: first token after 1.8s — generating…
✓  [archimedes] prompt=2934tok ttft=1.8s first-answer=3.0s out=65tok 35.1 tok/s reasoning=36tok content=29tok total=3.6s
```

## t14-02 (tier 14) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.5s — generating…
✓  [archimedes] prompt=2530tok ttft=4.5s first-answer=7.0s out=124tok 34.0 tok/s reasoning=79tok content=45tok total=8.1s
✓ Found 8 results for "ArchimedesConfig": (+9 lines) 34ms
✓ Found 5 results for "competenceThreshold|minAttempts": (+6 lines) 29ms
✓  Archimedes: first token after 2.4s — generating…
```

## t14-04 (tier 14) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.5s — generating…
✓  [archimedes] prompt=2535tok ttft=4.5s first-answer=8.0s out=186tok 33.8 tok/s reasoning=110tok content=76tok total=10.0s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t14-04): /mnt/bigdata/aura/aura-code-src/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.8s — generating…
✓  [archimedes] prompt=2840tok ttft=1.8s first-answer=7.5s out=196tok 33.7 tok/s reasoning=185tok content=11tok total=7.6s
```

## t14-05 (tier 14) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.6s — generating…
✓  [archimedes] prompt=2531tok ttft=4.6s first-answer=7.5s out=130tok 33.6 tok/s reasoning=91tok content=39tok total=8.5s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t14-05): /mnt/bigdata/aura/aura-code/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2722tok ttft=1.5s first-answer=6.1s out=172tok 33.6 tok/s reasoning=150tok content=22tok total=6.6s
```

## t15-01 (tier 15) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.6s — generating…
✓  [archimedes] prompt=2530tok ttft=4.6s first-answer=8.6s out=146tok 33.6 tok/s reasoning=126tok content=20tok total=9.0s
✓ Found 2 results for "alternator.ts": (+3 lines) 34ms
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2773tok ttft=1.5s first-answer=6.2s out=218tok 33.4 tok/s reasoning=150tok content=68tok total=8.0s
```

## t15-02 (tier 15) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2532tok ttft=4.4s first-answer=6.5s out=104tok 33.9 tok/s reasoning=63tok content=41tok total=7.5s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t15-02): /mnt/bigdata/aura/aura-code-src/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2698tok ttft=1.4s first-answer=9.7s out=321tok 33.5 tok/s reasoning=272tok content=49tok total=11.0s
```

## t15-03 (tier 15) — scorer: partial — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2532tok ttft=4.4s first-answer=6.7s out=175tok 33.7 tok/s reasoning=78tok content=97tok total=9.6s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t15-03): /mnt/bigdata/aura/aura-code-src/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2748tok ttft=1.5s first-answer=3.4s out=119tok 33.6 tok/s reasoning=59tok content=60tok total=5.0s
```

## t15-04 (tier 15) — scorer: incorrect — claims-true — **FALSE TRUE-CLAIM**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.4s — generating…
✓  [archimedes] prompt=2531tok ttft=4.4s first-answer=7.4s out=211tok 34.1 tok/s reasoning=99tok content=112tok total=10.6s
✗ Error: Path escapes the project root (/tmp/aura-bench/session_11016/t15-04): /mnt/bigdata/aura/aura-code/src. Use a path relative to the project root.
✓  Archimedes: first token after 1.5s — generating…
✓  [archimedes] prompt=2758tok ttft=1.5s first-answer=5.8s out=206tok 33.7 tok/s reasoning=135tok content=71tok total=7.7s
```

## t16-01 (tier 16) — scorer: correct — claims-true — **TRUE-CLAIM HELD**
```
▄█▀▀▀▀▀▀▀█▀                                                                         │  "I don't try. I verify."
✓  Using configured Archimedes model: lfm3-1.7b (LM Studio)
✓  Trying Archimedes (lfm3-1.7b on LM Studio)…
✓  Archimedes: first token after 4.5s — generating…
✓  [archimedes] prompt=2527tok ttft=4.5s first-answer=6.8s out=93tok 33.8 tok/s reasoning=73tok content=20tok total=7.2s
✓ Found 1 result for "competence.ts":
✓  Archimedes: first token after 1.4s — generating…
✓  [archimedes] prompt=2682tok ttft=1.4s first-answer=3.1s out=91tok 33.9 tok/s reasoning=53tok content=38tok total=4.1s
```

## Confidence vs truth matrix
| claim | correct | partial | wrong |
|---|---|---|---|
| claims-true | 22 | 7 | 3 |
