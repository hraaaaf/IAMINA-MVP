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
- Tesseract: narrow digit baseline only because the lab case misread `HbA1c` as `HbAlc`;
- Arabic PaddleOCR candidate `arabic_PP-OCRv5_mobile_rec`: **rejected as primary candidate** after C20/C21/C22 engineering evidence.

Arabic rejection evidence:
- C20 single recognizer: 1/3 synthetic PASS; lost `54`, and `7.4` degraded to `7` on proper RTL/Noto rendering;
- C21 dual-pass Arabic + generic numeric recognizer: 1/3 PASS; generic numeric pass failed to detect `54` and `68` reliably on Arabic lines;
- C22 typography robustness matrix: 4/6 overall, but the safety floor failed because proper RTL/Noto Naskh still lost `54` and converted `7.4` to `7` while generic DejaVu happened to pass 3/3.

Conclusion: typography-sensitive loss of safety-critical numeric values is unacceptable. **Do not promote PaddleOCR Arabic as IAMINA's primary Arabic OCR path.** This is a negative engineering result, not a production/runtime cutover.

Current recommendation:
- Latin-script glucometer/document OCR: local-first remains justified provisionally by C12/C15 synthetic evidence;
- Arabic OCR: primary remains **unselected**; next comparison must use a different local candidate or a governed fallback, measured first on controlled non-patient fixtures;
- no real-camera adequacy claim is allowed yet.

C19 provides an integrity/provenance manifest for controlled image fixtures with SHA-256, duplicate-content rejection, repository-relative paths, source type (`real_camera_test` or `synthetic_render`), locale/reference text/capture metadata and mandatory `patient_data=false`.

Gate remaining: controlled non-patient real-camera Arabic fixtures plus a different Arabic OCR candidate/fallback before any adequacy claim.

## 4. Evidence-backed primary/fallback recommendation

Current matrix:

| Modality | Primary candidate | Fallback candidate | Decision state |
|---|---|---|---|
| Text | cheapest passing Tier-1 candidate | one evidence-approved stronger Tier-2 | **BLOCKED: paid/network benchmark not authorized** |
| TTS | native `flutter_tts` | cloud TTS only on measured native insufficiency | **BLOCKED: real-device listening evidence** |
| OCR glucometer mobile | ML Kit local | PaddleOCR/local or governed cloud only on measured insufficiency | **PROVISIONAL local-first** |
| OCR Latin-script documents | PaddleOCR PP-OCRv6 small | dedicated cloud OCR, then VLM only if needed | **PROVISIONAL: synthetic evidence only** |
| OCR Arabic documents | **UNSELECTED** | governed alternate local/cloud OCR after measured comparison | **PaddleOCR Arabic REJECTED as primary; real-camera evidence still missing** |
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

No patient data. No paid/network provider call. No production provider cutover. No clinical approval. No CNDP/legal/data-residency authorization. No Vercel production deployment. C20/C21/C22 are synthetic engineering evidence only. MENA roadmap numerator unchanged by this supporting hardening unless a retained roadmap outcome is separately closed with evidence.
