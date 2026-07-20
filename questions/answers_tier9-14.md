# Aura Benchmark Answers — Tiers 9–14

### Tier 9 Answers
**t9-01**: Today, running `aura -m qwen3-vl:4b --image ./screenshot.png "describe this"` would fail immediately because no --image flag exists in the current CLI argument parser. The provider layer is ready but the CLI is missing — `toOpenAIMessages` already builds a multimodal content array with images first then text, and `HistoryMessage` supports an optional `images` field. However, the images field is never populated because there is no code to parse `--image` and attach its contents. The pipeline fails at arg parsing, not at the model.

**t9-02**: The minimal implementation adds a `--image` flag in the CLI arg parser (in `cli/index.ts`). The flag handler uses `fs.readFileSync` + base64 encode to read the file and convert it. Then it must attach the result to the images array on the initial message. This change lands in `cli/index.ts` before `runAgentLoop` is called.

**t9-03**: Aura should warn and continue text-only. This choice averts two worse alternatives: warn and continue avoids silent data loss (if the image were silently dropped, the user would never know) and avoids a hard crash mid-session (which would kill the entire conversation). Ideally, the system should check model capability before sending the image, so the warning can fire even earlier.

**t9-04**: A CSS/layout misalignment bug — e.g., a sidebar rendered 20px too wide, overlapping the main content — is a task where a screenshot measurably outperforms text description. A visual diff between expected and actual render captures pixel-level spatial relationships that paragraphs of prose cannot. Similarly, an error dialog or stack trace screenshot preserves exact typography, line numbers, and formatting. In all these cases, spatial relationships are hard to describe in words but trivial to show in an image.

**t9-05**: Ruby's read-only restriction should not be loosened before enabling vision. The read-only restriction is orthogonal to modality — receiving images doesn't grant write access. There is no reason to gate vision behind permission level because the two capabilities are independent. Vision is an input channel, not a write capability. The competence threshold should still apply per task category, images included — meaning Ruby can receive images, evaluate them, and answer, but still cannot modify files or execute tools.
