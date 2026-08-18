# IAMINA AI Cost Optimization Plan

Status: **ARCHITECTURE + VERIFIED LOCAL/COST-CONTROL EVIDENCE / NO PROVIDER CUTOVER**

Evidence synchronized through main `9088d190cb0d087718eeeaef6c9fcab20b3a3e9e`.

## Goal
Preserve IAMINA's deterministic clinical intelligence and safety while minimizing variable AI cost per active patient.

## Acceptance rule
A cost optimization is accepted only if it preserves the governed safety/quality floor and lowers or bounds cost. Primary KPI: **cost per accepted safe answer**.

## Verified architecture
- clinical urgency / insulin / prescription boundaries remain deterministic and precede generation;
- governed clinical context is computed outside the model;
- zero-model routing exists for bounded non-clinical turns;
- DeepSeek/Qwen governed low-cost adapters exist;
- STT and cloud vision are provider-neutral boundaries while current defaults remain unchanged;
- `flutter_tts` provides native client TTS;
- mobile glucometer OCR is local-first with ML Kit;
- Gemini, Kimi and governed OpenAI-compatible text adapters enforce a provider-side `160` output-token ceiling;
- controlled, expiring pricing and budget authorization cover text and generic metered media units;
- common LLM pipeline `stream()` / `think()` bypasses are fail-closed until governed egress authorization covers them;
- CI duplicate branch/PR validation was removed via #379, preserving PR gates while reducing runner waste.

## Verified OCR evidence
### Tesseract C10
- `54 mg/dL`: PASS;
- lab case: `HbA1c` misread as `HbAlc`;
- retained only as a narrow digit/glucometer baseline.

### PaddleOCR C12
Merged via #371 (`6f85271aba82684cc0a40890a06a15414ab75146`). Exact benchmark head `6b0a27bef10352d72f2b416d3d66edbd953f1746`:
- PaddleOCR `3.7.0`, PaddlePaddle `3.2.2`;
- `PP-OCRv6_small_det` + `PP-OCRv6_small_rec`;
- CPU local inference;
- 2/2 synthetic cases PASS;
- `54 mg/dL`: `358.73 ms`, mean recognition confidence `0.99978`;
- HbA1c/glucose lab case: `304.42 ms`, mean recognition confidence `0.998261`;
- no patient data, provider API or paid inference.

### PaddleOCR C15 hardening
Merged via #384 (`11bc53701126a0c9b8204ee203f3f7798565fa96`). Preserved exact-head evidence from `2e10cd4907620bef951949167f2fd2dc522e8e7e`:
- rotated glucometer `54 mg/dL`: PASS, `399.71 ms`;
- low-contrast glucometer `68 mg/dL`: PASS, `251.36 ms`;
- blur/JPEG lab `HbA1c 7.4 % / 1.32 g/L`: PASS, `298.61 ms`;
- mean recognition confidence range approximately `0.952–0.998`;
- local CPU, synthetic fixtures, no patient data or paid/provider inference.

These OCR results are synthetic-fixture evidence only. Real camera conditions, Arabic OCR and production suitability remain unproven.

## Text strategy
Target path:
1. deterministic safety + zero-model resolver;
2. cheapest adequate Tier-1 narrator;
3. deterministic output validation;
4. at most one evidence-approved stronger fallback;
5. governed static/offline fallback.

Routine frontier-model dependency is excluded.

Tier-1 candidates: DeepSeek V4 Flash, Gemini Flash-Lite, Qwen low-cost candidate, Kimi low-cost candidate, GPT-5 nano control. Tier-2: GPT-5 mini or evidence-backed stronger fallback.

Remaining text optimization: compact governed history, cache-stable prefixes and task-specific ceilings. No routine `think()`.

## STT
Provider boundary is decoupled. PR #375 prevents transcript-only evidence from being scored as real STT.

C18 merged via #388 (`9088d190cb0d087718eeeaef6c9fcab20b3a3e9e`) and adds repository-side corpus validation requiring:
- repository-relative audio fixture;
- matching lowercase SHA-256;
- unique audio content;
- explicit `source_type`;
- `consent_recorded=true` for human test speakers;
- `patient_data=false`;
- locale/reference/capture metadata;
- encoding, sample rate, channels and duration;
- critical tokens and/or required concepts.

There is still **no real audio corpus and no embedded local STT engine**. The next valid STT measurement requires at least 12 integrity-pinned human clips spanning FR, MSA Arabic, Darija and mixed speech, including clinically important numbers/concepts. Synthetic TTS may remain separately labelled engineering evidence only.

Cloud candidates after corpus readiness: Voxtral Mini Transcribe 2, GPT-4o-mini-transcribe, xAI/Grok STT if controlled pricing remains competitive; on-device STT remains a challenger.

## TTS
Native `flutter_tts` remains default. Cloud TTS is exceptional and requires real-device intelligibility evidence. Target median TTS API cost remains approximately zero, not a production measurement.

## OCR / vision routing
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

C16 merged via #387 (`50d27b9113849f8f765e723365e143f8facffda5`) and certifies with synthetic mixed-modality load that:
- text + STT + vision reservations cannot silently exceed the monthly cap;
- rejected over-budget reservations do not mutate committed spend;
- settlement releases unused reserved capacity;
- ledgers isolate subject/month accounting.

This proves the controller contract under synthetic pricing. It does **not** prove persistent production accounting or real provider spend.

No real provider price is hard-coded. Missing, ambiguous or stale pricing must fail closed.

## Economic target
Engineering targets, not production claims:
- median active patient AI-variable cost <= `$0.15/month`;
- normal active patient <= `$0.25/month`;
- heavy legitimate patient <= `$0.50/month`;
- no routine cloud TTS;
- no routine frontier-model dependency.

## Remaining critical path
1. collect and validate >=12 controlled human STT clips;
2. benchmark local STT and then cloud STT candidates;
3. validate native TTS on real devices;
4. paid/network text-provider benchmark only after explicit authorization, credentials and spend ceiling;
5. evidence-backed capability + cost routing decision;
6. persistent production budget/usage certification before any patient-data release.

## Non-claims
This plan does not claim production provider selection, production cost, real-world OCR/STT accuracy, clinical approval, CNDP/legal/data-residency authorization, patient-data release or production readiness.