# V1-01 — Calculation & clinical-authority inventory (working audit)

> Status: **OPEN / partial source audit + exact-head automated/UI evidence**, not a complete calculation inventory, clinical certification, or patient-level validation.
> Baseline: `hraaaaf/IAMINA-MVP main@13b7cce12c86daf60119fb703f22e8c6c192cf8d` (PR #919 post-merge).
> Scope: new V1-01 in `docs/ROADMAP.md`; retain historical P5 pre-real-patient gates.
> Change policy: audit and regression proof first; no new clinical target, therapeutic advice, LLM medical authority or deployment.

## Goal / acceptance / proof

**Goal:** enumerate patient-affecting arithmetic and normative decisions, identify each input/source, authority, sufficiency rule, consumer, and cross-layer discrepancies.

**Success means** every relevant backend/frontend calculation path has a row with its provenance, units, missingness, clinical authority, target population and downstream Home/Reports/IAmina/export consumers; independent numeric oracles, negative/insufficient-data tests, SQLite/PostgreSQL parity, API projection and mobile flow evidence are attached to the exact final HEAD.

**Not yet proven:** exhaustive call graph, all calculation outputs and consumers, integration UI runs/screenshots, patient isolation across every call path, independent specialist review, certification. Exact-head regression CI succeeded on commit \`100355d17...\`; any newer documentation commit requires rechecking its own SHA. No V1-01 completion percentage.

## Discovery perimeter (Git tree, 1,761 tracked blobs)

On the baseline tree, `backend/diabetes/services/clinical/` contains **55 direct Python files** (including non-calculation and policy modules), `backend/diabetes/api/v1/` **14**, `frontend/lib/features/journal/` **8**, `frontend/lib/features/dashboard/` **4**, `frontend/lib/data/drift/` **4**. These are *search perimeters*, not counts of audited algorithms. Inspect nested widgets, nutrition catalogues, imported APIs, CGM adapters, local DB and test fixtures before claiming completeness.

## Initial calculation and consumer register

| ID | Domain / producer | Source, transformation, consumer | Authority / gates to verify | Evidence state |
| --- | --- | --- | --- | --- |
| CAL-01 | Raw glucose KPIs | `backend/diabetes/services/clinical/sql_analytics.py`: SQL mean, sample SD, CV, row-based in/above/below range, GMI candidate, GRI, 5-zone counts | Derived from valid `LogEntry` and selected patient/time window; raw row fractions are **not** CGM time coverage | Source inspected; full SQL/PG parity and every caller PENDING |
| CAL-02 | Public KPI API and AI summary output | `backend/diabetes/api/v1/kpis.py::project_patient_kpis` -> `assess_cgm_window` -> `compute_verified_cgm_metrics` -> `project_public_kpis`; `ai/api/v1/ai.py::get_summary` now uses same projection | Normative output requires verified session/registry; raw descriptive SQL internally separate | Candidate code + synthetic negative test; exact-head CI PENDING |
| CAL-03 | CGM sufficiency and observations | `cgm_eligibility.py`, `cgm_analytics.py`: 14-day candidate window, session time fraction × capture, timestamp dedupe; descriptive CGM percentages and CV | Correct source/session; freshness/gaps/coverage; verified only on eligible windows; not always equal to true duration-weighted CGM exposure | Source inspected; synthetic tests exist, PG/cross-patient/runtime PENDING |
| CAL-04 | Target applicability | `target_applicability.py`: explicit clinician confirmation, known population context, valid bounded range, percentage goal, non-future timestamp | Verified patient-specific target **and** verified CGM metrics are required before normative comparison | Source inspected; cross-surface and language checks PENDING |
| CAL-05 | Offline/dashboard glucose | `frontend/lib/features/dashboard/clinical_engine.dart`: legacy row-based fraction, high/low bins, mean, sample CV, GMI calculator. `diabetes_module.dart` routes `/dashboard` to `DashboardCompanionEntryScreen` -> `DashboardPremiumScreen`, **not** this legacy `DashboardScreen`; legacy `_GMICard` masks GMI | Distinguish reachable premium patient flow from retained legacy widgets and ensure any reactivation cannot turn a manual sample fraction into CGM TIR | Actual module route verified in source; complete consumer test PENDING |
| CAL-06 | Offline Reports | `frontend/lib/features/journal/reports_screen.dart` + `reports_screen_presentation.dart` `_Stats.from`: log average, days with data, count below/inside/above configured range; `display()` uses `mgDl / 18.0` in mmol/L | Labels are descriptive **measurements in range**; verify rounding/units against shared 18.018 factor, profile authority, nulls and patient-scoped offline data | Producer and screen inspected; independent numeric oracle/runtime PENDING |
| CAL-07 | Glucose units | Legacy `backend/diabetes/services/clinical/unit_guard.py` silently defaults unknown units to mg/dL; **separate** active `backend/diabetes/middleware/unit_guard.py` calls canonical `log_input` guard and explicitly blocks invalid conversions; Flutter `glucose_formatter.dart` uses 18.018 | Verify all reachable inputs go through strict guard, supported aliases and numeric finite/round-trip tests; align patient-readable display constants | Strict middleware + legacy helper inspected; reachability and runtime PENDING |
| CAL-08 | AGP/daily/trends | `sql_analytics.py`: SQL/Python percentiles, daily averages, week-over-week range fractions and direction | Session/interval density, timezone/day grouping and unit eligibility; do not call sampled fractions CGM TIR | Implementation partly inspected; independent oracles PENDING |
| CAL-09 | Pair meal response | `paired_meal_response.py`: elapsed minutes and median pre/post/delta by episode | Confirmed meal/time pairing; no drug effect, prediction, diagnosis or causal attribution | Static producer inspected; consumers and tests PENDING |
| CAL-10 | Personal response/longitudinal | `personal_response.py`, `governed_longitudinal.py`, `observation_memory.py`, `proactive_intelligence.py` | Patient-scope, evidence density, descriptive baseline, no causality/clinical confidence; source erasure | Some producer signatures inspected; complete pipeline PENDING |
| CAL-11 | Nutrition & portions | `frontend/lib/core/data/nutrition_catalog.dart`, `meal_food_catalog*.dart`, portion editor; backend food decisions | Food/preparation/portion provenance, no invented grams/carbs, no dose implication | DISCOVERY ONLY |
| CAL-12 | PDF/export and LLM narration | `frontend/lib/services/local_report_pdf.dart`, diabetes consultation summaries, companion projections | Only already-authorized metrics with traceable window/source, no novel clinical fact from formatting | DISCOVERY ONLY |

## Triage: observations to reproduce, **not** established end-user defects

- **RISK-01 (confirmed defect, historical patch tested):** Old KPI cache key truncated fractional ranges with `int`. Candidate fix stores exact float representation in the key. Regression `test_kpi_cache_target_precision.py` passed both backends on `100355d17...`. Consumer reachability/invalid-input contracts still pending.
- **RISK-02 (confirmed API output authority gap; remediation candidate pending CI):** `POST /api/v1/ai/summary` serialized raw SQL `tir_pct`, `cv_pct` and `gmi` from mixed/manual LogEntry rows, unlike evidence-gated `GET /api/v1/kpis/`. Candidate centralizes `project_patient_kpis` in KPI API and uses it in `/kpis/`, `/ai/summary`, and the `/ai/doctor-brief` prompt; `test_v1_01_summary_kpi_authority.py` asserts null normative summary metrics and removes raw TIR/GMI/CV from the clinician-brief prompt for manual-only data. Actual deployed user exposure not yet reproduced; audit other consumers separately.
- **RISK-03 (P1 investigation): dormant offline GMI path.** `ClinicalEngine.calcGMI` accepts local `LogEntryData` and calculates on any nonempty sample; the inspected `_GMICard` deliberately shows unavailable. Prove non-reachability outside that card (or remove/guard old entry point) with tests.
- **RISK-04 (P1 investigation): legacy unknown-unit default.** `UnitGuard.normalize_to_mg_dl` converts known mmol/L and g/L but treats every other string as mg/dL. The separately inspected active middleware uses canonical `log_input` validation and rejects failed normalization. Verify whether the legacy method is reachable anywhere before declaring a patient defect or altering it.
- **RISK-05 (P1 investigation): cross-layer parity.** Backend PG/SQLite and local Drift may differ in day boundaries, rounding and which samples enter mean/range percentages. Build common patient-scoped, fixed-time fixtures and compare semantics, not just numbers.
- **RISK-06 (P1 investigation): unit-display conversion drift.** `_Stats.display` in Reports and `_DashboardBody._display` in the active premium Home use `/ 18.0` for mmol/L, while shared `GlucoseFormatter.mgdlToMmolFactor` and backend convert with `18.018`. Verify numeric differences near decimal rounding boundaries; any UI change requires BEFORE/AFTER at identical viewports.

Existing code protections already observed: API `project_public_kpis` checks verified CGM/evidence and recomputes from session-linked readings; offline GMI card displays no estimate; `target_applicability.py` requires explicit authority. Existing tests **present in the tree** include `test_p0_clinical_analytics_integrity.py`, `test_cgm_sufficiency_contract.py`, `test_governed_cgm_promotion.py`, and Flutter smart-insight/summary truthfulness contracts. Their presence is **not** proof they were executed on this branch.

- **RISK-07 (confirmed internal calculation defect; remediation candidate): fractional 5-zone gap.** `LogEntry.blood_sugar` is a decimal with **2 places** (`backend/diabetes/models/entry.py`), but both PG/SQLite `sql_analytics.py` 5-zone queries used `BETWEEN 54 AND 69` and `BETWEEN 181 AND 250`. Thus 69.50 counted in aggregate TBR but not TBR1/TBR2; 180.50 counted in aggregate TAR but not TAR1/TAR2. Candidate changes both SQLs to `>=54 AND <70` and `>180 AND <=250`, keeping all existing clinical endpoints and 70/180/54/250 thresholds unchanged. Three independent synthetic fractional-boundary regression cases added to `test_battelino_kpis.py`. Exact-head check on commit \`100355d17baf1e6544e322ca2e6e5ed2db6c89dc\`: CI #37867405403 SUCCESS (backend Ruff + full pytest, PostgreSQL full suite, guards, secrets); migration drift #37867405395 SUCCESS. These are **automated regressions only**, not downstream consumer/clinical-authority certification. The inventory remains OPEN.
- **RISK-08 (P1 investigation): normalization-factor divergence.** Canonical active `backend/diabetes/contracts/log_entry.py` uses `MMOL_L_TO_MG_DL=18.016`; legacy `backend/diabetes/services/clinical/unit_guard.py` and shared Flutter `GlucoseFormatter` use 18.018; live premium Home and Reports use 18.0 in patient display. Determine single authoritative factor, test boundary display equivalence and unit round-trips before UI changes, with mandatory visual BEFORE/AFTER evidence.

### Evidence-only inventory refinements

- Nutrition arithmetic is not an all-food calculator: `frontend/lib/core/data/nutrition_catalog.dart` returns null without documented `NutritionReferenceValue`, uses `carbsPer100g × grams / 100` for direct grams, and range bounds for sourced natural portion equivalents; `nutrition_portion_editor.dart` requires a confirmed selection. Validate source version, locale and roundtrip behavior; do not imply all foods have numeric nutrition.
- `backend/diabetes/services/clinical/correlations.py` and `prediction.py` are retired compatibility prototypes explicitly returning `[]` and `None`. They are not evidence that patient-facing causal/predictive analytics are implemented.
- Clinical `LogEntry.blood_sugar` storage permits two decimal places, so tests using only whole mg/dL inputs were insufficient to catch the 5-zone partition gaps.



## Verified automated evidence (2026-10-09, historical exact HEAD)

- [CI #37867405403](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37867405403) **SUCCESS** on `100355d17baf1e6544e322ca2e6e5ed2db6c89dc`: backend Ruff, import architecture, LLM/egress anti-bypass, Bandit, OpenAPI, full pytest; full suite also executed with PostgreSQL source-of-truth. Flutter was intentionally skipped (no changed Flutter path).
- [Django migration drift #37867405395](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37867405395) **SUCCESS** on the same SHA.
- Candidate RISK-01 cached fractional target collision and RISK-07 SQL 5-zone fractional gaps were covered by committed synthetic regression tests on that HEAD; both automated pipelines passed. This proves **test-gated backend changes**, not complete runtime/clinical audits.
- Clinical threshold rationale and source-to-public-consumer semantics require specialist review. Patient-visible Home/Reports/IAmina screenshots and all-unit parity not yet evidenced. No merge, no Vercel deployment.

## Additional P0 output regression candidate (2026-10-09)

- Source finding: `POST /api/v1/ai/summary` returned unprojected row fractions and raw SQL GMI/CV as normative-named response fields. This is a verified code path, NOT proof of actual production exposure.
- Candidate fix: use the existing governed CGM verification/projection for `/kpis/`, `/ai/summary` response, and `/ai/doctor-brief` prompt. Retain raw analytics only for descriptive internal processing. V1-03 zero patient-data model egress remains a separate open requirement.
- Added synthetic negative oracles: 60 manual readings over 14 days with raw GMI/TIR nonnull must yield null normative summary fields; clinician-brief prompt excludes raw CGM TIR/GMI/CV; no CGM metric computation without verified session. Unit test bypasses the endpoint consent decorator solely to test the handler in isolation with a fake patient and no provider operation.
- **Not yet proven:** exact final-HEAD Ruff/pytest/PG/SQLite, positive genuine-CGM fixture, frontend real-user rendering, non-summary consumers and independent clinical/data security reviewers. NO MERGE.

## Test/oracle matrix for continuation

1. **Provenance and eligibility:** manual-only, mixed, valid 14-day CGM, below-threshold coverage, gaps, duplicate timestamps, overlapping sessions, device mismatch, stale/unknown data; normative fields null unless correctly verified.
2. **Math boundaries:** empty, one sample, repeated identical values, extreme values, exact cutpoints (54/70/180/250 mg/dL), fractional boundaries, invalid/NaN/Infinity, rounding ties; TIR/TBR/TAR disjoint bins and percent-sum invariants.
3. **Authority:** clinical target missing, unconfirmed, future-dated, special population unknown, consent revoked, target changed; do not substitute population-wide targets.
4. **Database/API:** independent oracle on SQLite **and PostgreSQL** for SQL-only operators (`STDDEV_SAMP`, `PERCENTILE_CONT`, timezone date functions), patient isolation, cache collision and invalidation, API response nullability.
5. **Consumers:** same source/period/profile -> Home, Reports, IAmina structured context and PDF/export with correct `descriptive` vs `CGM-verified` labels; no LLM-created metric/decision; inspect real renders if presentation changes.
6. **Governance:** log evidence version, method, modality, window, missingness and applicable population for each public value; clinical reviewer, independent adversarial reviewer, release certifier, exact-head CI and post-merge gate.

## First remediation candidate and verification status

- Cache-key fractional precision candidate correction in `backend/diabetes/api/v1/kpis.py` using round-trippable float representations, preserving user/window isolation and making distinct fractional ranges distinct keys. The old keys expire normally with the existing 300-second TTL.
- Added `backend/diabetes/tests/test_kpi_cache_target_precision.py` with numeric-key separation and mocked endpoint recomputation assertions. **Written tests are not yet execution evidence**; final exact-head CI required.
- **Initial risk perspective A (clinical/authority):** a stale standard-window result might be returned for an altered range if cache keys collide; verify API gate and negative test, do not claim exposed patient incident.
- **Initial risk perspective B (data/UX):** frontend numeric display factors differ and old/new dashboard have different reachability; tests must target actual premium route. Decimal 5-zone SQL gaps warrant independent PG/SQLite testing as part of this same audit.
- **Provisional material-step score (not certification):** execution 6.9/10; adversarial 6.6/10; retained 6.6/10 due to incomplete producer/consumer enumeration, absent branch runtime evidence and pending independent review; no binary gate declared green.

## Immediate next actions

A. Fully reconstruct CAL-01/02/03 API/cache/projection flow, independently reproduce RISK-01 and add a regression test or close with contrary evidence.
B. Verify fractional 5-zone SQL partition invariants on SQLite and PostgreSQL; then static + test-index scan of all 55 clinical service modules and their import/call sites; extend every candidate to a complete input→calculation→consumer registry.
C. Validate independent numerical oracles and negative paths on both supported DB engines; confirm Flutter/Drift offline semantics and outputs.
D. Two isolated adversarial perspectives (clinical/safety vs cross-layer/data), fix supported defects, rerun tests on new HEAD; specialist reviewers and Release Certifier; do not merge/close without required proof.

### Mandatory status

- Builder stage: **OPEN**, partial static discovery only.
- Executed tests on this branch: **none at time of this baseline document**.
- Independent reviewers: **not yet performed**.
- Certification/clinical clearance: **none**.
- Deployments: **none authorized or performed**.

## Patient-visible Flutter null-vs-zero remediation + GitHub Actions visual goal

**Goal:** patient with 60 manual readings over 14 days and *no verified CGM session* must never see fabricated 0% GMI/TIR/CV, adverse hero inference, or a 100% fabricated AGP distribution.

**BEFORE (source-verified):** null TIR/GMI/CV in `ai_summary_screen_presentation.dart` were replaced with 0.0; `hasSufficientData` counted manual rows, so the AGP bar could show fabricated composition. Actual browser BEFORE proof pending on GitHub Actions.

**Target:** use `Non disponible` and `Données insuffisantes` for unavailable normative fields, no numeric range reference with missing value, neutral hero until clinical CGM proof, no AGP percent legend/bar without all three approved fractions. Preserve descriptive count/mean. No new threshold.

**Implementation:** conditional unavailability render and semantics, production widgets exercised through a *synthetic test-only fixture* `AISummaryKpiVisualFixture`. No patient data/LLM/backend in harness.

**Validation:** GitHub Actions `ui-summary-kpi-visual-cert.yml` checks out exact PR SHA and original base presentation file in turn, builds real Chrome Flutter Web for both states, records three same-state 390×844 captures `cards/hero/agp`, checks distinct hashes, uploads six PNGs, and runs targeted Flutter widget tests. Other `ui-browser-screenshot.yml` / `ui-screenshot-audit.yml` checks are also triggered by touched frontend paths. **Screenshots and tests remain pending until actual CI result.** The older backend CI is superseded. Independent clinical+UI reviewers and scoring/perfection pass remain open. No merge/deploy.


## V1-01 CAL-06/07 — Glucose display factor convergence (candidate; 2026-10-09)

- **Goal:** ensure Home premium, offline Reports and shared Flutter glucose formatter render the same patient-entered reading using the active backend contract `MMOL_L_TO_MG_DL=18.016`, without modifying stored mg/dL glucose or any clinical range thresholds.
- **BEFORE source:** Home `_DashboardBody._display` and offline Reports `_Stats.display` divide by `18.0`, while shared `GlucoseFormatter` divides by `18.018` and backend `log_entry.py` uses `18.016`. A 190 mg/dL reading may show 10.6 in Home/Reports vs 10.5 with backend factor (1 decimal). Visual proof still pending exact run.
- **Target/acceptance:** `190 mg/dL -> 10.5 mmol/L` throughout; other table or glucose clinical cutpoints remain unaltered. `70 -> 3.9`, `180 -> 10.0`, `118 -> 6.5`, `109 -> 6.1`, each with a fixed independently specified oracle. Real Chrome captures of **identical** seeded synthetic `190 mg/dL` Home and Reports at `390×844`, `768×1024`, BEFORE/AFTER from the same PR SHA, plus Flutter analyze/tests, exact CI.
- **Implementation candidate:** shared `GlucoseFormatter.convert` with factor `18.016` used by Home and Reports, no API/backend/schema/production seed change. Browser harness uses optional `v101=unit-190` opt-in isolated browser-only synthetic fixture: localized mmol/L profile and latest 190 mg/dL log. New workflow swaps only product source files to baseline commit `c0420ceb...` for BEFORE and restores exact HEAD for AFTER; preserves identical fixture/routes and captures.
- **Supporting external source:** ADA/AACC 2023 recommendations use `÷18` for *approximate* practical conversion; engineering choice is parity with **current** active backend 18.016, not a changed diagnostic/treatment recommendation. Need independent clinical review before release.
- **Outstanding:** wait for CI and PNG artifacts on exact HEAD; visually compare numeric text/overflow, check change against original 190 reading, test full locale/roundtrip/unknown unit, independent review, perfection pass; no V1-01 certification, merge or deployment implied.

## V1-01 CGM AGP public authority correction — 2026-10-09 candidate

**BEFORE VERIFIED FROM CODE:** `sql_analytics.compute_agp_profile` aggregates unqualified `diabetes_logentry` into percentiles (manual/mixed included). `get_summary` placed its output in an `agp_profile` dict key, but `SummaryResponse` omitted the field, so endpoint serialization could not expose it. Frontend expects AGP from `SummaryResponse.fromJson` and gates it by verified CGM fractions.

**GOAL:** produce public AGP only when governed public KPI window accepts session-linked CGM; expose `agp_profile` explicitly on the Ninja/Pydantic response schema; NEVER promote raw LogEntry/manual point distributions as sensor percentiles.

**Candidate:** add `compute_verified_cgm_agp_profile` to `cgm_analytics.py`, filtering patient/session/source/time, deterministic timestamp deduplication, local hour from one consistent valid session timezone, Python percentiles on the same sensor facts across PG/SQLite. `get_summary` calls only after TIR/TAR/TBR public projection is non-null; no raw SQL AGP call; schema field defaults to empty. Daily averages remain descriptive manual-inclusive and distinct. No new CGM eligibility thresholds.

**Oracle tests (pending CI exact-HEAD):** unlinked rows, wrong source, different patient, outside session, duplicate timestamp and manual LogEntry excluded; expected two-value percentile exact P5=101/P25=105/P50=110/P75=115/P95=119; invalid session timezone fails closed; 14-day hourly verified sensor fixture produces 24 serialized AGP bins while GMI remains withheld; manual-only route returns [] and has no AGP engine calls. No production patient input, no LLM networking. **V1-01 remains OPEN** pending run, real API contract, review and other CAL families.

## V1-01 CAL-09/10 — UTC versus local-day characterization candidate (2026-10-09)

- **Goal:** prove how three distinct evidence engines count `distinct_days` at a timezone boundary, without silently converting that count into a clinician-approved patient-local definition. `BasePatientProfile`/`DiabetesProfile` currently have no persisted patient timezone field to authorize such a conversion.
- **Technical oracle:** three readings at UTC 23:50, 23:54, and next-day 00:05 are spread across **two UTC dates**, but **one day at UTC+01**. Current `personal_response`, explicit-episode `paired_meal_response`, and source-separated `governed_longitudinal` each use `.date()` and should count two evidence days, despite one local-day interpretation. That is existing behavior to CHARACTERIZE, not a clinical recommendation or requirement.
- **Adversarial episode oracle:** a reused UUID with pre/post separated by two days and 15 minutes remains descriptively paired in current product semantics; elapsed minutes and no-causality limitation preserved. No arbitrary meal timing threshold introduced.
- **New test:** `backend/diabetes/tests/test_v1_01_evidence_day_boundaries.py`, four database-backed cases including patient isolation, UTC+01 counterexample, explicit episode linking, and separations. **Pending CI exact-head; do not count as passing until logs verified.**
- **Gate:** clinical/product reviewer must approve canonical interpretation of a `day` (UTC, patient timezone, sensor timezone, or source-local timezone) and any episode validity policy before changing grades/status or adding duration cutoffs. Current classifications are descriptive evidence density, not clinical confidence or therapy guidance.

## V1-01 CAL-07 — unit-pref mid-edit clinical integrity (2026-10-09 candidate)

- **BEFORE from live source:** `EditLogScreen` displays an original `69.9 mg/dL` value as `3.9 mmol/L`, then rebuilds `_actionButtons(unit)` and the suffix from `context.watch<PatientProfileData?>`. If profile preference changes before Save, `3.9` can be treated as **3.9 mg/dL**, not the original 69.9. This is a code-path finding; no real patient event asserted.
- **Goal/acceptance:** the glucose unit and number in an open edit form remain bound together for its entire life, even when the shared profile changes; saving unchanged must store **69.9 mg/dL**, while editing displayed value to **4.0 mmol/L** must store **72.064 mg/dL**. Inputs with an unsupported unit must fail closed, never silently reinterpret as mg/dL. No altered clinical thresholds.
- **Candidate implementation:** `EditLogScreen.build` uses the loaded `_initialUnit` snapshot rather than following the live profile preference; Add/Edit write paths validate `GlucoseFormatter.isSupportedUnit`; `toMgDl` and `editedToMgDl` throw for unknown units.
- **Tests pending exact-head:** actual Drift in-memory edit screen at **390×844 and 768×1024**, both unchanged and explicitly modified after a simulated profile preference change; assert numeric value, suffix, low-alert behavior and actual stored mg/dL. Independent formatter unit tests reject unknown units. These widget assertions exercise live widget layout but **are not comparative Chrome PNG captures**; screenshot proof of the dynamic profile switch remains outstanding for V1-01 final UI certification.
- **Gate:** no patient production, no merge, no Vercel; CAL-07 and #22 remain OPEN until downstream consumers, independent medical/UX reviews, UI screenshots and postmerge.

## V1-01 CAL-07: new-entry unit preference switch — candidate 2026-10-09
- BEFORE: AddLogSheet bound suffix/calculation to the live profile preference while a typed glucose value persisted. Switching a profile from mmol/L to mg/dL after entering 4.0 could silently reinterpret it as 4.0 mg/dL.
- Candidate: lock _draftGlucoseUnit once a non-empty value is typed; release lock on clearing/reset/new receipt. Do not change patient thresholds, diagnoses or treatment decisions.
- Tests pending exact-head: two true Drift widget saves (390×844, 768×1024) confirm that 4.0 mmol/L remains 72.064 mg/dL after a profile preference change, without a misleading low-glucose warning. UI proof workflow now captures both Add and Edit unit-switch states, four BEFORE plus four AFTER Flutter screenshot PNGs at identical viewports and synthetic source.
- Former HEAD f061910 had a Flutter analyzer failure because a test awaited the void-returning testTextInput.hide; removed await in the same commit. Clinical and visual certification of V1-01 remain OPEN.

## V1-01 CAL-07 — evidence pivot to actual Flutter Web / Chrome (2026-10-09)

- **Two widget-test screenshot workflow attempts failed** for non-product reasons: the first timed out after producing a PNG during widget teardown (guarded function conflict); the retry fixed teardown but the isolated screenshot environment was missing during the general Flutter suite, causing four failures even though 662 other tests passed. Backend Ruff+pytest and PostgreSQL were green on that HEAD.
- **Runtime test fix:** the general Flutter suite now performs all unit-switch/Drift assertions without requiring `IAMINA_V101_PROOF_DIR`. Visual evidence is generated independently.
- **New actual-browser fixture:** `frontend/lib/v1_01_unit_switch_browser_main.dart` is a test-only Flutter Web entrypoint using real AddLogSheet and EditLogScreen, a synthetic mmol/L profile and 69.9 mg/dL reading. When input exists, it changes the profile preference to mg/dL without changing the displayed numeric value and signals a post-render milestone.
- **New screenshot workflow:** `.github/workflows/ui-v1-01-edit-unit-switch-visual.yml` compiles baseline AddLog/EditLog/GlucoseFormatter code at `a1ee417`, captures Chrome screenshots at 390×844 and 768×1024, then restores exact PR HEAD and captures the same four states. Tool `tools/v1_01_unit_switch_browser_capture.cjs` checks renderer presence, screenshot completeness; workflow checks eight PNG signatures/dimensions and changed bytes. **Not yet executed/inspected at candidate HEAD.**
- Clinical limit: this does not yet fix Profile target-range mg/dL unit display/entry conversion. #22 remains OPEN, as do independent clinical reviewers and merge/post-merge. No patient data or Vercel.

## V1-01 CAL-07 / decision #22 — Profile target unit storage repair candidate (2026-10-09)

- **BEFORE code:** ProfileScreen loaded canonical mg/dL `targetRangeLow/High` directly as text irrespective of the profile unit, exposed target controls before unit selection and wrote parsed target text as mg/dL without normalization. Under mmol/L this mislabels and can dangerously store small mmol/L numerals as mg/dL target thresholds. Confirmed by source inspection, not by a real patient incident.
- **Goal:** choose glucose unit before target range; display values in selected unit, but store canonical mg/dL. Preserve original canonical values during unchanged edits and multiple unit toggles to avoid drift at `69.9 mg/dL`. Fail closed when saved preference is unknown or typed target is invalid. No change to hard-coded clinical target thresholds.
- **Candidate fix:** ProfileScreen snapshots canonical low/high and last displayed rounded values. It reads edits through `GlucoseFormatter.editedToMgDl`, converts while changing unit only after validating pending input, synchronizes controller text and unit labels, and persists canonical mg/dL. Profile presentation puts unit selector before target fields. Tests at 390×844 and 768×1024 cover exact 69.9/180 roundtrip and edited 4.0/10.5 mmol/L → 72.064/189.168 mg/dL using real Drift. A negative widget test verifies a persisted unsupported unit cannot overwrite target values. **Do not mark tests as passing until exact-head CI is observed.**
- **UI/UX visual gate:** no before/after same viewport captures of the Profile target panel yet; separate from the AddLog/EditLog Chrome comparison. Independent clinical/UX review and full V1-01 closeout required. No merge/patient pilot/Vercel.

## 2026-10-09 V1-01 CAL-07 — exact mobile overflow and browser-profile proof follow-up

- **Before facts on `f208feb`:** 15/17 GitHub workflows success, CI `#37964165514` FAIL with 668 passed/1 failed/1 skipped. Real horizontal RenderFlex had width 304 px and child edge 418 px (+114) at 390×844 in a Profile ExpansionTile offstage subtree. Canonical target values persisted as expected in Drift assertions; the failing assertion was only a layout overflow, not a changed clinical calculation.
- **Candidate responsive fix `4286010`:** section title in Profile `_buildSectionTitle` becomes `Flexible(Text(softWrap: true))` so the icon/title row can wrap on narrow layouts. The title `l10n.glucoseTarget` now reflects the currently selected unit instead of always printing `mg/dL`. Existing 390×844 test still requires `tester.takeException() == null` and same storage oracle. Do not infer success without new exact-head CI.
- **Before Chrome failure:** [#37964165240](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37964165240) failed BEFORE on the experimental `ui_browser_audit_main.dart` Profile fixture; fixture had no usable seeded Profile and emitted a browser `undefined.update` error, so there is no valid Profile BEFORE/AFTER evidence from that run. **This is a harness failure, not a clinical product failure.**
- **Strategy adjustment:** restore the already proven cross-surface dashboard/Reports Chrome script and its test-only browser entrypoint to their pre-Profile-extension content. Add real ProfileScreen to the separately successful isolated `v1_01_unit_switch_browser_main.dart`, seed a complete synthetic profile with unit mmol/L and exact canonical low/high 69.9/180 mg/dL; compare the real old and new Profile UI at 390×844 and 768×1024. The real browser captures EditLog/AddLog/Profile: **12 total PNG** (BEFORE/AFTER × three screens × two viewports) with screenshot integrity and expected target unit title checks.
- **Review gates still open:** independent medical + accessibility/RTL review, V1-04 country/onboarding unit-first workflow, full CAL-01…12 closure, GitHub merge/postmerge. No production patient data or Vercel deployment.

## 2026-10-09 — V1-01 unit-switch visual proof: Flutter CanvasKit semantics correction

- **Exact-head result on `8cac30c`:** **16/17 GitHub workflows SUCCESS**, including main CI `#37967580068` and glucose cross-surface real Chrome `#37967579790`. Only `V1-01 edit glucose unit switch visual proof #37967579947` failed during BEFORE Profile capture: Playwright `getByText('Suivi médical')` timed out after it had saved four BEFORE EditLog/AddLog PNGs. Flutter CanvasKit does not expose the canvas text as a stable HTML text locator; **not a product render or numerical integrity regression**.
- **Next candidate test-harness-only:** drive the actual Flutter medical `ExpansionTile` via its built `ListTile.onTap` in the isolated synthetic web entrypoint, wait for the true `AminaTextField` controllers and actual `Cible glycémique` title, print the observed values to the browser log, and require the Playwright runner to independently assert BEFORE `70/180 mg/dL` against AFTER `3.9/10.0 mmol/L`. Capture 12 screenshot PNGs at 390×844 and 768×1024, same source and layouts. No product runtime changes, no schema or clinical thresholds changed. **Exact-head rerun required before claiming success**.

## 2026-10-09 exact-head closeout of unit-entry substep only (not V1-01)

**Source of truth:** [PR #920, HEAD b0e971e8d087dca9cd73023a5bc7afd57f420096](https://github.com/hraaaaf/IAMINA-MVP/pull/920), OPEN/DRAFT, main baseline 13b7cce12c86daf60119fb703f22e8c6c192cf8d.

**Goal:** a glucose number must not silently change units when the profile preference changes during AddLog/EditLog, and editable target ranges must display selected units while remaining canonical mg/dL in storage. No unsupported normative TIR/GMI or fabricated CGM AGP for manual-only samples.

**Executed proof on exact SHA b0e971e:**
- **17/17 GitHub workflows SUCCESS**, no failed/pending, including [CI #37969874153](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874153), [real Chrome glucose cross-surface #37969874258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874258), and [real Chrome AddLog/EditLog/Profile before/after #37969874302](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874302). PostgreSQL, Flutter/Drift and API contracts pass within the scope of their test fixtures; not proof of deployed patient safety.
- **12 real Chrome PNGs downloaded and visually inspected** from [artifact #11635771127](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874302/artifacts/11635771127): AddLog, EditLog and actual ProfileScreen, BEFORE and AFTER at 390×844 and 768×1024. Profile BEFORE shows 70/180 under mg/dL title, AFTER 3.9/10.0 under mmol/L title; the selected unit now precedes target fields. No visible horizontal clipping in these states. EditLog binds 3.9 to mmol/L and AddLog 4.0 to mmol/L despite a synthetic live profile preference change; AddLog no longer shows false low-glucose warning.
- **Pixel cross-check, max RGB channel delta > 12:** EditLog 390/768 = 309/309 changed pixels; AddLog 390/768 = 69,165/57,815; Profile 390/768 = 16,615/16,496. Images are dimension-matched; timestamp in AddLog also varied, so not every pixel difference is caused by the unit fix.
- **Visual-quality provisional 8/10 on these six FR before/after pairs only.** No Chrome Arabic RTL, real patient UI review, accessibility score, or full clinical certification.
- **Tested canonical target values in widget/Drift:** unchanged 69.9/180 mg/dL survives unit changes; edited 4.0/10.5 mmol/L persists 72.064/189.168 mg/dL using active 18.016 write factor. Active backend write and shared Flutter display both use **18.016** on this exact HEAD, supported independently by the Flutter conversion regression tests. Earlier audit wording claiming Flutter still used 18.018 or active Home/Reports still used 18.0 was HISTORICAL and is no longer accurate; Home/Reports use the shared formatter. The only directly inspected divergent conversion helper is the retained legacy backend unit_guard.py (18.018), whose patient-path reachability remains UNPROVEN. Keep **legacy reachability, aliases, and final approved factor policy** open; do not claim an active cross-layer discrepancy without a reachable consumer.

**Outstanding CAL gates:** complete CAL-01…12 source-to-consumer register and independent numeric oracles; independent clinical and security/UX reviewers; Arabic RTL and accessibility; actual country→unit→target onboarding in V1-04; patient-local time-zone contract for CAL-09/10 evidence days; CAL-11 source provenance and CAL-12 exports/LLM claims. No merge before independent approvals or Vercel deployment without explicit authorization.

**29-decision tracking:** 0/29 fully delivered, #19/#22/#28 IN PROGRESS, 26/29 not started in V1. Unit-entry substep passing does not mark #22 delivered.

**Next exact:** prove or refute reachability of retained backend/diabetes/services/clinical/unit_guard.py (legacy 18.018 and unknown-unit default), then independently validate current 18.016 display/write rounding and historical active-route elimination with authoritative boundary oracles. Fix only reachable discrepancies; complete CAL-01…12 registry and independent review.
