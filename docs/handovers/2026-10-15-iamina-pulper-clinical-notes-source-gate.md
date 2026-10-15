# IAMINA — Pulper unverified LLM clinical notes — 2026-10-15

## Intégration et certification technique (15 octobre 2026)

- [#1024](https://github.com/hraaaaf/IAMINA-MVP/pull/1024) MERGED dans branche parent [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) uniquement : `3cec7ca1633852eccc7d2c7272ac0b848219a4e0`.
- Ancien parent `3cec7ca1` : le test macOS-host `test_request_contains_only_locale_script_and_opaque_token` a échoué par collision accidentelle `142` dans token opaque cryptographique, non par exposition de texte médical. Correction **test-only** `34415a5939c0a9b442c08fd8d2a50b2be4e90487` : token déterministe incluant `142`, structure du prompt autorisé exacte, assertions cliniques appliquées après retrait du token.
- Code `34415a59` : [Pulper #38704151662](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151662) PASS avec [JSON #11957098931](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151662/artifacts/11957098931) inspecté (18/18 critiques, 6/6 fail-closed, 0 corruption/0 fuite, textes synthétiques seulement), [Django #38704151679](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151679), [Shadow #38704151721](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151721), [Companion #38704151575](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151575), [CI #38704151643](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151643) SUCCESS; portabilité [#38704151705](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38704151705) encore en cours au moment de préparation. Vérifier sa conclusion avant clôture.
- Le **commit documentaire** contenant ce texte crée un autre HEAD : refaire validation CI de ce SHA final exact; preuve et statut vivants : [issue #1023](https://github.com/hraaaaf/IAMINA-MVP/issues/1023) / [Notion maître](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6). Aucune certification clinique, egress patient, main merge ou Vercel; #1002/#320 OPEN.


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
