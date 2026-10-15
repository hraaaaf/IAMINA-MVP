# IAMINA — Pulper P1 clinical data integrity fixes — 2026-10-15

## Goal / Success / Proof
- Goal: Keep **Groq** as governed Pulper text LLM while preventing false evidence verification and any upload+persist path that skips a patient-visible staged preview.
- Success: contradictory numeric/units or missing model citations never reach a verified provenance map or clinical DB; `POST /documents/ingest?confirm=true` is rejected before reading document/AI/cache/DB; patient-scoped `/documents/confirm/{batch_id}` continues once only. Qualification corpus preserves critical precision/recall >= 99%, provenance/fail-closed 100%, zero corruption and no identity leaks. 5/5 exact-HEAD CI green required. **No claims of success until runs/artefacts inspected.**
- Proof location: [P1 issue #1011](https://github.com/hraaaaf/IAMINA-MVP/issues/1011), [PR #1015](https://github.com/hraaaaf/IAMINA-MVP/pull/1015) child of [Groq #1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005).

## Implementation
- LLM-sourced evidence must contain a single bounded numeric source value agreeing with normalized unit/field; Glucose mmol/L conversion x 18.018 is verified against converted mg/dL to 0.5 tolerance. HbA1c IFCC mmol/mol is deliberately **not** auto-converted into NGSP % without qualified clinical conversion policy. Ambiguous multi-numeric lines, contradictory values, unsupported units and missing model evidence are rejected; critical numeric fields and unverified glucose readings removed prior to review/storage. Medication name/dose strings require literal agreement with source (unverified medication names discarded).
- Initial upload always preview-only; `confirm=true` returns 422 before any side-effect. Separate patient-bound one-time confirm remains available. Invalid/low-confidence outputs cannot persist even if user issues confirmation.
- Tests: wrong HbA1c source↔normalized mismatch, IFCC mmol/mol refusal, accurate/wrong mg/dL↔mmol/L glucose, ambiguous multi-value, medication dose mismatch, absent citation, wrong reading rejection; HTTP contract with no upload & DB state, patient-scoped preview→confirmation, replay and invalid extraction refusal.

## Boundaries
- These are **technical tests**; no patient identity, external clinical content, explicit clinical/privacy/security signoff, CNDP health processing or US transfer authorization provided. Groq processor policy remains **PENDING** for patient egress; no policy relaxation, no main merge, no Vercel production. Image OCR benchmark remains synthetic. Previous Pulper Golden Corpus 18/18 is a prior-SHA metric and must be re-established at the changed code SHA.
- Technical parent PR #1005 remains DRAFT. The child PR may be temporarily pointed at `main` only to activate existing `pull_request` workflow triggers; before integration, restore its base to the parent feature branch.
