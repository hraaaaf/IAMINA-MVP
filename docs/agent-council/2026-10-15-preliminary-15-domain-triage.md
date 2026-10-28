# IAMINA — Council-wide preliminary triage (NOT fifteen executed subagents)

**Date:** 2026-10-15. **Baseline:** `main@d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b`. **Owner:** single AI assistant, non-independent preliminary review. **Release verdict:** `NOT_CERTIFIED`. **Issue:** [#1029](https://github.com/hraaaaf/IAMINA-MVP/issues/1029).

## Evidence integrity and limits

- All 15 Copilot agent profiles, `AGENTS.md`, `docs/ROADMAP.md`, `docs/agent-council/README.md`, `.skills/full-app-agent-council/SKILL.md`, lot/security/release skills and quality policy were read at the baseline.
- This is **one assistant making 15 specialist-oriented triage passes, not 15 isolated agent sessions**. No individual subagent session/run ID exists. `scripts/ci_full_app_agent_council.py:110` explicitly reports `llm_subagents_executed = 0`. No claim of full codebase coverage, independent adversarial work or human expertise.
- `main` CI [#38700512524](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38700512524) succeeded; backend, Flutter and PostgreSQL runtime jobs were **skipped** for the documentation-only commit. Not exact-main full-runtime validation.
- See [Notion evidence ledger](https://app.notion.com/p/3fa77c66336281fb8b5dd89bdf38704e?pvs=204). Paths below are evidenced against `d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b`. Cited existing tests are **discovered**, not asserted executed on that baseline.

## Fifteen-domain dashboard — preliminary triage only

| Role | Evidence SHA:path:line | Specialized question / evidence gap | Verdict |
| --- | --- | --- | --- |
| IA01 Architecture | `backend/core/ai_egress.py:147-180` | Scope / module-ownership and provider boundary mapping still partial; need full graph/import tests | OPEN |
| IA02 Clinical safety | `backend/core/triage_classification.py:196-235` | Deterministic class exists; under-triage and negative MENA corpus not executed this pass | OPEN |
| IA03 Diabetes | `backend/diabetes/api/v1/profile.py:28-35,137-152` | Profile values/thresholds require population-specific origin and cross-surface validation | OPEN |
| IA04 CGM | `backend/diabetes/api/v1/cgm.py:130-169` | Transport and reading endpoints present; provenance/time-sufficiency/TIR audits not completed | OPEN |
| IA05 Medication | `frontend/lib/features/journal/widgets/insulin_logging.dart:1-16` | Taken insulin parser found, no global proof against prescriptive output | OPEN |
| IA06 Nutrition | `frontend/lib/core/data/meal_food_catalog.dart:34-39` | Food search/catalogue discovered; numeric source/portion/gram basis not fully traced | OPEN |
| IA07 MENA | `frontend/lib/services/locale_preference_service.dart:41,72-85` and `backend/diabetes/api/v1/profile.py:28,103-107` | Frontend supports English UI while profile API language enum excludes English; may be intentional separation, requires flow/contract test before classifying | OPEN / CONTRACT QUESTION |
| IA08 Security/privacy | `backend/diabetes/api/v1/logs.py:173-174` | Unexpected internal exception was exposed in client response; issue #1032 / PR #1034 candidate fix | CHANGES_REQUIRED |
| IA09 Data/offline | `backend/diabetes/api/v1/logs.py:122-174` | UUID cross-patient check and atomic savepoints observed; concurrent replay, restore and migration tests not run on baseline | OPEN |
| IA10 Companion/AI | `backend/core/llm_gateway.py:96-125,198-211`, `backend/core/ai_egress.py:238-337` | Gateway/consent checks seen, exhaustive anti-bypass/egress and prompt-control test absent here | OPEN |
| IA11 QA | `scripts/ci_full_app_agent_council.py:110-122` | Static-probes not LLM sessions; main run runtime jobs skipped; audit evidence insufficient | OPEN |
| IA12 UX | `frontend/lib/services/locale_preference_service.dart:36-85` | No observed BEFORE/AFTER same viewports or assisted navigation; no visual rating | OPEN |
| IA13 Release | `.skills/lot-execution/SKILL.md:1-20` + GitHub branch/rulesets API | `main` unprotected, no repository rulesets; issue #1033 | CHANGES_REQUIRED |
| IA14 Regulatory | `backend/core/ai_processor_policy.py:167-199` | External provider PENDING and Moroccan processing/transfer human legal gate unresolved; no clinical/regulatory certification | HUMAN_GATE |
| IA15 Adversarial | `scripts/ci_full_app_agent_council.py:110`, `docs/QUALITY_SCORING_POLICY.md:1-55` | Static probe/green-CI overclaims challenged; independent reviewer absent | OPEN |

### Findings, priority and corrections

**SEC-01 MAJOR — possible exception disclosure.** On `d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b:backend/diabetes/api/v1/logs.py:173-174`, an unexpected `str(exc)` is returned via `POST /api/v1/logs/batch`. This can disclose implementation/internal data; not a demonstrated patient leak or exploit. Existing adjacent API error handling uses generic conflict copy. [Issue #1032](https://github.com/hraaaaf/IAMINA-MVP/issues/1032). **Safe candidate fix:** [draft PR #1034](https://github.com/hraaaaf/IAMINA-MVP/pull/1034), exact candidate `c6aeb6927798fbba8573df1b2edf1f3805000d21`, changes only `backend/diabetes/api/v1/logs.py` and `backend/diabetes/tests/test_ninja_crud.py`. The regression injects `RuntimeError("SYNTHETIC_PRIVATE_DETAIL")` and asserts no response leak and a subsequent valid record succeeds.

**CI evidence on candidate `c6aeb692`:** [CI #38703721464](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38703721464) SUCCESS: backend ruff, import-linter, AI gateway/egress anti-bypass, Bandit, OpenAPI, pytest; SQLite `2814 passed / 5 skipped / 3 xfailed / 121 subtests passed`; PostgreSQL `2818 passed / 1 skipped / 3 xfailed / 121 subtests passed`; Flutter SKIPPED backend-only. [Migration drift #38703721445](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38703721445) SUCCESS. Pytest `-q` logs do not name individual collected test cases; exact named negative-test execution has not been separately proved. **PR stays DRAFT** awaiting independent Reviewer and Release Certifier. Do not merge on builder-only claim.

**GOV-01 MAJOR governance/configuration gap.** GitHub `GET /branches/main` reports `protected:false`; `GET /rulesets` returns `[]`. Thus instructions requiring Builder→Reviewer→Release Certifier are not enforced as server-side merge policy. [Issue #1033](https://github.com/hraaaaf/IAMINA-MVP/issues/1033). Owner/admin should define independent review, required checks and bypass policy; test enforcement, remembering GitHub 'skipped' status can count as acceptable for some required checks. No repo configuration changed by this triage.

**COUNCIL-01 BLOCKER for requested 15-agent completion, NOT product exploit.** 0/15 genuine LLM subagent sessions. Registered Remote Desktop Commander `DESKTOP-3MAJEEH` OFFLINE at inspection; Notion connector does not advertise session-spawn access. Open [#1029](https://github.com/hraaaaf/IAMINA-MVP/issues/1029). Need connected genuine orchestration (GitHub Copilot CLI), fifteen session IDs with immutable SHA, code/test/runtime/sources, IA15 independent reconstruction and cross-domain contradiction register.

**V1-01/V1-03 P0 roadmap work not complete**: `docs/ROADMAP.md` orders complete calculation/medical authority audit and strict privacy boundary; this preliminary triage is not a substitute. Each clinical, numeric, CGM, nutrition and AI output requires versioned source→derivation→frontend consumer lineage and negative tests.

**Human gates remain separate**: D31 physical devices, native-speaker/clinical privacy and CNDP/legal/regulatory review where applicable, and explicit user Vercel authorization. No real patient data, no third-party package installation, no costs or deployment.

### Primary standards and skill references (framework only; no certification)

- [GitHub Copilot CLI custom-agent instructions and subagents](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) — software operation; actual subagents require separate runs.
- [GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) — review and status checks configurable.
- [OWASP MASVS](https://mas.owasp.org/MASVS/) — mobile security benchmark.
- [NIST SSDF v1.1](https://csrc.nist.gov/pubs/sp/800/218/final) — secure engineering process benchmark.
- [ADA Standards of Care in Diabetes—2026](https://professional.diabetes.org/standards-of-care) — clinical source, **not** authorization to change IAMINA thresholds.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) — accessibility benchmark.
- [Moroccan CNDP, Loi 09-08](https://www.cndp.ma/textes-et-lois/) — applicable analysis is deployment/data-flow-specific; no legal approval claimed.

### Scoring and remaining sequence

`EXECUTION_SCORE=NOT_SCORABLE`, `ADVERSARIAL_SCORE=NOT_SCORABLE`, `RETAINED_SCORE=NOT_SCORABLE`; too little coverage, independent review and baseline execution proof. Under the repository quality policy, missing required test/evidence caps any claimed score at `7.9/10` and prevents `VERIFIED`. **Never score 15 static probes as 15 expert reviews.**

**NEXT exact:** independent review and release certification for PR #1034; GitHub policy decision for #1033; connect genuine subagent runtime, freeze current main SHA, run IA01–IA15, verify executed tests, compare cross-domain contradictions, publish 15 evidence reports; only then consider closure of #1029. P5 canonical historical progress `6/12 = 50.0%` unchanged (not 15-agent or V1 completion).
