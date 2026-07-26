# Aura 50-Day Trial

> ## 🔴 Trial paused — hardware limitation + broken automation
>
> **Status: paused as of 2026-07-26. Daily collection is stopped.**
>
> Two separate problems, neither of them the model or the approach:
>
> **1. The daily automation has been failing since 2026-07-24.** The systemd
> service runs with an empty environment, so it couldn't find the `aura`
> binary (installed under nvm) on its `PATH`. Every scheduled run since then
> aborted at the first question, before reaching any model. Three days of
> scheduled runs produced nothing — not bad results, no results.
>
> **2. The GPU serving the local model has become unstable.** The AMD Radeon
> 680M iGPU running Ollama crashes under sustained load — roughly half of
> longer requests fail with a driver-level error
> (`vk::Queue::submit: ErrorDeviceLost`). These failures can look identical
> to a normal empty response unless you check the underlying logs directly,
> which means benchmark data collected right now couldn't be trusted.
>
> Rather than keep collecting numbers we can't stand behind, the trial is
> paused and the daily timer is disabled until both are resolved. Everything
> published so far reflects real, verified runs — the existing dashboard is
> not affected by either issue, since both were caught before further
> collection rather than after.
>
> **What's being tried first:** setting an explicit `PATH` in the systemd
> unit, and lowering `OLLAMA_CONTEXT_LENGTH` to reduce memory pressure on the
> iGPU — the cheapest things to test before anything more invasive
> (different GPU config, different hardware, or a different local-inference
> backend).
>
> When the hardware issue is resolved, the **full benchmark will be re-run
> from scratch** — not resumed from where it left off — and the complete
> comparison published, so the before/after is honest and whole.
>
> *"I don't try. I verify"* cuts both ways: better to stop and redo it
> properly than publish numbers we can't vouch for.

Daily, automated, unedited proof: does Aura's Ruby Alternator get
measurably better over 50 days of real use?

## 📊 Live Dashboard
**[View live charts →](https://dusancar-sudo.github.io/aura-50-day-trial/)**

Pass rate trend, verification catch rate, and Ruby competence by category —
updated automatically every day. No download needed.

## Setup
- **Large model (cloud):** DeepSeek Chat (`deepseek/deepseek-chat`) — the escalation target the benchmark runs against (`runner/run.py`)
- **Local model (Ruby Alternator):** `gemma-archimedes-gen2` — a local fine-tune of Gemma-4-E2B, 4.6B parameters, Q4_K_M, served by Ollama on an AMD Radeon 680M iGPU (`.aura.json`)
- **Ruby Alternator:** local model attempts every task first, gets verified by the large model, escalates on failure or low competence

> **Note:** earlier revisions of this README described the setup as GLM-5.2 plus
> Granite 4.1 3B on CPU. Both changed during the trial — the local model moved to
> the `gemma-archimedes-gen2` fine-tune and the escalation target to DeepSeek Chat —
> and the README wasn't updated at the time. Corrected 2026-07-26 to match what the
> code actually runs. Published results were produced by the configuration described
> above, not the one previously documented here.

## What is this?
Every day a systemd timer runs the full Aura benchmark suite (115 questions,
tiers 1-19) against the current state of Ruby Alternator's accumulated
episode/competence history, and commits the raw result here — good day or
bad day, nothing is cherry-picked.

See [CHARTER.md](CHARTER.md) for the full architecture and success metrics.

## Case Studies
Real incidents — infrastructure failures, bugs found, fixes applied:
- [2026-07-17 — Ollama port collision: why sessions 002 and 008 scored near zero](case-studies/2026-07-17-ollama-port-collision.md)
- [2026-07-17 — Catching Ruby fabricating a function that doesn't exist](case-studies/2026-07-17-fabrication-catch.md)

## Structure
- `logs/` — one dated entry per day
- `results/` — raw benchmark JSON + session notes per day
- `case-studies/` — real incidents: what broke, why, how it was fixed
- `scripts/daily_run.sh` — the automation itself
- `index.html` — the live dashboard (auto-regenerated daily)
