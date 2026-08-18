# P0-MENA-4 / #319 — Low-cost benchmark freeze — 2026-08-18

Status: **PRE-RUN FREEZE / NO PAID OR NETWORK BENCHMARK EXECUTED**

Base SHA: `55cc5957c109f98cb217a942619087d8833a2745`

## Goal

Select the cheapest architecture that is sufficiently safe and accurate for IAMINA's bounded companion role. Do not optimize for frontier-model prestige. Clinical/safety decisions remain deterministic; cloud models are narration, transcription, perception or fallback components only.

## Cost-first architecture hypothesis

1. **Text bot:** small low-cost model, not frontier by default.
2. **STT:** specialized transcription model.
3. **TTS:** native iOS/Android system voice by default, cloud fallback only if language/voice quality is insufficient.
4. **OCR:** local PaddleOCR first; cloud OCR only on low-confidence or unsupported cases.
5. **Meal/photo understanding:** small multimodal model only when local OCR/rules cannot answer the task.

## Frozen mini-benchmarks

### A. Text bot

Primary candidate:
- Google Gemini API — `gemini-2.5-flash-lite`
  - current official standard pricing: $0.10 / 1M input tokens, $0.40 / 1M output tokens;
  - text/image/video input supported.

Comparator:
- OpenAI API — `gpt-5-mini`
  - current official standard pricing: $0.25 / 1M input tokens, $2.00 / 1M output tokens;
  - structured outputs and function calling supported.

Optional ultra-cheap control only if the rubric can be satisfied:
- OpenAI API — `gpt-5-nano`
  - current official standard pricing: $0.05 / 1M input tokens, $0.40 / 1M output tokens;
  - intended for cheap classification/summarization-type workloads, not assumed sufficient for the conversational lane until tested.

Frontier models are excluded from the default benchmark unless every low-cost candidate fails a hard requirement.

### B. STT

Primary low-cost candidate:
- Mistral — Voxtral Mini Transcribe 2, exact account-visible model ID confirmed immediately before execution.

Comparator:
- OpenAI — `gpt-4o-mini-transcribe`.

`gpt-4o-transcribe` is retained only as a higher-cost quality control if both cheaper candidates fail the hard floor.

### C. OCR

Primary:
- local PaddleOCR PP-OCRv6, starting with tiny/small and escalating to medium only if needed.
- PP-OCRv6 is explicitly optimized for digital displays and has tiny/small/medium tiers, making it suitable for glucometer/display OCR without per-call cloud cost.

Fallback comparator:
- Mistral OCR 4, exact account-visible model ID confirmed immediately before execution.

General-purpose frontier VLM OCR is excluded unless PaddleOCR + dedicated OCR fail the required cases.

### D. TTS

Primary:
- native operating-system TTS on iOS/Android. API cost target: approximately zero to IAMINA.

Cloud TTS is tested only if native French/Arabic/Darija user experience is demonstrably inadequate. No cloud TTS provider is preselected before that failure is observed.

### E. Meal/photo understanding

Primary cloud candidate only where needed:
- `gemini-2.5-flash-lite` using image input.

The model must express uncertainty and must not claim exact carbohydrate values from an ambiguous meal image. Deterministic safety rules remain authoritative.

## Benchmark decision order

For every lane:

1. hard safety/privacy floor;
2. minimum task accuracy / intelligibility;
3. French + Arabic + Darija / mixed-language adequacy where relevant;
4. latency and availability;
5. cost.

A candidate that fails a hard safety or task floor is rejected regardless of price. Among candidates that pass, the cheapest adequate option wins.

## Execution constraints

- Synthetic/minimized repository fixtures only.
- No patient data.
- No credential committed to Git.
- Exact provider/model/API/region identity captured in each run record.
- Missing credential, model identity, budget authorization or execution authorization is STOP.
- Benchmark success does not authorize production or real-patient cutover.
- Paid/network calls remain prohibited until explicit budget authorization is recorded.

## Current source facts used for this freeze

Verified on 2026-08-18 against primary/official sources:

- Google Gemini 2.5 Flash-Lite is described as the smallest/cost-effective at-scale Gemini 2.5 model and is priced at $0.10/M input and $0.40/M output tokens on the paid standard tier.
- OpenAI `gpt-5-mini` is priced at $0.25/M input and $2/M output tokens; `gpt-5-nano` at $0.05/M input and $0.40/M output tokens.
- OpenAI `gpt-4o-mini-transcribe` is the cheaper GPT-4o transcription variant and is documented as improving language recognition/word error rate versus original Whisper models.
- PaddleOCR PP-OCRv6 exposes tiny/small/medium tiers from roughly 1.5M to 34.5M parameters and explicitly reports improved digital-display recognition.

Provider prices and model catalogs are mutable and must be rechecked immediately before any live cost calculation.

## Pre-run gate

Required before the first paid/network call:

1. credentials available out of source control;
2. explicit network/API authorization;
3. explicit total spend ceiling;
4. exact account/project model IDs confirmed;
5. dry-run manifest validation passes without invoking providers.

## Success criterion

#319 is not a contest for the most capable model. Success is an evidence-backed stack that satisfies the hard safety/quality floor and minimizes sustainable cost per active user.

## Accounting

This freeze does not close any #319 live benchmark outcome and does not change the MENA numerator.
