# P0-MENA-4 / #319 — Non-STT modality status — 2026-08-19

Status: **PROVISIONAL EVIDENCE MATRIX / NO PROVIDER CUTOVER**

STT corpus and STT provider comparison are intentionally parked for later. This document covers the five remaining axes only.

## 1. Native TTS real-device adequacy

Current recommendation: **native `flutter_tts` remains the cost-first default candidate, not yet an adequacy-approved winner**.

Reason: the client already has native TTS and therefore avoids routine cloud TTS cost, but FR/ar-MA intelligibility and preservation of clinically important numbers/units still require human listening on real devices.

C19 adds a fail-closed device-evidence contract requiring device/OS/engine/voice metadata, `human_checked=true`, `patient_data=false`, required locale coverage, and explicit intelligibility/critical-content outcomes. Failures remain visible rather than being converted into a passing record.

Gate remaining: controlled real-device observations.

## 2. Paid/network text-provider benchmark

No provider is selected. No paid/network benchmark is authorized by this lot.

C19 adds a preflight contract that blocks execution unless all of the following exist simultaneously:
- exact provider and model identity;
- explicit network/API authorization;
- positive explicit spend ceiling;
- out-of-source-control credential reference (`env:VARIABLE`, never a value);
- controlled pricing evidence reference;
- synthetic/minimized dataset identity;
- `patient_data=false`.

Gate remaining: explicit owner authorization + credentials + spend ceiling + current controlled prices.

## 3. OCR / vision real-camera and Arabic evidence

Evidence-backed state:
- mobile glucometer: existing ML Kit local-first path;
- PaddleOCR PP-OCRv6 small: C12 2/2 synthetic PASS plus C15 3/3 degraded synthetic PASS for Latin-script diabetes fixtures;
- Tesseract narrow Latin-script baseline: the earlier lab case misread `HbA1c` as `HbAlc`;
- Arabic PaddleOCR candidate `arabic_PP-OCRv5_mobile_rec`: **rejected as primary candidate** after C20/C21/C22 engineering evidence;
- Tesseract `ara` 5.3.4: **C23 6/6 synthetic PASS with 6/6 exact critical numeric preservation**, including all 3 proper RTL/Noto Naskh cases.

Arabic PaddleOCR rejection evidence:
- C20 single recognizer: 1/3 synthetic PASS; lost `54`, and `7.4` degraded to `7` on proper RTL/Noto rendering;
- C21 dual-pass Arabic + generic numeric recognizer: 1/3 PASS; generic numeric pass failed to detect `54` and `68` reliably on Arabic lines;
- C22 typography robustness matrix: 4/6 overall, but the safety floor failed because proper RTL/Noto Naskh still lost `54` and converted `7.4` to `7` while generic DejaVu happened to pass 3/3.

C23 Tesseract Arabic evidence:
- same 6-case synthetic matrix as C22: 6/6 PASS;
- numeric safety floor: 6/6 exact (`54`, `68`, `7.4` preserved across both typography profiles);
- proper RTL/Noto Naskh subset: 3/3 PASS;
- synthetic fixtures only; no patient data, provider API, paid inference, or real-camera evidence.

Conclusion: typography-sensitive loss of safety-critical numeric values makes PaddleOCR Arabic unsuitable as the primary candidate. **Tesseract `ara` is now the preferred local Arabic OCR candidate for the next validation stage, not a production-approved winner.**

Current recommendation:
- Latin-script glucometer/document OCR: local-first remains justified provisionally by C12/C15 synthetic evidence;
- Arabic OCR: **Tesseract `ara` becomes the provisional primary candidate** because it cleared C23's synthetic numeric safety floor; PaddleOCR Arabic remains rejected as primary;
- no real-camera adequacy claim is allowed yet, and no runtime/provider cutover is authorized by this evidence.

C19 provides an integrity/provenance manifest for controlled image fixtures with SHA-256, duplicate-content rejection, repository-relative paths, source type (`real_camera_test` or `synthetic_render`), locale/reference text/capture metadata and mandatory `patient_data=false`.

Gate remaining: controlled non-patient real-camera Arabic fixtures measured with Tesseract `ara`, then comparison against a governed fallback only if the measured failure rate requires one.

## 4. Evidence-backed primary/fallback recommendation

Current matrix:

| Modality | Primary candidate | Fallback candidate | Decision state |
|---|---|---|---|
| Text | cheapest passing Tier-1 candidate | one evidence-approved stronger Tier-2 | **BLOCKED: paid/network benchmark not authorized** |
| TTS | native `flutter_tts` | cloud TTS only on measured native insufficiency | **BLOCKED: real-device listening evidence** |
| OCR glucometer mobile | ML Kit local | PaddleOCR/local or governed cloud only on measured insufficiency | **PROVISIONAL local-first** |
| OCR Latin-script documents | PaddleOCR PP-OCRv6 small | dedicated cloud OCR, then VLM only if needed | **PROVISIONAL: synthetic evidence only** |
| OCR Arabic documents | **Tesseract `ara`** | governed alternate local/cloud OCR only if real-camera evidence shows need | **PROVISIONAL: C23 synthetic 6/6 + numeric 6/6; real-camera evidence missing** |
| Vision meal/photo | provider-neutral explicit-intent vision path | no frontier default | **NO winner selected** |
| STT | parked | parked | **DEFERRED by owner** |

This matrix is not a production provider selection and does not authorize patient-data egress.

## 5. Synthetic fail-closed rollout smoke

C19 merged contract-level smoke coverage spanning:
- stale controlled pricing blocks before a synthetic provider invocation;
- mixed text + vision reservations cannot cross the configured monthly budget silently;
- failed authorization does not mutate committed spend;
- `stream()` and `think()` remain blocked before inner-provider invocation.

This smoke validates composition of the existing fail-closed contracts. It is **not** evidence of production provider wiring or production readiness.

## Non-claims

No patient data. No paid/network provider call. No production provider cutover. No clinical approval. No CNDP/legal/data-residency authorization. No Vercel production deployment. C20/C21/C22/C23 are synthetic engineering evidence only. MENA roadmap numerator unchanged by this supporting hardening unless a retained roadmap outcome is separately closed with evidence.
