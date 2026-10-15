# IAMINA IA01–IA15 — evidence pre-audit (NOT 15 agent executions)

Date: 2026-10-15. Evaluated source: `main@d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b` (immutable source reference).

## Authority and actual execution

- **15/15 specialist profiles read**, `AGENTS.md`, canonical roadmap, council README and full-app skill read.
- **0/15 independent specialist LLM subagent sessions executed**. This is one coordinator's bounded repository evidence inventory, **not fifteen audits**, independent reviews, clinical approval or release certification.
- Existing council GitHub Action produces **15 static probes** and reports `llm_subagents_executed: 0`. The CI for `main@d3a2c75` was SUCCESS (`38700512524`) but its backend/Flutter/PostgreSQL jobs were SKIPPED (docs-only diff).
- Runtime requirement #1029 remains OPEN. Desktop Commander `DESKTOP-3MAJEEH` was OFFLINE at check; no subagent-capable Work/Copilot CLI runtime connected to this execution. Do not substitute static checks for isolated agent IDs.
- One isolated security remediation **candidate** was separately created as PR #1036 on `bcae04ae3245179eed04c038cb1f68228da4bbde`; exact-head CI `38704886349` and migration `38704886483` succeeded. The original audited `main` remains distinct from this candidate.

## Fifteen-domain baseline register — source inspection, not specialist sign-off

Every source path below is from source SHA `d3a2c75d79b6e1374c3e6ff9320a2d6a5f1e193b`; therefore a reference like `file.py:31` means `d3a2c75:file.py:31`. Tests named are **located or inspected**, not individually claimed as independently executed unless a run is stated. All role verdicts: **PRE-AUDIT ONLY / NOT CERTIFIED**.

| Role | Inspectable source evidence | Existing tests or required proof | Risk / contradiction / action |
|---|---|---|---|
| IA01 Architecture | `docs/architecture/ARCHITECTURE.md:12-32,77-102` states Flutter/Django/module ownership | Import-linter ran SUCCESS in PR #1036 CI, not 15-agent architecture proof | Verify complete cross-layer call graph, residual legacy boundaries and ADR drift; V1-01 register |
| IA02 Clinical safety | `backend/core/triage_classification.py:188-235` deterministic classifier and response | `backend/diabetes/tests/test_triage_classification.py`; bounded MENA severity corpus/human safety review still required | Independent assessment of under-triage, numeric bounds and real emergency-resource applicability |
| IA03 Diabetes/evidence | `backend/diabetes/services/clinical/evidence_registry.py:128-157` ADA source record with zero external clinical authority; `docs/COMPANION_INTELLIGENCE_CONTRACT.md:40-52` | Evidence provenance/population tests exist; clinician validation not shown by source inspection | Check applicability/type/age/pregnancy, never infer prescription or diagnosis |
| IA04 CGM metrics | `backend/diabetes/services/clinical/cgm_eligibility.py:74-95,115-223` refuses KPI promotion from CGM provenance alone; `backend/diabetes/services/clinical/cgm_analytics.py:21-73` | `backend/diabetes/tests/test_cgm_sufficiency_contract.py:61-170` covers sparse/overlap/gaps/timezone | Verify every consumer calls sufficiency gate; test temporal sampling and physical sensor claims separately |
| IA05 Medication/insulin | `frontend/lib/features/journal/widgets/insulin_logging.dart:1-11` parses logged administered quantity | `backend/diabetes/tests/test_journal_insulin_logging.py:33-109` covers negative values, replay and cross-patient UUID | Prove logged historical dose cannot become recommendation anywhere downstream |
| IA06 Nutrition | `frontend/lib/core/data/nutrition_catalog.dart:7-9,73-91`; `docs/NUTRITION_DATA_SOURCES.md:35-46` | `frontend/test/core/data/nutrition_catalog_test.dart`; source↔portion matching checks required | Source provenance/portion confidence and MENA food-name equivalence must be audited exhaustively |
| IA07 MENA languages | `frontend/lib/services/locale_preference_service.dart:37-41,88-109`; `backend/core/locale.py:67-79` | `backend/core/tests/test_locale_api.py:30-150`; native human high-severity corpus not replaced | `backend/diabetes/api/v1/profile.py:28,102-106` legacy `preferred_language` enum excludes `en`, while separate locale resolver supports `en`; examine API ownership before calling this a defect |
| IA08 Cyber/privacy | `backend/core/ai_egress.py:224-283,316-375` consent/payload gates; `backend/core/ai_processor_policy.py:167-195` Groq PENDING | Egress negative tests; OWASP MASVS/MASWE; PR #1036 SQLite/Postgres security tests succeeded | **MAJOR** unexpected raw exception in `backend/diabetes/api/v1/logs.py:173-174`, issue #1035, candidate PR #1036 |
| IA09 Data/offline | `backend/diabetes/api/v1/logs.py:122-188` patient scope, batch savepoints, UUID replay and source invalidation | `backend/diabetes/tests/test_ninja_crud.py:182-218`, `backend/diabetes/tests/test_journal_insulin_logging.py:85-109`; new privacy test in PR #1036 | Need fault injection, cross-vault A→B→A, multi-device CAS, PostgreSQL replay and restore proof |
| IA10 Generative AI | `backend/core/llm_gateway.py:99-125` gateway capability/egress assertions; `backend/core/ai_processor_policy.py:239-258` processor approval gate | CI anti-bypass `check_ai_egress_boundaries.py` passed on PR #1036 | V1-03 demands zero patient raw context to external LLM; trace *all* callsites and output guards; no clinical authority |
| IA11 QA | `.github/workflows/ci.yml:27-74` diff-based backend/frontend scope; exact `main@d3a2c75` CI #38700512524 | PR #1036 CI #38704886349: SQLite **2814 passed/5 skipped/3 xfailed**, PostgreSQL **2818 passed/1 skipped/3 xfailed**, 121 subtests each | Green CI on docs-only SHA skipped major suites; inspect test collection/skips, not green badge alone |
| IA12 UX/accessibility | `frontend/test/p0_ux_6_4_rtl_accessibility_contract_test.dart:5-60` checks source strings and localized labels | Rendered BEFORE/AFTER identical viewport, screen-reader and RTL tests required; D31 device evidence separate | Static source-string tests ≠ visual/physical accessibility certification |
| IA13 Release/ops | `docs/ROADMAP.md:1-10` release posture `NOT_RELEASE_AUTHORIZED`, no current patient-prod release candidate | Exact source→artifact digest, rollback, migrations and physical/offline proof required | Do not deploy Vercel or promote dev Vercel/Neon to patient production |
| IA14 Regulatory/QMS | `docs/ROADMAP.md:1-10` retains P5-6A/P5-6B gates and D31 separately; `backend/core/ai_processor_policy.py:167-195` pending approval | Moroccan CNDP evidence by actual processor and qualified human sign-offs; not established by an AI review | Jurisdiction/intended-purpose analysis and release human gates must remain open |
| IA15 Adversarial | `AGENTS.md` Builder→Reviewer→Certifier and `docs/QUALITY_SCORING_POLICY.md`; baseline main branch REST `protected:false`, repo rulesets `[]` | Re-read actual test jobs, invalidated HEADs, skipped jobs, role/run identity; independent model context unavailable | Issue #1038 branch governance; reject 15 static probes as LLM reviews and reject green-only certification |

## Verified findings and contradictions

1. **SEC/DATA MAJOR**: source-level API information-disclosure path: `d3a2c75:backend/diabetes/api/v1/logs.py:173-174` interpolated `str(exc)` into API errors. Issue [#1035](https://github.com/hraaaaf/IAMINA-MVP/issues/1035), PR [#1036](https://github.com/hraaaaf/IAMINA-MVP/pull/1036) candidate fixes it; exact-head CI green, independent review/merge/post-merge pending. No actual patient leakage asserted.
2. **GOVERNANCE MAJOR**: repository `main` reported `protected:false`; `/rulesets` returned `[]` at check, while `AGENTS.md` requires strict PR/review/certification chain. Issue [#1038](https://github.com/hraaaaf/IAMINA-MVP/issues/1038). No assertion about uninspected external/global policies.
3. **QA EVIDENCE**: main CI SUCCESS on `d3a2c75` was docs-scoped and skipped backend/Flutter/Postgres. CI on PR #1036 separately ran backend SQLite and PostgreSQL, but frontend was correctly skipped. No transfer of proof between SHAs.
4. **AI INDEPENDENCE BLOCKER**: 15 specialist files and 15 deterministic probes exist, but **no 15 unique real subagent sessions**, so a 15-agent council score, independent adversarial sign-off or full-app certification would be false.
5. **CLINICAL / LEGAL / PHYSICAL GATES**: no observed competent clinician/regulator/native speaker validation for this whole-app review. Existing roadmap human release gates and D31 physical testing remain separate and untouched.

## Quality scoring / readiness

- 15-agent execution coverage: **0/15 confirmed true LLM subagents**. Profile infrastructure: 15/15 files present, not audit conclusions.
- Role-by-role execution/adversarial scores: **NOT SCORED** (no genuinely isolated role-specific execution and sign-off). Do not average source checks into a fictitious 10-point score.
- Council binary gate: **FAIL — NOT_VERIFIED/NOT_CERTIFIED** regardless of 15 static probes, or green technical CI. The repository quality policy caps claims with missing required proof at 7.9/10 and any blocking privacy/safety issue at 5.9/10 until corrected and re-verified.
- Code remedy candidate #1036: implementation + synthetic negative test present; exact-head SQLite/Postgres tests + lint, Bandit and migration drift GREEN; no independent reviewer/Release Certifier, no post-merge evidence. **DRAFT / NO CERTIFICATION**.
- Canonical historical global P5 completion is still **6/12 = 50%**; this audit does not add a closed lot.

## Prioritized executable roadmap

1. **P0 — #1035**: review exact two-file PR #1036 with independent security reviewer; check no exception canary in API; certifier/Perfection Pass; merge only after all gates then verify exact main SHA and post-merge CI. Do not bypass patient/safety policy.
2. **P0 — V1-01/V1-03**: full enumeration of calculations, data modality, source→derivation→consumer and every generative egress path; negative/missing/provenance tests. Distinguish verified from planned.
3. **P1 — #1038**: enable branch PR/required-check governance after policy/owner review, verify rejected bypass. No deployment action.
4. **P1 — #1029**: establish actual subagent-capable runtime, freeze new SHA, delegate IA01–IA15 to 15 isolated read-only contexts with unique session IDs, proofs and evaluated tests; IA15 independently reconstructs; reconcile contradictions and create only evidenced remediation issues.
5. **P1 — releases**: clinical, privacy, regulatory, native MENA and D31 physical gates only through competent real reviewers and devices; no real patient data, no Vercel without owner approval.

## Official references checked

- GitHub custom subagents: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli
- OWASP error handling: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet
- OWASP MASVS: https://mas.owasp.org/MASVS/
- NIST SSDF final v1.1 (2022), v1.2 only draft: https://csrc.nist.gov/pubs/sp/800/218/final
- ADA 2026 Standards of Care: https://professional.diabetes.org/standards-of-care
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- EU MDCG 2019-11 rev.1 (June 2025), only jurisdictional as applicable: https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en
- GitHub branch protection: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

**STOP/next:** Do not close #1029 on this pre-audit. Recheck issue #1035 independent review and any remaining CI/merge work; real 15-agent execution requires external runtime access. No patient data, no expense, no Vercel deployment.