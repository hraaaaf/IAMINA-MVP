# IAMINA — Pulper unverified LLM clinical notes — 2026-10-15

## Goal / Success / Proof
- **Goal**: model-generated free-form `clinical_notes` cannot be shown in patient preview nor written to `LabReport` as source-verified observations or treatment guidance without a governed evidence contract.
- **Success**: synthetic source `metformin 500 mg`, model note proposing `1000 mg` -> note suppressed, warning generic without leaking suggested dosage; even an accurate verbatim LLM note remains hidden pending source-note schema and qualified human review. No unrelated structural medication or glucose changes.
- **Proof**: synthetic mocked parser tests (unsupported advice, verbatim note held, malformed note) + API/DB preview/confirm test, full exact-HEAD CI and bounded synthetic Pulper corpus qualification. Issue [#1023](https://github.com/hraaaaf/IAMINA-MVP/issues/1023).

## Strategy / trade-off
- Temporarily **suppress all LLM-origin `clinical_notes`** in `_map_json_to_output`, before patient preview/cache/database, and show a generic warning. This is deliberately conservative: even legitimate source observations are hidden until field-level source attribution and clinical meaning can be independently qualified.
- Patient-authored structured logs and deterministic spreadsheet glucose extraction stay governed by their existing paths.
- This is an implementation **CANDIDATE** on a separate follow-up branch and is **not yet tested/approved**.
- This branch was created from Pulper medication child [#1022](https://github.com/hraaaaf/IAMINA-MVP/pull/1022); it must NOT be integrated until parent [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) includes the certified #1019 patch and the new diff is confirmed to contain only this issue's changes.

## Release boundaries
- No real patient data in tests, no prescribing/insulin recommendations, no unsafe model clinical authority.
- Groq remains PENDING for patient data; independent qualified clinical, security, privacy/CNDP/provider proof and release approvals [#320](https://github.com/hraaaaf/IAMINA-MVP/issues/320), [#1002](https://github.com/hraaaaf/IAMINA-MVP/issues/1002) absent.
- **No merge main and no Vercel deployment**. Main product parent PR stays DRAFT.
