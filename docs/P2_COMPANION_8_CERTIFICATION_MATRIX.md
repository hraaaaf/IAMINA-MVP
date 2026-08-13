# P2-COMPANION-8 — Safety + Certification Matrix

Status: IN PROGRESS

## Release rule

P2-COMPANION-8 does not add a second clinical engine. It makes the already-certified companion boundaries explicit release gates.

The repository CI runs the complete backend pytest suite on every pull request. Therefore every test listed below is already blocking: a failure makes CI red and prevents certification.

## Permanent blocking matrix

| Boundary | Blocking evidence |
|---|---|
| Smart Suggestions exposes only approved action classes and preserves its authority ceiling | `backend/diabetes/tests/test_p2_companion_smart_suggestions.py` |
| Consultation preparation remains patient-scoped, deterministic and clinician-authority preserving | `backend/diabetes/tests/test_p2_companion_consultation_companion.py` |
| After-visit continuity preserves explicit provenance and does not infer a visit from unrelated logs | `backend/diabetes/tests/test_p2_companion_after_visit_continuity_contract.py`, `backend/diabetes/tests/test_p2_companion_after_visit_runtime.py` |
| Evidence and uncertainty remain explicit and governed | `backend/diabetes/tests/test_p2_companion_evidence_uncertainty.py` |
| Longitudinal change remains bounded to authoritative review anchors | `backend/diabetes/tests/test_p2_companion_change_since_review.py` |
| Personal patterns remain descriptive and evidence-bound | `backend/diabetes/tests/test_p2_companion_personal_patterns.py` |
| Read-only companion overview preserves patient scope and does not consume proactive attention budget | `backend/diabetes/tests/test_p2_companion_overview.py`, `backend/diabetes/tests/test_p2_companion_overview_api.py` |
| Jurisdiction-neutral deterministic emergency wording remains regression-tested | `backend/diabetes/tests/test_clinical_semantics_hardening.py` |
| Input safety and false-positive behavior remain regression-tested | `backend/diabetes/tests/test_clinical_shield.py` |
| Advice/disclaimer throttling remains regression-tested in FR and Arabic/Darija | `backend/diabetes/tests/test_advice_filter.py` |

## Certification requirements

A P2-COMPANION-8 release is GO only when all of the following are true on the exact PR head:

1. Full CI succeeds.
2. Django migration drift succeeds.
3. All companion regression files above are still present and executed by the full backend pytest suite.
4. No new companion public entrypoint introduces free-text model authority, caller-supplied clinical state, or an unreviewed action class.
5. Patient scope, provenance, evidence windowing and uncertainty remain explicit.
6. Clinical Safety Reviewer records PASS on the exact head.
7. Release Certifier records GO on the exact head.
8. Zero unresolved review threads remain before merge.
9. Post-merge CI and migration drift succeed on the merge SHA.

## Non-goals

P2-COMPANION-8 does not create diagnosis, prescription, dosing, treatment-change, causality, efficacy or clinician-override authority. It also does not add a new LLM provider, notification system, emergency engine or treatment optimizer.
