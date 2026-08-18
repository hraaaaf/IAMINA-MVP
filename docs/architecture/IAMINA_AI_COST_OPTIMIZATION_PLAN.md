# IAMINA AI Cost Optimization Plan

Status: **ARCHITECTURE + VERIFIED IMPLEMENTATION EVIDENCE / NO PROVIDER CUTOVER**

## Goal
Preserve IAMINA's deterministic clinical intelligence and safety while minimizing variable AI cost per active patient.

## Success
A cost optimization is accepted only when evidence preserves the governed safety/quality floor and lowers or bounds cost. Primary KPI: **cost per accepted safe answer**.

## Verified architecture
- clinical urgency / insulin / prescription boundaries remain deterministic and precede generation;
- governed clinical context is computed outside the model;
- zero-model routing exists for bounded non-clinical turns;
- DeepSeek/Qwen governed low-cost adapters exist;
- STT and cloud vision are provider-neutral boundaries while current defaults remain unchanged;
- `flutter_tts` provides native client TTS;
- mobile glucometer OCR is local-first with ML Kit;
- Gemini, Kimi and governed OpenAI-compatible text adapters enforce a provider-side `160` output-token ceiling;
- controlled, expiring pricing and budget authorization cover text and generic metered media units.

## Verified local OCR evidence
### Tesseract C10
- `54 mg/dL`: PASS;
- lab case: `HbA1c` misread as `HbAlc`;
- retained only as a narrow digit/glucometer baseline.

### PaddleOCR C12
Merged via PR #371 (`6f85271aba82684cc0a40890a06a15414ab75146`). Exact benchmark head `6b0a27bef10352d72f2b416d3d66edbd953f1746` passed:
- PaddleOCR `3.7.0`, PaddlePaddle `3.2.2`;
- `PP-OCRv6_small_det` + `PP-OCRv6_small_rec`;
- CPU local inference;
- 2/2 synthetic cases PASS;
- `54 mg/dL`: `358.73 ms`, mean recognition confidence `0.99978`;
- `HbA1c 7.4 % / Glycemie a jeun 1.32 g/L`: `304.42 ms`, mean recognition confidence `0.998261`;
- no patient data, provider API or paid inference.

This is synthetic-fixture evidence only. Real camera conditions, Arabic OCR and production suitability remain unproven.

## Target architecture
1. deterministic safety + zero-model resolver;
2. cheapest adequate Tier-1 narrator;
3. deterministic output validation;
4. at most one evidence-approved stronger fallback;
5. governed static/offline fallback.

Routine frontier-model dependency is excluded.

## Text
Candidates: DeepSeek V4 Flash, Gemini Flash-Lite, Qwen low-cost candidate, Kimi low-cost candidate, GPT-5 nano control; GPT-5 mini as quality fallback.

Remaining optimization: compact governed history, cache-stable prefixes, task-specific token ceilings, no routine `think()`.

## STT
Provider boundary is decoupled, but **no real local STT engine or audio corpus is currently embedded**. PR #375 (`92fb8a2052873d9d3b633ba6f08ea4fc73d4dd72`) now fails closed unless each measured STT case supplies:
- repository-relative audio fixture;
- allowed audio extension;
- lowercase SHA-256 matching the file.

The next valid STT measurement therefore requires a controlled audio corpus. Initial protocol target: at least 12 integrity-pinned clips spanning FR, MSA Arabic, Darija and mixed speech, including clinically important numbers/concepts. Transcript-only cases are not measured STT evidence.

Cloud candidates after corpus readiness: Voxtral Mini Transcribe 2, GPT-4o-mini-transcribe, xAI/Grok STT if current controlled pricing remains competitive. On-device STT remains a challenger if measurable quality is adequate.

## TTS
Native `flutter_tts` remains default. Cloud TTS is exceptional and requires real-device intelligibility evidence. Target median TTS API cost remains approximately zero, not yet a production measurement.

## OCR / vision
- mobile glucometer: ML Kit primary;
- PaddleOCR: measured local synthetic candidate;
- Tesseract: narrow digit baseline only;
- cloud OCR/VLM only after measured local insufficiency;
- meal vision only on explicit intent; current capture already reduces payload to max width 1600 / JPEG quality 85;
- no exact carbohydrate claim unless supplied by a separate governed estimator.

## Pricing and budget
Delivered contracts:
- controlled expiring text price registry;
- text budget reservation;
- exact-rational `MeteredPrice` for seconds/pages/images/characters;
- metered budget reservation under single-call and monthly caps.

No real provider price is hard-coded. Missing, ambiguous or stale pricing must fail closed.

## Economic target
Engineering targets, not production claims:
- median active patient AI-variable cost <= `$0.15/month`;
- normal active patient <= `$0.25/month`;
- heavy legitimate patient <= `$0.50/month`;
- no routine cloud TTS;
- no routine frontier-model dependency.

## Remaining critical path
1. broaden local OCR fixtures beyond easy synthetic cases;
2. create integrity-pinned STT corpus and run local/cloud STT comparisons;
3. native TTS real-device intelligibility gate;
4. paid/network text-provider benchmark only after explicit authorization, credentials and spend ceiling;
5. evidence-backed capability + cost routing decision;
6. production budget/usage certification before any patient-data release.

## Non-claims
This plan does not claim production provider selection, production cost, real-world OCR/STT accuracy, clinical approval, CNDP/legal/data-residency authorization, patient-data release or production readiness.