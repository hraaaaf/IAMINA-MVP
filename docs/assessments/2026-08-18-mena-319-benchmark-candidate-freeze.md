# P0-MENA-4 / #319 — Benchmark candidate freeze — 2026-08-18

Status: **COST-FIRST PRE-RUN FREEZE / NO PAID OR NETWORK BENCHMARK EXECUTED**

Base SHA: `55cc5957c109f98cb217a942619087d8833a2745`

Canonical optimization plan: `docs/architecture/IAMINA_AI_COST_OPTIMIZATION_PLAN.md`

## Goal

Benchmark the least expensive architecture that preserves IAMINA's deterministic clinical authority, safety boundaries and acceptable FR/AR/Darija experience. Frontier-model performance is not the objective.

## Architectural principle

IAMINA's clinical/safety authority remains deterministic. Generative models narrate approved context only. Therefore model choice is optimized for language quality, reliability, latency and cost, not autonomous medical reasoning.

Decision order:

1. hard safety/privacy floor;
2. sufficient task quality;
3. FR/AR/Darija/mixed-language adequacy;
4. latency/availability;
5. total variable cost.

Among candidates that pass the hard floor, the cheapest adequate candidate wins.

## Candidate set

### Text Tier 1 — cheap narrator

1. DeepSeek V4 Flash
2. Gemini 2.5 Flash-Lite
3. Qwen low-cost API candidate — exact current account-visible model ID to be frozen before execution
4. Kimi low-cost candidate — exact current account-visible model ID to be frozen before execution
5. GPT-5 nano — ultra-cheap control

### Text Tier 2 — quality fallback

1. GPT-5 mini
2. best Tier-1 challenger if benchmark evidence supports a stronger variant

No frontier model is a routine candidate.

### STT

1. Voxtral Mini Transcribe 2
2. GPT-4o-mini-transcribe
3. xAI/Grok STT if current account-visible pricing/API availability remains competitive
4. on-device transcription as zero-cloud challenger where FR/AR/Darija quality is adequate

Higher-cost STT only if all cheaper candidates fail the quality floor.

### OCR / vision

1. local PaddleOCR PP-OCRv6 tiny/small
2. local medium model only if tiny/small fail
3. dedicated Mistral OCR 4 cloud fallback
4. Qwen small VLM / Gemini Flash-Lite only for tasks dedicated OCR cannot solve
5. general-purpose frontier VLM excluded unless all cheaper paths fail

### TTS

1. native iOS/Android TTS
2. cloud TTS only if native FR/AR/Darija intelligibility fails the UX floor

Fixed/help/safety phrases should be locally reusable rather than regenerated.

## Cost-reduction work to benchmark

- deterministic zero-model routing before any LLM;
- reduce raw history payload to compact governed state + last 1-2 turns;
- stable cacheable system prefix;
- remove unused structured-output fields;
- hard API output-token ceiling;
- prohibit routine reasoning/`think()`;
- at most one paid quality escalation per turn;
- STT silence trimming / compact encoding / duplicate-audio reuse;
- local OCR crop/preprocess first, cloud only for uncertain regions;
- no automatic vision analysis without explicit user intent;
- native TTS by default;
- per-patient cost ledger and circuit breakers.

## Execution constraints

- Synthetic/minimized repository fixtures only.
- No patient data.
- No credential committed to Git.
- Exact provider/model/API identity must be captured in each run record.
- Missing credential, model identity, budget authorization or execution authorization is STOP.
- Benchmark success does not authorize production or real-patient cutover.

## Verified code observations motivating the plan

- `companion.conversation` evaluates urgent/insulin/prescription safety before the LLM path.
- `core.llm_gateway` constrains generation to approved capabilities and applies PHI/egress controls.
- current text routing is provider/quota based (`Gemini -> Kimi -> fallback`), not task-cost based.
- the conversation path can resend ~3000 characters of recent history on every generative turn.
- the narrator asks for an extra `concern_detected` JSON field although the runtime only consumes `reply`.
- Gemini currently defaults to `gemini-2.5-flash`, while its implementation notes Flash-Lite has weaker JSON-schema reliability; reducing unnecessary JSON dependence may therefore enable cheaper narration.
- normal answers are prompt-limited to two sentences / 40 words, but provider API output is not yet hard-capped.
- Gemini `think()` exposes a 2048-token thinking budget and is unnecessary for routine bounded narration.

## Economic target

Benchmark target, not a production claim:

- median active patient AI-variable cost <= `$0.15/month`;
- normal active patient <= `$0.25/month`;
- heavy legitimate patient <= `$0.50/month`;
- median TTS API cost approximately zero;
- no routine frontier-model dependency.

Hosting, database, notifications and support are outside this AI-variable target.

## Pre-run gate

Required before the first paid/network call:

1. credentials available out of source control;
2. explicit network/API authorization;
3. explicit total spend ceiling;
4. exact current account-visible model/API identity confirmed for each candidate;
5. dry-run manifest validation passes without invoking providers.

## Accounting

This freeze does not close any #319 live benchmark outcome and does not change the MENA numerator.
