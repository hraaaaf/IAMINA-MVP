# V1-03 — Local Summary and Unverified-CGM Safety Review — 2026-10-10

**STATUS: TECHNICAL CANDIDATE / NOT CLINICALLY CERTIFIED / UNMERGED.**

## PRE → Goal → Observable success → Proof

- Repository `hraaaaf/IAMINA-MVP`; base `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`.
- Working branch `security/v1-03-summary-local-only-20261010`, [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) OPEN/DRAFT.
- Goal: a patient summary route cannot build a patient-data model prompt or present clinical CGM metrics from merely CGM-labeled rows. Same invariants in the companion clinical context.
- Success criterion: nonempty and empty authenticated summary does not call model gateway/formatter; structured clinical pattern remains deterministic; unverified CGM row provenance returns `None` for clinical CV/TIR/TAR/TBR/GMI, no `CGM_HIGH_VARIABILITY` and no unverified TIR trend in Companion; baseline negative tests continue passing.

## Implementation reviewed

1. `backend/diabetes/services/clinical/engine.py`: local `_format_fallback` replaces `_format_with_llm` on `run_clinical_analysis`. `guard_normative_kpis` precedes normative pattern construction and is applied in `DiabetesEngine.analyze`; ungoverned TIR trend/label are suppressed.
2. `backend/ai/api/v1/ai.py`: `get_summary` reuses the engine's single localized `report.insights` rather than formatting a second time; the legacy summary helper is local. The response uses `project_public_kpis` for normative values and reports `ai_provider=fallback`.
3. `backend/diabetes/tests/test_v1_03_local_summary_egress.py`: synthetic Django endpoint tests with 5 readings and zero readings; direct legacy helper; 100 readings/16 days with 80% rows `source=cgm` but no persisted sensor sessions; companion negative path. Mocks deny model entry.
4. `backend/diabetes/tests/test_api.py`: historical one-reading high/low tests require descriptive means but do not imply continuous CGM TAR/TBR. `docs/api/openapi.json` synchronized with the new route docstring.

## Exact parent-HEAD evidence

- Candidate code/doc snapshot `8ca3ac69657b5c2c7014286514af8231292f82e2`.
- [CI #38034929969](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034929969): **SUCCESS**. Actual Django/pytest results: SQLite `2780 passed / 5 skipped / 3 xfailed` (121 subtests), PostgreSQL `2784 passed / 1 skipped / 3 xfailed` (121 subtests). CI Ruff and OpenAPI guard passed. **Frontend analyze/tests/PWA job SKIPPED**, do not claim Flutter evidence from this workflow.
- [Django migration drift #38034930096](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930096): SUCCESS.
- [Companion real chat E2E #38034930097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930097): SUCCESS.
- Superseded `41fa1b25` [CI #38034682093](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034682093) FAILED on the old single-reading TAR/TBR test assumptions plus a stale OpenAPI description. Both issues were corrected on `8ca3ac6`; do not mask or rewrite that history.
- All proofs above apply to the **parent**. This documentation closeout is a new commit and therefore needs its own exact-HEAD CI.

## Adversarial observations / unresolved risk

- Existing `/ai/doctor-brief` and companion chat/stream can still construct patient-derived text for the governed LLM gateway. No actual final provider-bound payload capture or external data leakage is proven by this lot; strict V1-03 zero-patient-context external LLM policy remains unresolved.
- `ai_provider=fallback` is truthful about zero model use but the Flutter summary model treats `fallback` as degraded. User-visible copy may thus be misleading. **No AFTER visual certification of this specific behavior**.
- Raw AGP output and existing descriptive SQL analytics require a separate clinical nomenclature and source-sufficiency review; normative fields are masked in the affected JSON summary and companion context, not magically throughout the product.
- Remaining CAL-09/10 patient-local clinical day / episode duration; CAL-11 USDA per-row primary provenance; CAL-12 typed/consented multilingual clinical PDF; reviews on other AI routes.
- Clinical, privacy/security, linguist-native FR/AR/Darija/RTL and accessibility reviewers remain unrecorded. Same-executor checks are not independent human review. No complete V1 decision is delivered.

## Next exact

1. Prove new documentation HEAD CI, migration drift and expected tests; inspect any new failure.
2. Review final outgoing provider payloads from Doctor Brief/chat/stream with wholly synthetic fixtures, including patient opt-out, denied processor policy, auth and locale. Do not send patient data to providers.
3. Resolve truthful UI state and capture BEFORE/AFTER at canonical viewports before a merge decision.
4. Independent specialist review, adversarial convergence, release certifier, then any approved merge and exact-main post-merge tests. Human patient/regulatory gates and explicit Vercel authorization remain separate.
