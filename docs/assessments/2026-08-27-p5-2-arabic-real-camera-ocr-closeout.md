# P5-2 — Arabic OCR real-camera evidence closeout

Date: 2026-08-27

## Goal

Obtain controlled real-world Arabic OCR evidence for IAMINA without weakening the exact numeric safety floor or promoting an unqualified local full-document engine.

## Frozen evidence contract

- source: public non-patient AraReceipt real receipt photographs;
- dataset revision: `d995859bd253ad37053faee8bce24b5fa1c265e2`;
- deterministic selection: first 6 eligible Arabic-text annotations and first 6 eligible numeric annotations in dataset/annotation order;
- OCR: Tesseract `ara`, `--psm 7`;
- PASS required **6/6 Arabic normalized exact** and **6/6 numeric-token sequence exact**;
- no post-result case selection or threshold change.

## Observed result

Run: `33116085468`

Artifact: `9664573464`

Artifact digest: `sha256:18034bd1e0b296fc4671a5dc5b9c62177a82c8cac72dee6926c822d9ca1c1be2`

Result:

- Arabic normalized exact: **2/6**;
- numeric sequence exact: **2/6**;
- verdict: **FAIL**.

The exact numeric floor therefore does not qualify Tesseract `ara` for this retained real-camera bounded lane.

## Full-document consequence

No local Arabic full-document primary is qualified from retained measured evidence:

- full-frame Tesseract: rejected;
- C27/C28 Tesseract full-document strategies: rejected;
- EasyOCR `ar+en`: **0/10**;
- Surya2 local CPU: **7/10**;
- PaddleOCR-VL 1.6: **1/10**.

The governed state remains **UNQUALIFIED** rather than inventing a winner.

## Success / proof decision

P5-2 was an evidence-acquisition gate, not a mandate to force a positive OCR result. Its retained success criteria are satisfied because:

- the real-camera source is non-patient and revision-pinned;
- bounded Tesseract received an explicit PASS/FAIL verdict;
- the 100% numeric hard floor was preserved;
- the full-document local route has an evidence-backed `UNQUALIFIED` decision;
- exact run/artifact/SHA evidence is retained;
- no patient-data, provider/runtime cutover, CNDP/legal or clinical approval is implied.

Issue #517 is therefore closed as **completed evidence acquisition with a negative product qualification result**. Any future Arabic OCR improvement is a new remediation/qualification task.
