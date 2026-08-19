# P0-MENA-4 / #319 — Non-STT modality status — 2026-08-19

Status: **PROVISIONAL EVIDENCE MATRIX / NO PROVIDER CUTOVER**

STT corpus and STT provider comparison remain intentionally parked. This document covers the five active non-STT axes.

## 1. Native TTS real-device adequacy

Current recommendation: **native `flutter_tts` remains the cost-first default candidate, not yet an adequacy-approved winner**.

Reason: the client already has native TTS and therefore avoids routine cloud TTS cost, but FR/ar-MA intelligibility and preservation of clinically important numbers/units still require human listening on real devices.

C19 provides a fail-closed device-evidence contract requiring device/OS/engine/voice metadata, `human_checked=true`, `patient_data=false`, required locale coverage, and explicit intelligibility/critical-content outcomes.

Gate remaining: controlled real-device observations.

## 2. Paid/network text-provider benchmark

No provider is selected. No paid/network benchmark is authorized by this work.

C19 preflight blocks execution unless exact provider/model identity, explicit network authorization, positive spend ceiling, out-of-source-control credential reference, controlled pricing evidence, synthetic/minimized dataset identity, and `patient_data=false` are all present.

Gate remaining: explicit owner authorization + credentials + spend ceiling + current controlled prices.

## 3. OCR / vision real-camera and Arabic evidence

Evidence-backed state:
- mobile glucometer: existing ML Kit local-first path;
- PaddleOCR PP-OCRv6 small: C12 2/2 synthetic PASS plus C15 3/3 degraded synthetic PASS for Latin-script diabetes fixtures;
- PaddleOCR Arabic `arabic_PP-OCRv5_mobile_rec`: **rejected as primary** after C20/C21/C22 because proper RTL/Noto rendering lost safety-critical numeric content (`54`, `7.4`);
- Tesseract `ara` 5.3.4 C23: **6/6 synthetic PASS**, including 3/3 proper RTL/Noto Naskh and 6/6 exact critical numeric preservation (`54`, `68`, `7.4`);
- C24-W real-camera full-frame Arabic test: **rejected**; directly photographed Arabic-English speed sign failed exact numeric safety after two attempts (raw + EXIF-normalized). This rejects full-frame Tesseract as sufficient general camera OCR, not localized/bounded-field use;
- C27 Misraj exact numeric document benchmark: **rejected** on the pinned 10-page slice;
- C28 Tesseract automatic document-layout mode: **rejected** on the same pinned slice, exhausting the justified Tesseract full-document branch;
- C29 EasyOCR `ar+en`, CPU: **rejected 0/10** exact numeric-safe document cases on the same pinned Misraj slice.

Conclusion:
- **bounded/localized Arabic fields:** Tesseract `ara` remains the provisional local primary because C23 cleared the synthetic safety floor;
- **full-frame camera / full Arabic documents:** no local engine currently qualifies as primary from the measured evidence;
- **general Arabic document fallback:** requires a governed alternate OCR path until a candidate passes the same exact numeric floor on controlled real/document evidence;
- no runtime/provider cutover is authorized by these benchmarks.

Gate remaining for the local lane: controlled non-patient bounded-field real-camera Arabic fixtures. General document OCR is no longer blocked on more Tesseract/EasyOCR tuning; it is blocked on selecting and evidencing a different fallback candidate.

## 4. Evidence-backed primary/fallback recommendation

| Modality | Primary candidate | Fallback candidate | Decision state |
|---|---|---|---|
| Text | cheapest passing Tier-1 candidate | one evidence-approved stronger Tier-2 | **BLOCKED: paid/network benchmark not authorized** |
| TTS | native `flutter_tts` | cloud TTS only on measured native insufficiency | **BLOCKED: real-device listening evidence** |
| OCR glucometer mobile | ML Kit local | PaddleOCR/local or governed cloud only on measured insufficiency | **PROVISIONAL local-first** |
| OCR Latin-script documents | PaddleOCR PP-OCRv6 small | dedicated cloud OCR, then VLM only if needed | **PROVISIONAL: synthetic evidence only** |
| OCR Arabic bounded fields | **Tesseract `ara`** | governed alternate OCR only if real-camera bounded-field evidence shows need | **PROVISIONAL: C23 synthetic 6/6; real-camera bounded-field evidence missing** |
| OCR Arabic full documents | none local | **governed fallback required** | **LOCAL PRIMARY REJECTED: C24-W/C27/C28/C29 negative** |
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

No patient data. No paid/network provider call. No production provider cutover. No clinical approval. No CNDP/legal/data-residency authorization. No Vercel production deployment. C20–C23 are synthetic engineering evidence; C24-W is controlled external real-camera evidence; C26–C29 use pinned external document evidence and do not establish strict camera provenance. MENA roadmap numerator unchanged by this supporting hardening unless a retained roadmap outcome is separately closed with evidence.
