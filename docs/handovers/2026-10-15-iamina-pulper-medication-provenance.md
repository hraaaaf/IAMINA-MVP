# IAMINA — Pulper medication field-level provenance — 2026-10-15

## Goal / Success / Proof
- **Goal**: reject uncited model-produced medication dose, frequency and type even if the drug name has verified provenance; refuse embedded substring citations such as `500 mg` inside `1500 mg`.
- **Success**: the synthetic DOCX LLM path rejects missing, wrong-line and embedded-substring citations; an individually cited dose/frequency/type remains available for patient preview only. The API preview must not display unverified values.
- **Proof expected**: focused tests `backend/diabetes/tests/test_pulper_provenance.py` and `backend/diabetes/tests/test_document_confirmation_scope.py`, full CI and relevant Pulper synthetic qualification on exact code HEAD. Follow [#1019](https://github.com/hraaaaf/IAMINA-MVP/issues/1019), parent [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005).

## Implementation candidate
- `_enforce_model_evidence_coverage` strips `MedicationEntry.dose`, `frequency` and `drug_type` unless **that exact field** has verified source evidence; a verified name does not confer evidence on other model-generated attributes.
- `_evidence_matches_value` rejects medication citations occurring only inside longer words or numeric tokens.
- Because this guard runs only from the LLM parser, an absent provider label must never disable it; a targeted negative test is included.
- Six focused provenance tests (missing independent citations, valid positive path, embedded dose, embedded drug name, wrong-line frequency, absent provider label) and one API preview rejection test.
- **Status at authored commit**: implementation candidate; exact-HEAD CI has NOT YET BEEN OBSERVED. Do not mark completed merely because this file is committed.

## Release boundary
- Source evidence is not physician approval; dose and frequency are historical document data, **never treatment advice**.
- Groq patient egress remains PENDING; qualified clinician, security, privacy/CNDP and provider approvals are not supplied.
- The parent PR remains DRAFT and no merge to `main`, real-patient processing or Vercel deployment is authorized.
- PR child may temporarily target `main` only to trigger existing pull-request CI; must retarget parent branch before any integration. Validate new parent HEAD after child merge. No thresholds or guardrails may be relaxed.
