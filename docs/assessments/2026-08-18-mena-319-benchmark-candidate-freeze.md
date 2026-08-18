# P0-MENA-4 / #319 — Benchmark candidate freeze — 2026-08-18

Status: **COST-FIRST / LOCAL EVIDENCE + BUDGET GUARDS MERGED / NO PAID OR NETWORK PROVIDER BENCHMARK EXECUTED**

Evidence synchronized through main `9088d190cb0d087718eeeaef6c9fcab20b3a3e9e`.

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
- Gemini Flash-Lite
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

The STT runtime boundary is provider-neutral. PR #375 rejects transcript-only placeholder evidence. C18 #388 additionally requires integrity-pinned corpus fixtures before measurement.

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

### C12 PaddleOCR
Merged #371 (`6f85271aba82684cc0a40890a06a15414ab75146`). Benchmark head `6b0a27bef10352d72f2b416d3d66edbd953f1746`:
- 2/2 synthetic gating cases PASS;
- `54 mg/dL`: `358.73 ms`, confidence `0.99978`;
- lab HbA1c/glucose: `304.42 ms`, confidence `0.998261`.

### C15 PaddleOCR hardening
Merged #384 (`11bc53701126a0c9b8204ee203f3f7798565fa96`). Preserved measured evidence:
- rotated `54 mg/dL`: PASS, `399.71 ms`;
- low-contrast `68 mg/dL`: PASS, `251.36 ms`;
- blur/JPEG lab: PASS, `298.61 ms`;
- mean confidence approximately `0.952–0.998`.

All OCR measurements above are local synthetic evidence only: no patient data, provider API or paid inference. They do not establish real-camera or Arabic OCR adequacy.

## Cost-control state
- bounded zero-model routing exists;
- DeepSeek/Qwen governed low-cost adapters exist;
- Gemini/Kimi/compatible adapters enforce 160 provider-side output tokens;
- STT and cloud vision are provider-neutral boundaries;
- native TTS exists client-side;
- controlled expiring pricing covers text and generic metered media;
- no real provider price is embedded in source;
- C16 #387 (`50d27b9113849f8f765e723365e143f8facffda5`) certifies synthetic mixed text/STT/vision budget caps, fail-closed over-budget behavior, settlement release and subject/month isolation.

C16 is a controller-contract proof under synthetic pricing, not proof of persistent production accounting or real provider spend.

## STT evidence gate
C18 #388 merged as `9088d190cb0d087718eeeaef6c9fcab20b3a3e9e`.

Measured STT fixtures must now be repository-relative, SHA-256 pinned, unique-content, explicitly typed, non-patient, metadata-complete and include critical tokens/concepts. Human test speakers additionally require recorded consent.

There is currently no real audio corpus and no embedded local STT engine. Therefore a real STT score remains blocked until a controlled corpus exists.

Initial corpus protocol: at least 12 integrity-pinned human clips spanning FR, MSA Arabic, Darija and mixed-language speech, including clinically important numbers/concepts. Synthetic TTS audio may be used only as separately labelled engineering stress evidence.

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

## Remaining benchmark outcomes
1. populate real text provider matrix;
2. populate real STT results after corpus readiness;
3. extend OCR/vision evidence to real-camera/Arabic where required;
4. validate native-device TTS adequacy;
5. produce evidence-backed primary/fallback recommendation per modality with contractual notes;
6. complete synthetic fail-closed rollout smoke coverage where still missing.

## Accounting / non-claims
These local/cost-control merges do not change the canonical MENA numerator by themselves. Benchmark success does not imply provider cutover, patient-data release, clinical approval or CNDP/legal/data-residency authorization.