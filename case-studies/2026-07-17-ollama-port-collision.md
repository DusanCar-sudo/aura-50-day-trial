# Incident Report: Ollama Port Collision — 2026-07-17

**Severity:** High — caused two benchmark sessions to produce misleading results
**Status:** Resolved
**Affected sessions:** 002 (0%), 008 (30% with timeouts)

---

## What Was Observed

The first two benchmark sessions returned scores far below what the
system was capable of:

- **Session 002:** 0% — every answer was empty or wrong
- **Session 008:** 30% — 7 out of 20 questions hit the 180-second
  timeout and returned nothing

At the time these were recorded as real results and committed to the
trial repo. They are not representative of the system's actual capability.

---

## Root Cause

Two separate issues stacked on top of each other:

### Issue 1 — Ollama restart loop (confirmed from system logs)

When the systemd Ollama service was first enabled, a manually-started
`ollama serve` process was already running and holding port 11434.
The new systemd service tried to bind the same port, failed immediately,
and restarted — every 3 seconds, indefinitely.

**System log evidence (2026-07-17 17:10:58 — 17:11:30+):**

```
Jul 17 17:10:58 ollama[450341]: Error: listen tcp 127.0.0.1:11434: bind: address already in use
Jul 17 17:10:58 systemd[1]: ollama.service: Failed with result 'exit-code'.
Jul 17 17:11:01 systemd[1]: ollama.service: Scheduled restart job, restart counter is at 1.
Jul 17 17:11:01 ollama[450361]: Error: listen tcp 127.0.0.1:11434: bind: address already in use
Jul 17 17:11:01 systemd[1]: ollama.service: Failed with result 'exit-code'.
Jul 17 17:11:04 systemd[1]: ollama.service: Scheduled restart job, restart counter is at 2.
...
Jul 17 17:11:30 systemd[1]: ollama.service: Scheduled restart job, restart counter is at 10.
```

The restart counter reached at least 21 before the stale process was
identified and killed. During this entire window, every Ruby attempt
to Granite returned a connection error or empty response — not because
Granite failed, but because Ollama itself was in a crash loop.

### Issue 2 — Context window too small

Even when Ollama was running, it was loading Granite with the default
4096-token context window. Aura's system prompt + tool definitions
exceed 4096 tokens — so every real inference attempt either:
- Returned word salad (model degraded at context limit)
- Returned a 400 error (`request exceeds available context size`)

This is why Session 008 produced partial results rather than zero —
some questions fit within 4096 tokens, others didn't.

### Issue 3 — Silent failure

Neither issue produced a visible error in the Aura TUI that would have
flagged the problem to a human observer. The Ruby Principle panel showed
"empty response" and escalated to the cloud model, which itself failed
due to the same underlying Ollama instability. Results looked like
low performance rather than infrastructure failure.

---

## How It Was Diagnosed

1. **`pgrep -a ollama`** — revealed two separate ollama processes
   running simultaneously
2. **`sudo lsof -i :11434`** — showed the stale manual process holding
   the port (PID 449921)
3. **`sudo journalctl -u ollama -n 40`** — showed the 3-second restart
   loop with "address already in use" errors
4. **Direct curl test** — confirmed Ollama itself was reachable once
   the port conflict was resolved, but responses were incoherent until
   the context window was raised

---

## Fix Applied

1. **Killed the stale process:** `kill -9 449921`
2. **Restarted the systemd service cleanly**
3. **Raised context window to 16384** via systemd environment variable:
   ```
   Environment="OLLAMA_CONTEXT_LENGTH=16384"
   ```
4. **Confirmed with a real test:** a prompt of ~15,500 characters
   returned a coherent `Hello!` response (previously returned word
   salad at 4096 tokens)
5. **Disabled Vulkan GPU acceleration** (`GGML_VK_VISIBLE_DEVICES=""`)
   to force CPU-only inference — this eliminated the prefill bottleneck
   that was causing 6-minute hangs on the first token

---

## What the Real Baseline Looks Like

Once the environment was clean:

| Session | Model | Score | Notes |
|---|---|---|---|
| 009 | DeepSeek + Granite | 80% / 20 questions | First clean TUI session |
| 010 | GLM-5.2 + Granite | 90% / 60 questions | Full tier 1-8 benchmark |
| 012 | GLM-5.2 + Granite | 80% / 25 questions | Tiers 15-19, hard reasoning |

Sessions 002 and 008 remain in the repo as-is — no cherry-picking,
no deletion. They are labeled as infrastructure failures, not model
failures.

---

## Lesson

The 50-day trial's "no cherry-picking" rule applies to genuine
performance data. It does not mean infrastructure failures should be
treated as valid performance measurements. The correct approach —
which we followed — is to document the failure in detail, publish the
logs, and establish the real baseline once the environment is verified.

A benchmark that silently absorbs infrastructure failures into its
trend line is not more honest — it's less informative.
