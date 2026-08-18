# P0-MENA-4 / #319 — Benchmark candidate freeze — 2026-08-18

Status: **COST-FIRST / LOCAL EVIDENCE ACTIVE / NO PAID OR NETWORK PROVIDER BENCHMARK EXECUTED**

Evidence synchronized through main `92fb8a2052873d9d3b633ba6f08ea4fc73d4dd72`.

Canonical optimization plan: `docs/architecture/IAMINA_AI_COST_OPTIMIZATION_PLAN.md`

## Goal
Benchmark the least expensive architecture that preserves IAMINA's deterministic clinical authority, safety boundaries and acceptable FR/AR/Darija experience.

Decision order:
1. hard safety/privacy floor;
2. sufficient task quality;
3. FR/AR/Darija/mixed-language adequacy;
4. latency/availability;
5. total variable cost.

Among passing candidates, the cheapest adequate candidate wins.

## Candidate freeze
### Text Tier 1
- DeepSeek V4 Flash
- Gemini 2.5 Flash-Lite
- Qwen low-cost candidate, exact model/region frozen before run
- Kimi low-cost candidate, exact model/API frozen before run
- GPT-5 nano control

### Text Tier 2
- GPT-5 mini or evidence-backed stronger fallback

No frontier model is a routine candidate.

### STT
- Voxtral Mini Transcribe 2
- GPT-4o-mini-transcribe
- xAI/Grok STT if current controlled pricing/API remains competitive
- on-device challenger if measurable FR/AR/Darija quality is adequate

The STT runtime boundary is provider-neutral. PR #375 now prevents transcript-only or placeholder evidence from being scored as real STT: every measured case must carry an integrity-pinned repository audio fixture.

### OCR / vision
- mobile glucometer: existing on-device ML Kit primary
- PaddleOCR PP-OCRv6 small: measured local synthetic candidate
- Tesseract: narrow digit/glucometer baseline only
- cloud OCR/VLM only where local evidence is insufficient
- cloud meal/glucometer vision remains provider-neutral; Gemini remains current default

### TTS
- native iOS/Android `flutter_tts` first
- cloud only if real-device FR/AR/Darija intelligibility fails the UX floor

## Verified local OCR evidence
### C10 Tesseract
`54 mg/dL` PASS; lab `HbA1c` misread as `HbAlc`. Not lab-document authority.

### C12 PaddleOCR exact-head
Merged PR #371, merge `6f85271aba82684cc0a40890a06a15414ab75146`.
Benchmark head `6b0a27bef10352d72f2b416d3d66edbd953f1746`:
- PaddleOCR `3.7.0`; PaddlePaddle `3.2.2`
- `PP-OCRv6_small_det` + `PP-OCRv6_small_rec`
- CPU local inference
- 2/2 synthetic gating cases PASS
- `54 mg/dL`: `358.73 ms`, confidence `0.99978`
- lab HbA1c/glucose case: `304.42 ms`, confidence `0.998261`
- no patient data, provider API or paid inference

Synthetic evidence does not establish real-camera or Arabic OCR adequacy.

## Cost-control state
- bounded zero-model routing exists;
- DeepSeek/Qwen governed low-cost adapters exist;
- Gemini/Kimi/compatible adapters enforce 160 provider-side output tokens;
- STT and cloud vision are provider-neutral boundaries;
- native TTS exists client-side;
- meal images are already resized/compressed before upload;
- controlled expiring pricing exists for text;
- generic metered pricing/budget reservation covers STT seconds, OCR pages, images and TTS characters;
- no real provider price is embedded in source.

## STT evidence gate
There is currently no real audio fixture corpus in the repository and no embedded local STT engine. Therefore a real STT score is blocked until a controlled corpus exists.

Initial corpus protocol requires at least 12 integrity-pinned clips spanning FR, MSA Arabic, Darija and mixed-language speech, with clinically important numbers/concepts. Synthetic TTS audio may be used only as a separately labelled engineering stress fixture, never as a substitute for human-speech adequacy evidence.

## Economic target
Engineering targets, not production claims:
- median active patient AI-variable cost <= `$0.15/month`
- normal active patient <= `$0.25/month`
- heavy legitimate patient <= `$0.50/month`
- median cloud TTS cost approximately zero
- no routine frontier dependency

## Paid/network pre-run gate
Required before any paid/network provider call:
1. credentials out of source control;
2. explicit network/API authorization;
3. explicit total spend ceiling;
4. exact provider/model/API identity;
5. current controlled pricing record for charged modality;
6. dry-run manifest validation.

## Accounting / non-claims
Local measurements do not close the remaining live provider outcomes by themselves and do not change the MENA numerator. Benchmark success does not imply provider cutover, patient-data release, clinical approval or CNDP/legal/data-residency authorization.