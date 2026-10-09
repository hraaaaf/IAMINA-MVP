# V1-01 — Calculation & clinical-authority inventory (working audit)

> Status: **OPEN / INITIAL STATIC PASS**, not a complete calculation inventory, clinical certification, or runtime validation.
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
| CAL-02 | Public KPI API | `backend/diabetes/api/v1/kpis.py` -> `compute_kpis` -> `assess_cgm_window` -> `compute_verified_cgm_metrics` -> `project_public_kpis` | `evidence_projection.py` suppresses normative CGM fields unless provenance, covered session and registry authorize them | Source inspected; live/API negative tests PENDING |
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

- **RISK-01 (P0 investigation): KPI cache alias.** `backend/diabetes/api/v1/kpis.py` forms key suffixes with `int(target_low)`/`int(target_high)`. Numerically distinct requested ranges can share one patient/window cache key. Reproduce with fractional low/high and assert cache does not return metrics computed for another range; inspect whether public callers can pass such ranges. Do not change caching until a regression test proves the intended contract.
- **RISK-02 (P1 investigation): semantic mislabel.** Raw SQL fields named `tir_pct` are fractions of rows, while true CGM TIR requires verified sensor-session coverage. The inspected KPI API uses `evidence_projection` to fail closed, and the inspected dashboard widget says recorded readings. Audit *all other* consumers (`compute_trend`, analysis summaries, exports, alerts) before claiming a leak.
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
