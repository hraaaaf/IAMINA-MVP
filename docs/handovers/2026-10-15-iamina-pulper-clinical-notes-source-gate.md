# IAMINA — Pulper unverified LLM clinical notes — 2026-10-15

## Goal / Success / Proof
- **Goal**: model-generated free-form `clinical_notes` cannot be shown in patient preview nor written to `LabReport` as source-verified observations or treatment guidance without a governed evidence contract.
- **Success**: synthetic source `metformin 500 mg`, model note proposing `1000 mg` -> note suppressed, warning generic without leaking suggested dosage; even an accurate verbatim LLM note remains hidden pending source-note schema and qualified human review. No unrelated structural medication or glucose changes.
- **Proof**: synthetic mocked parser tests (unsupported advice, verbatim note held, malformed note) + API/DB preview/confirm test, full exact-HEAD CI and bounded synthetic Pulper corpus qualification. Issue [#1023](https://github.com/hraaaaf/IAMINA-MVP/issues/1023).

## Strategy / trade-off
- Temporarily **suppress all LLM-origin `clinical_notes`** in `_map_json_to_output`, before patient preview/cache/database, and show a generic warning. This is deliberately conservative: even legitimate source observations are hidden until field-level source attribution and clinical meaning can be independently qualified.
- Patient-authored structured logs and deterministic spreadsheet glucose extraction stay governed by their existing paths.
- This is an implementation **CANDIDATE** on separate PR [#1024](https://github.com/hraaaaf/IAMINA-MVP/pull/1024). Candidate test collection: three mocked LLM parser regressions and one patient preview→confirm→LabReport persistence check; success must be proven with exact-HEAD GitHub CI (not assumed). It remains NOT YET CLINICALLY APPROVED.
- This branch was created from Pulper medication child [#1022](https://github.com/hraaaaf/IAMINA-MVP/pull/1022), then rebased by merging exact parent head. The parent [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) includes #1019 on SHA `8b4271c814db5d8acfa1d7770bf1570c05f7b7ba`, with **5/5** postmerge GitHub workflows SUCCESS. Diff to parent rechecked: three implementation/test files plus this handover only. Child #1024 remains a separate DRAFT candidate; CI has NOT yet qualified this child.

## Release boundaries
- No real patient data in tests, no prescribing/insulin recommendations, no unsafe model clinical authority.
- Groq remains PENDING for patient data; independent qualified clinical, security, privacy/CNDP/provider proof and release approvals [#320](https://github.com/hraaaaf/IAMINA-MVP/issues/320), [#1002](https://github.com/hraaaaf/IAMINA-MVP/issues/1002) absent.
- **No merge main and no Vercel deployment**. Main product parent PR stays DRAFT.
