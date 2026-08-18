# P0-MENA-4 / #319 — Benchmark candidate freeze — 2026-08-18

Status: **COST-FIRST PRE-RUN FREEZE / LOCAL EVIDENCE ACTIVE / NO PAID OR NETWORK PROVIDER BENCHMARK EXECUTED**

Initial freeze base SHA: `55cc5957c109f98cb217a942619087d8833a2745`
Evidence sync verified through main: `dd3481fea54585da221cbf2a9cfe05ed8711a857`

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

The runtime STT path is now provider-neutral behind an injectable boundary; Gemini remains the current default until benchmark evidence authorizes a later cutover.

### OCR / vision

1. mobile glucometer OCR: existing on-device ML Kit path remains primary;
2. local PaddleOCR PP-OCRv6 small: measured synthetic candidate, 2/2 prior exact-head cases passed;
3. Tesseract: retained only as a narrow digit/glucometer baseline, not lab-document OCR authority;
4. expand local camera/display/document fixtures before cloud fallback;
5. dedicated Mistral OCR 4 / Qwen small VLM / Gemini Flash-Lite only where local evidence is insufficient;
6. general-purpose frontier VLM excluded unless cheaper paths fail.

Cloud meal/glucometer vision is now provider-neutral behind an injectable boundary; Gemini remains the current default. Existing deterministic media validation is enforced before provider invocation.

### TTS

1. native iOS/Android `flutter_tts` path already exists and remains the default;
2. cloud TTS only if measured FR/AR/Darija intelligibility fails the UX floor.

Fixed/help/safety phrases should be locally reusable rather than regenerated.

## Verified local OCR evidence

### C10 Tesseract

- synthetic glucometer `54 mg/dL`: PASS;
- synthetic lab case: `HbA1c` was misread as `HbAlc`;
- conclusion: Tesseract is not promoted to lab-document OCR authority.

### C12 PaddleOCR PP-OCRv6 small

Prior exact-head evidence on `5a36b281437e84d5726c040eea831a8b12522e5c`:

- PaddleOCR `3.7.0`;
- PaddlePaddle `3.2.2`;
- `PP-OCRv6_small_det` + `PP-OCRv6_small_rec`;
- CPU local inference;
- patient data: false;
- provider API: false;
- paid inference: false;
- setup latency: `57282.16 ms`;
- 2/2 gating cases PASS;
- `54 mg/dL`: `582.93 ms`, mean recognition confidence `0.99978`;
- `HbA1c 7.4 % / Glycemie a jeun 1.32 g/L`: `509.38 ms`, mean recognition confidence `0.998261`.

Artifact digest: `sha256:9f789af8683932140780a9e9428b6fbddc0c67859422ad882933c7afd3b8eaf1`.

This is synthetic-fixture evidence only. Real camera conditions, Arabic OCR and production suitability remain unproven.

## Cost-reduction work to benchmark

- deterministic zero-model routing before any LLM;
- reduce raw history payload to compact governed state + last 1-2 turns;
- stable cacheable system prefix;
- remove unused structured-output fields where safe;
- keep provider API output ceilings enforced and evaluate narrower task-specific ceilings rather than assuming one global limit;
- prohibit routine reasoning/`think()`;
- at most one paid quality escalation per turn;
- STT silence trimming / compact encoding / duplicate-audio reuse;
- local OCR crop/preprocess first, cloud only for uncertain regions;
- no automatic vision analysis without explicit user intent;
- native TTS by default;
- per-patient cost ledger and circuit breakers.

## Verified code observations motivating the plan

- urgent/insulin/prescription safety is evaluated before the conversational LLM path;
- `core.llm_gateway` constrains generation to approved capabilities and applies PHI/egress controls;
- the conversational text path is still provider/quota-oriented rather than fully task/cost-routed;
- DeepSeek and Qwen have governed OpenAI-compatible adapters;
- STT and cloud vision now expose provider-neutral injectable boundaries while defaults remain unchanged;
- current Gemini, Kimi and governed OpenAI-compatible low-cost adapters enforce a `160` output-token ceiling at the provider API layer;
- the prompt-level two-sentence / 40-word target remains stricter than that global ceiling, but lowering the provider ceiling globally could truncate structured summary use cases and therefore needs task-specific evidence;
- Gemini `think()` exposes a 2048-token thinking budget and is unnecessary for routine bounded narration;
- native `flutter_tts` already exists client-side;
- meal-photo capture already resizes to max width 1600 and image quality 85 before upload;
- C13 extends the controlled pricing/budget contract beyond text tokens to metered units such as STT seconds, OCR pages, images and TTS characters, without embedding provider prices.

## Economic target

Benchmark target, not a production claim:

- median active patient AI-variable cost <= `$0.15/month`;
- normal active patient <= `$0.25/month`;
- heavy legitimate patient <= `$0.50/month`;
- median TTS API cost approximately zero;
- no routine frontier-model dependency.

Hosting, database, notifications and support are outside this AI-variable target.

## Execution constraints

- Synthetic/minimized repository fixtures only.
- No patient data.
- No credential committed to Git.
- Exact provider/model/API identity must be captured in each run record.
- Missing credential, model identity, budget authorization or execution authorization is STOP.
- Benchmark success does not authorize production or real-patient cutover.

## Pre-run gate for paid/network providers

Required before the first paid/network provider call:

1. credentials available out of source control;
2. explicit network/API authorization;
3. explicit total spend ceiling;
4. exact current account-visible model/API identity confirmed for each candidate;
5. current controlled pricing record for the charged modality;
6. dry-run manifest validation passes without invoking providers.

## Accounting

Local/synthetic measurements such as C10/C12 are evidence, but they do not by themselves close the remaining external/live provider outcomes in #319 and do not change the MENA numerator. Benchmark success does not imply provider cutover, patient-data release, clinical approval or CNDP/legal authorization.
