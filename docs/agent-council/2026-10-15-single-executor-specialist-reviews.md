# IAMINA — fifteen bounded specialist review passes (single executor, not 15 subagents)

Source reviewed: `main@405a10205ff60618598ad27df95eaac3fd5aef4e` (postmerge #1036); report author type: ONE GPT-6 conversation/session.
**Methodology:** fifteen *sequential domain-focused source-review passes*, no separate model contexts and no individual LLM session IDs. These are not 15 independent agents, nor clinical/release certification. They supplement — never replace — the static probes or the actual isolated execution requirement in [issue #1029](https://github.com/hraaaaf/IAMINA-MVP/issues/1029).

Scope: representative critical contracts and tests read on one immutable source SHA, targeted GitHub CI logs and relevant official standards checked. **Not a file-by-file audit of all ~2,053 repository paths**; unreviewed paths explicitly remain open.

## Verification ledger

- `main@3affe8bcc61c6ef111986fb740f05fbdc3acb08a`: earlier 15-domain pre-audit [#1039](https://github.com/hraaaaf/IAMINA-MVP/pull/1039) merged, postmerge CI #38706505809 SUCCESS but docs-scoped.
- `main@405a10205ff60618598ad27df95eaac3fd5aef4e`: PR #1036 merged, exact-head postmerge CI #38708068060 and migration #38708068058 **pending at report drafting; never inherit premerge tests silently**.
- Fix candidate #1036 SHA `048c9c54e9333064c7557a1c8efe2c054d47180c`: CI #38707355599 SUCCESS: SQLite 2815 passed/5 skipped/3 xfailed, PostgreSQL 2819 passed/1 skipped/3 xfailed, 121 subtests each, Ruff/anti-bypass/Bandit PASS; migration #38707355603 SUCCESS.
- Issue #1040 voice privacy: candidate [PR #1041](https://github.com/hraaaaf/IAMINA-MVP/pull/1041) unmerged at report draft; its tests and CI must be recorded separately.
- `main` branch REST protected:false / rulesets [] at readback, [#1038](https://github.com/hraaaaf/IAMINA-MVP/issues/1038). No branch admin rule changed.

## Role-by-role bounded passes — one executor

### IA01 — Architecture
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `docs/architecture/ARCHITECTURE.md:12-32` ; `docs/architecture/ARCHITECTURE.md:77-102`.
- **Observation vérifiée / limite :** Flutter/Django modular-monolith and ownership boundaries are documented. Full callgraph and deferred legacy paths were not traced file-by-file.
- **Tests / exécutions :** `.github/workflows/ci.yml` import-linter completed on #38707355599; not a multi-service runtime proof.
- **Risque et contradiction :** MAJOR evidence gap: V1-01 source→derivation→consumer manifest absent from this review.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Map each endpoint, module owner, data store and UI consumer; prove module import boundaries and migration consequences.

### IA02 — Clinical safety
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/core/triage_classification.py:188-235` ; `backend/ai/api/v1/voice.py:155-165`.
- **Observation vérifiée / limite :** Deterministic classification/response path exists. Source voice emergency branch previously logged a patient transcript snippet, issue #1040; remediation in PR #1041, not yet merged at this source SHA.
- **Tests / exécutions :** backend/diabetes/tests/test_triage_classification.py exists; #1041 adds synthetic urgent-path logging regression, CI pending.
- **Risque et contradiction :** BLOCKED for clinical release: emergency semantics, native corpus, no real-device routing and professional sign-off cannot be inferred.
- **Verdict :** BLOCKED or CHANGES_REQUIRED.
- **Correction / next :** Fix #1040 logging; run emergency priority/under-triage cases FR/AR/Darija, cross-check emergency-resource jurisdiction with qualified reviewers.

### IA03 — Diabetes clinical / evidence
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/diabetes/services/clinical/evidence_registry.py:128-157` ; `docs/COMPANION_INTELLIGENCE_CONTRACT.md:40-52`.
- **Observation vérifiée / limite :** ADA 2026 source is registered with clinical_authority=NONE, and companion ceiling expressly forbids dose decisions. This does not prove every caller complies.
- **Tests / exécutions :** backend/diabetes/tests/test_target_applicability.py and test_clinical_semantics_hardening.py located; independent clinical review not executed.
- **Risque et contradiction :** CONDITIONAL: population applicability (children, pregnancy, comorbidity, unknown diabetes) must be linked to every patient-facing assertion.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Complete V1-01 calculation inventory; test unknown/insufficient evidence fail-closed and clinician authority on each downstream output.

### IA04 — CGM and metrics
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/diabetes/services/clinical/cgm_eligibility.py:74-95` ; `backend/diabetes/services/clinical/cgm_eligibility.py:115-223` ; `backend/diabetes/services/clinical/cgm_analytics.py:21-73`.
- **Observation vérifiée / limite :** Separate sufficiency gate checks window/session coverage and rejects overlapping sessions; metric function requires caller to prove sufficiency. No universal device claim established.
- **Tests / exécutions :** backend/diabetes/tests/test_cgm_sufficiency_contract.py:61-170 includes 14-day, coverage, overlap, duplicates and timezone cases.
- **Risque et contradiction :** MAJOR open question: all KPI/CGM UI consumers must be proven to honor gate, provenance, freshness and denominator.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Trace every GMI/TIR/TBR display and exclude sparse/unlinked data; retain physical sensor gate for device claims.

### IA05 — Medication and insulin
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `frontend/lib/features/journal/widgets/insulin_logging.dart:1-11` ; `backend/diabetes/tests/test_journal_insulin_logging.py:33-109`.
- **Observation vérifiée / limite :** Client parsing treats zero/invalid administered quantities as absent; server has negative-value rejection and same-patient replay tests. These are historical log controls, not prescriptive authorization.
- **Tests / exécutions :** test_journal_insulin_logging.py covers decimal preservation, negative rejection, UUID replay, cross-patient exclusion.
- **Risque et contradiction :** CONDITIONAL: prove every medicine/insulin UI uses logging-only semantics and never computes/recommends a dose.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Check absence/zero/delete semantics across backend and frontend; add no-dose/prescription-prompt negative tests where missing.

### IA06 — Nutrition and portions
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `frontend/lib/core/data/nutrition_catalog.dart:7-9` ; `frontend/lib/core/data/nutrition_catalog.dart:317-379` ; `docs/NUTRITION_DATA_SOURCES.md:35-46`.
- **Observation vérifiée / limite :** Carbohydrate quantities are source-backed and null when no reference; numerical conversion scales by grams. Moroccan household portions remain intentionally unquantified without proof.
- **Tests / exécutions :** frontend/test/core/data/nutrition_catalog_test.dart exists; not rerun in current backend-only remediation CI.
- **Risque et contradiction :** CONDITIONAL: individual food identity, preparation and MENA aliases may not have sufficient source match.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Cross-check curated records/portion bounds against source releases; test untranslated aliases, units and ranges, never infer insulin dosing.

### IA07 — MENA clinical language
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `frontend/lib/services/locale_preference_service.dart:37-41` ; `backend/core/locale.py:67-79` ; `backend/diabetes/api/v1/profile.py:28-28`.
- **Observation vérifiée / limite :** Frontend language preference and canonical locale resolver support English while legacy profile PATCH whitelist excludes it; separate endpoints may make this intentional, so do not call it a proven bug.
- **Tests / exécutions :** backend/core/tests/test_locale_api.py:30-150; frontend/test/p0_ux_6_4_rtl_accessibility_contract_test.dart:5-60 exists.
- **Risque et contradiction :** INFERRED interface contradiction: English persisted UI preference vs legacy profile field requires caller/use-path check; native emergency parity is separate.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Trace language choice persistence end-to-end and screen-reader RTL/Arabic numerals; get native clinician/speaker review before locale release.

### IA08 — Security/privacy
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/core/ai_egress.py:309-354` ; `backend/core/ai_processor_policy.py:167-195` ; `backend/ai/api/v1/voice.py:139-163`.
- **Observation vérifiée / limite :** Consent, purpose and text field controls exist; external Groq policy is PENDING. Raw internal batch errors were corrected in #1036; unredacted emergency/STT voice logs documented as #1040.
- **Tests / exécutions :** #38707355599 exact-head Ruff/Bandit/egress gates and SQLite+Postgres passed for #1036; #1041 source/tests under new CI.
- **Risque et contradiction :** CHANGES_REQUIRED: #1040 raw transcript logging remains until PR merges; data-at-rest and cross-provider negative egress need separate proofs.
- **Verdict :** BLOCKED or CHANGES_REQUIRED.
- **Correction / next :** Merge tested #1041 only after gates; prove secure logs/retention, vault and no external transfer to PENDING processors under OWASP MASVS.

### IA09 — Data/offline and migration
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/diabetes/api/v1/logs.py:122-188` ; `frontend/lib/services/sync_service.dart:101-115` ; `frontend/lib/services/patient_vault_session_controller.dart:52-108`.
- **Observation vérifiée / limite :** Batch UUID replay and patient checks exist; client reconciles auth epoch and retires prior vault; the batch privacy error has a tested generic-error remedy merged on this source HEAD.
- **Tests / exécutions :** #38707355599: SQLite 2815 passed and PostgreSQL 2819 passed on #1036 candidate; migration #38707355603 success; postmerge #38708068060 must be separately checked.
- **Risque et contradiction :** CONDITIONAL: A→B→A vault restoration, failed migrations and real PWA offline behavior are not established by backend-only tests.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Test cross-owner recovery, rollback, locked/offline reboot, dirty-record replay, schema migration and observed device/browser behavior.

### IA10 — Companion/LLM
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `backend/core/llm_gateway.py:99-125` ; `backend/core/ai_processor_policy.py:239-258` ; `backend/ai/api/v1/ai.py:156-201`.
- **Observation vérifiée / limite :** Gateway checks capability and declared egress context; processor requires explicit APPROVED. Summary assembles governed KPIs then calls a generator; this review did not trace all contexts for V1-03 zero-raw-clinical egress.
- **Tests / exécutions :** #38707355599 egress anti-bypass checks passed; unit/rule tests exist, but full callgraph and mock-provider payload captures not executed here.
- **Risque et contradiction :** MAJOR gap: generic/opaque-token-only V1-03 contract cannot be marked proven from DLP regex and gateway alone.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Inventory every LLM/STT/media callsite; capture synthetic outgoing payloads; negative tests for health facts, patient isolation, consent-off and provider-PENDING.

### IA11 — QA/verification
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `.github/workflows/ci.yml:22-82` ; `docs/QUALITY_SCORING_POLICY.md:21-46`.
- **Observation vérifiée / limite :** Workflow diff-scopes backend and frontend; green docs-only main CI #38706505809 skipped runtime suites; separate backend candidate #38707355599 executed SQLite and PostgreSQL tests.
- **Tests / exécutions :** Candidate #38707355599: SQLite 2815 pass/5 skip/3 xfail and PostgreSQL 2819 pass/1 skip/3 xfail; 121 subtests each. Frontend skipped for backend-only diff.
- **Risque et contradiction :** MAJOR contradiction to reject: green CI != all test families covered or reviewed clinical readiness.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** Report exact SHA+job states and test exclusions; require conditional relevant gates, no skipped critical jobs counted as run.

### IA12 — UX/accessibility
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `frontend/test/p0_ux_6_4_rtl_accessibility_contract_test.dart:5-60` ; `frontend/lib/services/locale_preference_service.dart:88-109`.
- **Observation vérifiée / limite :** Tests assert source-string semantics/target hints and locale logic; they do not show actual visual target↔render comparison or hands-on screen-reader behavior.
- **Tests / exécutions :** No BEFORE/AFTER viewport captures produced in this audit; D31 remains independent physical-device task.
- **Risque et contradiction :** NOT VERIFIED visually; static tests cannot establish UX certification or physical accessibility.
- **Verdict :** REVIEW_REQUIRED — limited evidence; no whole-domain PASS.
- **Correction / next :** For any UI change use target/mockup and BEFORE/AFTER same 390×844, FR/AR/RTL, iPhone/desktop, accessibility checks and score.

### IA13 — Release/operations
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `docs/ROADMAP.md:1-10` ; `.github/workflows/ci.yml:1-19`.
- **Observation vérifiée / limite :** Canonical roadmap explicitly NOT_RELEASE_AUTHORIZED and no patient production release candidate; Vercel/Neon is dev/cert only. This work modified no deployment configuration.
- **Tests / exécutions :** Postmerge run #38706505809 success on earlier docs lot; #38708068060 pending at snapshot on latest code merge.
- **Risque et contradiction :** BLOCKED for real-patient release: exact runtime freeze, processor/physical signoff, rollback and operator approval absent.
- **Verdict :** BLOCKED or CHANGES_REQUIRED.
- **Correction / next :** Keep no Vercel deployment; later bind build digest→SHA→runner→device, migrations rollback and explicit owner release approval.

### IA14 — Regulation and QMS
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `docs/ROADMAP.md:1-10` ; `backend/core/ai_processor_policy.py:167-195` ; `docs/COMPANION_INTELLIGENCE_CONTRACT.md:40-52`.
- **Observation vérifiée / limite :** Moroccan patient processing/cross-border evidence, clinical intended-use and professional signoffs are separate gates. AI-generated reviews are not competent regulatory signoff.
- **Tests / exécutions :** No completed CNDP/qualified audit or D31 device proof was created in this task.
- **Risque et contradiction :** HUMAN_GATE for real-patient data and medical claims; product label alone does not settle potential device-software qualification.
- **Verdict :** BLOCKED or CHANGES_REQUIRED.
- **Correction / next :** Map actual jurisdiction, purpose, legal basis/processor contracts, intended use and documented risk assessment with qualified human/legal decision.

### IA15 — Adversarial/cross-review
- **Preuve source (SHA `405a10205ff60618598ad27df95eaac3fd5aef4e`) :** `AGENTS.md:86-96` ; `docs/QUALITY_SCORING_POLICY.md:21-46` ; `docs/agent-council/README.md:1-31`.
- **Observation vérifiée / limite :** Compared source, CI scopes and claims: (1) 15 static probes != 15 model sessions; (2) docs green != clinical tests; (3) patient-data logs conflict with privacy doctrine; (4) main branch was unprotected at API readback.
- **Tests / exécutions :** GitHub branch main protection readback FALSE and repository rulesets []; [#1038] open. Source #1040 and fix #1036 independently read; no isolated IA15 model instance available.
- **Risque et contradiction :** NOT INDEPENDENT, NOT CERTIFIED. This adversarial *pass* is by same GPT session that did builder work, not a second agent.
- **Verdict :** BLOCKED or CHANGES_REQUIRED.
- **Correction / next :** Obtain actual independent model/human context and 15 verifiable session IDs for #1029; falsify every finding, rerun exact-SHA tests, register unresolved conflicts.

## Cross-audit / prioritized remediations

1. **P0 privacy — #1040**: finish reviewed voice logger redaction + synthetic tests, CI and postmerge before claiming the leak path closed. No inference of a real-world incident.
2. **P0 data/egress — V1-01/V1-03**: source→calculation→consumer and exact external provider payload register; negative safeguards + population applicability, no activation.
3. **P1 release governance — #1038**: enforce PR + relevant status checks + external review policy, with admin-configuration safeguards (CI scoped/skipped caveat).
4. **P1 agent runtime — #1029**: start coordinator on immutable updated `main`, spawn IA01–IA15 truly separate sessions, each own ID, audit path+line and tests; IA15 genuinely re-read independently. This remains an external runtime gate.
5. **Human/physical gates**: D31 real device testing, native MENA safety reviewers and legal/CNDP/clinical approvals separately; no patient data or Vercel without explicit authorization.

## Evidence score and caps

- Specialist passes documented here: 15/15 **single-executor**, distinct scope, NOT 15 subagents.
- True isolated LLM subagents with IDs for this audit: **0/15**.
- Clinical, regulatory, physical, UX and overall release scores: **NOT_SCORED / NOT_CERTIFIED** without required binary gates; no averaging of CI or static probes.
- Due to same executor, any material software pass has a maximum 9.4/10 even with sufficient proof; absent required tests cap 7.9/10; unresolved blocking clinical/privacy defects cap 5.9/10 under `docs/QUALITY_SCORING_POLICY.md`. Do not convert these ceilings into awarded ratings.
- Historical canonical P5: **6/12 = 50%** remains unchanged; no new release authorization.

## External primary standards (context, not certification)

- ADA Standards of Care in Diabetes (2026): https://professional.diabetes.org/standards-of-care
- OWASP MASVS: https://mas.owasp.org/MASVS/
- OWASP Error Handling: https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet
- GitHub branch protection: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- NIST AI RMF 1.0: https://www.nist.gov/itl/ai-risk-management-framework
- Moroccan CNDP regulatory source: https://www.cndp.ma/ (jurisdiction-specific human counsel required)

**Next exact:** finish technical fixes #1041 and postmerge, keep #1029 OPEN until runtime for 15 truly separate LLM sessions; bind any revised audit claims to a new immutable SHA.