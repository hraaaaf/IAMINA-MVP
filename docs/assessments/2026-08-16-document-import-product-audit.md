# Document Import product audit — 2026-08-16

Status: SMART audit in progress; truthfulness correction applied; privacy-copy correction and exact-head certification pending.

## Product contract

Document Import is a two-step extraction workflow: select a supported medical document, inspect the extracted data, then explicitly confirm before anything is persisted. The preview must distinguish data that will actually be stored from information that was merely detected.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical page header bridge | Keeps the global IAmina header while preserving sensitive legacy workflow layout | 9.0/10 | KEEP — legacy AppBar is clipped by the bridge; no visible double-header |
| Intro / purpose | Explains the two-step review-before-save contract | 9.2/10 | KEEP |
| Supported-format chips | Sets upload expectations before file picker | 8.5/10 | IMPROVE — functionally useful; Arabic `Photo` remains untranslated in the chip surface |
| Privacy notice | Explains why AI processing may be blocked without consent/provider approval | 7.5/10 | IMPROVE — current copy says the document may be sent externally, while implementation extracts locally and authorizes pseudonymized text egress; wording is broader than actual behavior |
| Choose-document CTA | Clear primary action | 9.5/10 | KEEP |
| File type / size guard | Prevents unsupported or oversized payloads | 8.0/10 | KEEP backend 15 MB hard limit; client currently loads bytes before backend rejection, so UX can improve later without weakening server enforcement |
| Loading state | Separates analysis from saving | 9.0/10 | KEEP |
| Confidence / review banner | Surfaces extractor confidence and backend `needsReview` state | 9.0/10 | KEEP — `needsReview` is backend-defined for usable extraction below 0.7 confidence; confirmation remains a deliberate user decision |
| Extracted glucose | Core importable data preview | 9.5/10 | KEEP |
| Extracted lab values | Core importable report data preview | 9.5/10 | KEEP |
| Extracted medications | Useful recognition, but store layer does not persist medications | 5.5/10 baseline → 9.0/10 | IMPROVE — explicitly label “detected — not imported”; medications alone no longer enable confirmation |
| Clinical notes | Persisted into LabReport and useful for review | 9.0/10 | KEEP |
| Warnings / errors | Critical anti-hallucination and validation feedback | 9.5/10 | KEEP |
| Empty / non-importable state | Prevents confirmation when nothing persistable was extracted | 7.0/10 baseline → 9.5/10 | IMPROVE — `hasUsefulData` now matches actual persisted categories rather than treating medications as persistable |
| Confirm CTA | Explicit second step before DB write | 9.5/10 | KEEP — backend confirmation consumes staged batch once and persists only after this action |
| Cancel CTA | Safe exit before persistence | 9.5/10 | KEEP |
| Completion state | Confirms success/failure and glucose import count | 8.5/10 | IMPROVE later — lab-report persistence is not surfaced explicitly in the success summary |
| Back to Dashboard | Valid exit after import | 8.5/10 | KEEP for now; Journal may be a stronger contextual destination after visual audit |
| Import another document | Supports batch workflow without forcing navigation | 9.0/10 | KEEP |

## Verified backend contract

- `/api/v1/documents/ingest?confirm=false` stages extraction in Django cache and does not persist patient data.
- `/api/v1/documents/confirm/{batch_id}` consumes the staged batch once before persistence.
- Backend rejects empty files and files over 15 MB.
- Spreadsheet extraction is deterministic and bypasses the LLM; PDF/DOCX/image content is extracted locally and parsed from pseudonymized text when AI parsing is needed.
- Real text egress requires explicit global AI consent and an authorized provider policy.
- `needs_review` is true when extraction is usable and confidence is below 0.7.
- Store persistence creates a `LabReport` containing lab values, clinical notes and raw audit text, plus imported glucose `LogEntry` rows.
- The store does **not** persist `MedicationEntry` objects.

## Verified findings

- Frontend and backend confirmation routes match exactly: `/api/v1/documents/confirm/{batchId}`.
- The previous frontend `hasUsefulData` included `medications.isNotEmpty`, so a medication-only extraction could enable “Confirm import” even though no medication record would be persisted.
- The medications section previously used the generic heading “Medications/Médicaments/الأدوية”, which implied parity with persisted sections.
- The current privacy copy is conservative but factually broader than the implemented egress path: it says the document may be sent externally, whereas the Pulper extracts the document locally and calls the LLM with masked text.
- The canonical header bridge is intentionally presentation-only and avoids touching import workflow logic.

## Runtime correction

Branch: `agent/document-import-product-audit`

- `PulperPreview.hasUsefulData` now reflects categories the store actually persists: glucose, lab values and clinical notes.
- Medication extraction remains visible but is explicitly labeled in EN/FR/AR as detected and not imported.
- The empty state now says no **importable** medical data was detected.
- Anti-regression contract: `frontend/test/features/document_import_truthfulness_contract_test.dart`.

## Remaining safe work

- Tighten privacy wording to describe local extraction + authorized pseudonymized-text processing accurately.
- Review completion-state hierarchy and destination after real Chrome inspection.
- Review supported-format chip localization, especially Arabic.
- Exact-head CI / drift / screenshot / real Chrome certification.

## Certification gate

No final page score or CLOSED status before exact-head gates, real Chrome 390×844 inspection, runtime merge, post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
