# Aura Benchmark — Answers

## Tier 11

### t11-01

### t11-01
The `tokensUsed` object in the `Episode` interface (in `src/archimedes/types.ts`) has the structure:
```
tokensUsed: { archimedes?: number; largeModel?: number }
```
It is an object with two optional numeric fields — `archimedes` (token count used by the small model) and `largeModel` (token count used by the large model). Only the model that actually executed the task has its field populated.

### t11-02
The default task category returned by `inferTaskCategory` (in `src/archimedes/alternator.ts`) when no regex patterns match is `'other'`. The function checks for patterns in this order: `review`, `research`, `refactor`, `implementation` — and the final fallback `return 'other'` catches anything that doesn't match those four patterns.

### t11-03
In `src/archimedes/episode-capture.ts`, the `loadEpisodes` method inspects two properties of the parsed JSON object to verify it is a valid episode: `parsed?.id` must be truthy (exists and is non-null) AND `typeof parsed.timestamp === 'number'` must be true. If either check fails, the file is skipped as corrupt.

```typescript
if (parsed?.id && typeof parsed.timestamp === 'number') {
  episodes.push(parsed);
}
```

### t11-04
The `durationMs` field in the `Episode` interface represents the **wall-clock duration** of the episode in **milliseconds**. In `src/archimedes/alternator.ts`, it is measured by capturing `const startMs = Date.now()` at the beginning of the alternation run (line 278) and then computing `Date.now() - startMs` (line 464) when the episode object is constructed, giving the elapsed real-world time.

### t11-05
In `src/archimedes/episode-capture.ts`, the filename of a stored episode is named **`${id}.json`** via the `episodePath` method (line 44-46):
```typescript
episodePath(projectRoot: string, id: string): string {
  return path.join(this.projectDir(projectRoot), `${id}.json`);
}
```
The episode is saved by `saveEpisode` which calls `episodePath(projectRoot, episode.id)` to determine the full file path, then writes the JSON-serialized episode to that path (using an atomic write via `.tmp` + `rename`).

## Tier 12

### t12-01
In `AlternatorOptions` (`src/archimedes/alternator.ts`, line 24-42), the default permission level assigned to the `permissions` property if none is provided is `'normal'`. The constructor (line 270) does:
```typescript
this.permissions = opts.permissions ?? new PermissionSystem('normal');
```
This is intentionally NOT `'auto'` — the Archimedes attempt must not auto-approve destructive operations the user's chosen mode would have prompted for.

### t12-02
The provider class instantiated in `buildArchimedesProvider` to talk to local Ollama is **`OpenAICompatibleProvider`** (imported from `'../providers/openai-compatible.js'`). The function at line 243-252 creates an instance with the Archimedes model name, the Ollama base URL, and `apiKey: 'ollama'`, labeled `'Archimedes (Ollama)'`.

### t12-03
The alternator passes `initialHistory` to **both** inner agent loops unconditionally — whenever it is set in `AlternatorOptions`. Specifically:
- **Archimedes loop** (line 345): `initialHistory: this.opts.initialHistory`
- **Large model loop** (line 426): `initialHistory: this.opts.initialHistory`

The `initialHistory` field holds prior conversation history for multi-turn REPL sessions. It is always threaded into both `runAgentLoop` calls so that either model can continue from where the conversation left off.

### t12-04
The `display` option in `AlternatorOptions` implements the **`Display`** interface (imported from `'../cli/display.js'`). If the option is omitted, the constructor falls back to a **no-op display** created by `createNoopDisplay()` (line 92), which returns an object with empty function stubs for every display method (`agentThinking`, `streamText`, `streamEnd`, `toolBlocked`, `warning`, `success`, `error`, `header`, `summary`, `showPlan`, `stepStarted`, `stepCompleted`, `contextBar`, `contextDashboard`, `compactionEvent`) — all `() => {}`, silently swallowing all UI output.

### t12-05
The `abortSignal` is propagated to both inner agent loops by passing `abortSignal: this.opts.abortSignal` in the options object to both `runAgentLoop` calls:
- **Archimedes loop** (line 346): `abortSignal: this.opts.abortSignal`
- **Large model loop** (line 427): `abortSignal: this.opts.abortSignal`

This supports REPL features like Ctrl+C / `:stop` — the signal from the parent context is forwarded directly so that either agent loop can be terminated cleanly from the UI layer.
