# IAMINA D19 — RISK-02: AI-summary CGM metric authority (2026-10-29)

**Status: CANDIDATE / DRAFT / NOT_VERIFIED / NO_RELEASE.** This assessment describes the scoped fix, not all of D19. No clinical approval, patient deployment, consent-bypass authorization or verified production use.

## Goal, success, proof
- **Goal:** `POST /api/v1/ai/summary` must not present manually recorded glucose statistics as clinically validated CGM metrics, nor pass those raw metric values to any AI narration step.
- **Success:** public CGM TIR/TAR/TBR/CV come only from verified patient- and session-linked readings through the same governed projection used by `GET /api/v1/kpis/`; GMI stays unavailable if registry authority does not promote it; unverified hourly AGP is not published.
- **Proof required:** exact-HEAD SQLite and PostgreSQL regression CI, source diff, no Vercel deployment, security/clinical review, and the full D19 Web FUE before any D19 decision closure.

## Exact candidate
- Repository: `hraaaaf/IAMINA-MVP`.
- Starting main: `a9dad08a5cfd4dc2f31f2cb35a1d72eb84aeb8e0`. The base advanced independently during work; reconcile before any eventual merge.
- Branch: `fix/d19-summary-cgm-authority-20261029`.
- Functionality commit: `e91761c9aa89af743047d0f150707d57b94403df`.
- Last backend-tested code SHA: `afbe55a0eba9ebadc9c3baf48fba9e72665dd1ec` (two legacy API assertions updated to the fail-closed CGM contract).
- Open PR: [#1185](https://github.com/hraaaaf/IAMINA-MVP/pull/1185), DRAFT.
- Paths: `backend/ai/api/v1/ai.py`, `backend/diabetes/api/v1/kpis.py`, `backend/diabetes/tests/test_d19_summary_cgm_authority.py`, `backend/diabetes/tests/test_api.py` (two existing assertions updated) and this assessment. No frontend change, schema migration, new clinical thresholds, new model egress route, or patient mutation.

## Before / target / implementation
**BEFORE (source verified):** `/kpis/` assessed verified CGM windows and recomputed metrics from `CGMReadingRecord`; `/ai/summary` directly returned `compute_kpis()`'s row-derived CV/TIR/TAR/TBR/GMI. The SQL AGP helper was also called regardless of sensor eligibility, while the narrator was built from those same raw KPI fields.

**TARGET:** use the pre-existing `assess_cgm_window` + `compute_verified_cgm_metrics` + `project_public_kpis` contract for both public endpoints. Keep descriptively recorded values separate from normative CGM claims. Do not promote additional clinical thresholds.

**IMPLEMENTED candidate:** `project_patient_kpis` extracts the existing `/kpis/` governed projection, reused by `/ai/summary`. The summary builds a separate immutable descriptive-only analytics snapshot for pattern generation and narrator compression (CGM normative values and row-provenance fraction withheld). The response includes only public projected KPI fields. Legacy row-based AGP is fail-closed to an empty list until a separately proven sensor-based AGP exists. Daily recorded-glucose averages remain descriptive.

**Deliberate limitation:** even if a verified CGM session permits a public TIR/CV field, the narrator is kept descriptive only for this sublot. Introducing safe CGM-verified narration or a real sensor AGP is a different reviewed change, not a reason to leak row-based metrics.

## Scenario-to-evidence matrix

| ID | Scenario | Expected candidate behavior | Evidence status |
| --- | --- | --- | --- |
| R2-01 | 60 synthetic manual readings, 14 days | Public GMI/TIR/TAR/TBR/CV and confidence null, no raw CGM claims in generated AI pivot, descriptive mean retained, AGP absent | PASS synthetic automated regression at `afbe55a0`; NOT a Web FUE |
| R2-02 | Verified synthetic CGM session | Public TIR/TAR/TBR/CV recomputed from sensor records, not SQL row fractions; GMI remains unpromoted; no unsupported narration | PASS synthetic automated regression at `afbe55a0`; NOT a Web FUE |
| R2-03 | Verified session, non-standard target interval | No promotion of normative CGM percentages and no sensor metric function call | PASS synthetic automated regression at `afbe55a0`; NOT a Web FUE |
| R2-04 | Cross-patient session ownership | Sensor qualification receives the authenticated user's ID | Argument checked in test; full A/B browser isolation NOT_RUN |
| R2-05 | AI data egress and consent | Existing consent/evidence decorator unchanged; no real LLM invoked by synthetic unit tests | Static diff only; full security/consent verification NOT_RUN |
| R2-06 | Authenticated real Web FR/AR/RTL, 390×844 / 768×1024 / 1280×900 | Patient-facing result, keyboard, refresh, error/empty/recovery states safe in all locales | NOT_RUN |
| R2-07 | Clinician/privacy independent review | Accept description-vs-CGM distinction, sensor ownership and missingness policy | NOT_RUN |

**FUE verdict:** NOT_RUN / NO_GO for D19 as a whole. Unit and CI proofs cannot replace a complete Web FUE or qualified clinical/privacy review.

## Critical risks, boundaries and follow-up
1. The `summary` route remains protected by the pre-existing `patient_ai_egress_scope`; the patch must not be interpreted as consent or backend production certification.
2. The code still contains other historical analytics and reporting consumers; this sublot only resolves `/ai/summary` projection/narration and legacy AGP on that route.
3. `GET /kpis/` response semantics must remain unchanged by moving its existing evidence calculation into a shared helper.
4. The separate fractional cache-key correction [#1183](https://github.com/hraaaaf/IAMINA-MVP/pull/1183) is DRAFT, intentionally not included. Both branches touch `kpis.py`; they must be reconciled explicitly and retested on a resulting exact HEAD, not merged wholesale.
5. The authoritative clinical factor/rounding, D19 CAL-01 through CAL-12 and D22 unit UI remain outside this sublot.

## Release gate and continuation
**No merge / no Vercel deployment without explicit separate owner approval and required risk gates.** Current proof and scoring stay provisional until CI is final; do not mark D19 completed.

**Next exact:** inspect exact-HEAD CI failures/success, correct observed regressions, rerun when SHA changes, perform adversarial clinical/privacy review and D19 Web FUE, record scores and closeout only to the level proven. Continue no-deploy preparation of the next independent D19 regression only after these checks.

## Evidence update: exact code SHA `afbe55a0` — 2026-10-29

**Prior RED diagnosed:** code SHA `e91761c9` failed two old integration tests asserting TAR/TBR percentages after a *single manually recorded* high/low glucose reading. That old expectation confuses sampled fractions with CGM time-exposure metrics. The expected result was corrected in two tests without restoring unsafe CGM promotion. Commit `afbe55a0` changes only these assertions: `log_count=1`, no statistically sufficient record, TAR/TBR/GMI public fields null.

**Passed on `afbe55a0`:**
- [CI #40859236279](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859236279) COMPLETED/SUCCESS: Ruff, Django tests, import-linter, AI egress anti-bypass, Bandit, OpenAPI, secret hygiene.
- Django/SQLite logs: **2866 passed, 5 skipped, 3 xfailed, 127 subtests passed, 11 warnings**.
- PostgreSQL logs: **2870 passed, 1 skipped, 3 xfailed, 127 subtests passed, 11 warnings**.
- [Django migration drift #40859236278](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859236278) COMPLETED/SUCCESS.
- [Companion real chat E2E screenshots #40859236285](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859236285) COMPLETED/SUCCESS. This workflow does **not** independently prove real patient Web FUE, all FR/AR languages, or clinical endorsement.
- Neither Vercel frontend nor backend has a deployment associated with `afbe55a0` at inspection. **No deployment requested.**

**Clinical documentation cross-check (no new thresholds):**
- [ADA Standards of Care in Diabetes—2026, section 6](https://doi.org/10.2337/dc26-s006): CGM TIR is assessed from sensor use and coverage; supports preserving a CGM-specific eligibility gate.
- [International Consensus on Time in Range (Diabetes Care 2019)](https://diabetesjournals.org/care/article-pdf/42/8/1593/529329/dci190028.pdf): standardized TIR/TAR/TBR, GMI and AGP are CGM-report metrics, not a label automatically justified by isolated fingerstick rows.
- These primary sources validate the general source distinction, **not** a per-patient clinical target or release certification.

### Quality gate and verdict
- Engineering implementation/exact code SHA: **PASS** for the scoped test suite.
- Clinical, privacy, cross-account, mixed input ownership, consent E2E, full D19 Web FR/AR/RTL responsive FUE: **NOT_RUN / OPEN**.
- **Execution score: 8.8/10 (provisional). Adversarial score: 8.5/10 (same executor), gap 0.3. Retained score: 7.9/10 under missing required evidence cap. Status: NOT_VERIFIED / NO_GO for a completed D19 decision.** Scores are not proof of deployment readiness.
- The mandatory Perfection Pass and all release gates remain open. Technical test success is not approval to merge or deploy.
- Final document-only HEAD after this amendment requires its own GitHub CI; the above backend results are strictly for code SHA `afbe55a0`.

**Next exact:** verify doc-only CI/HEAD, inspect PR scope and any red checks, then obtain qualified clinical/privacy review and real Web FUE before requesting separate release/merge authorization. Keep [#1183](https://github.com/hraaaaf/IAMINA-MVP/pull/1183) independent until explicitly reconciled.

## GO for test-only previews and Web FUE — 2026-10-29

**Owner authorization scope:** the user said GO after a request for an isolated Web D19 preview/FUE. This permits preview testing only. **It does not authorize production deployment, merge to main, real patient data mutation or clinical approval.**

### Deployments and safety checks
- Source branch: `fix/d19-summary-cgm-authority-20261029`. No merge.
- Backend manual preview `dpl_6MysgCN7a2t6CYYyRuf9UAjTjKjx`, unique URL `https://iamina-certified-piipzaklj-achraf-benmoussa-s-projects.vercel.app`, code/commit `74bd735d71a47e09f14b6b16da2a0400c002c652`, state READY. Later commits touch frontend and this assessment, not backend clinical implementation. The backend remains protected with Vercel auth.
- Frontend manual BEFORE preview `dpl_DwbN2J9XjhWpdbEzGnGnngdSoj3b`, URL `https://iamina-review-4iyfq2ibu-achraf-benmoussa-s-projects.vercel.app`, commit `74bd735d`, READY.
- Frontend manual AFTER preview `dpl_FDWErTGt6pCSCfv7hUh5EnmYZUEo`, URL `https://iamina-review-7wsqhqjzu-achraf-benmoussa-s-projects.vercel.app`, code SHA `85426e4ff4cfc9cc3d9febef64d8e23f9a67a6fc`, READY.
- Preview-specific, Git-branch-scoped `IAMINA_REVIEW_PREVIEW_API_BASE_URL` points to the exact backend deployment instead of the stable/production backend alias. Production project settings/aliases unchanged. Vercel preview DB expected host/DB/role are distinct from production; `/api/v1/health` on the backend preview returned HTTP 200 `{"status":"ok","db":"ok","cache":"unavailable"}`. This proves DB connectivity, **not** a clinical data isolation audit or cache correctness. Authenticated KPI retrieval was blocked at Vercel Authentication; no patient data accessed. No real patient inputs, external AI calls or credential enrollment used.
- CI and browser evidence for AFTER code SHA `85426e4f`: **7/7 completed SUCCESS** — CI #40864022496 (backend/PG and Flutter/PWA); migration drift #40864022588; UI geometry golden #40864022468; P5-5 rehearsal #40864022512; Companion browser E2E #40864022560; first-use visual #40864022665; browser screenshot certification #40864022552. Flutter job log explicitly shows **835 tests passed / 1 skipped**, PWA build present. The browser screenshot workflow generated actual PNG artifacts for synthetic patient surfaces at **390×844, 768×1024, 1280×900**. These are NOT authenticated AI-summary API journeys.

### Web UI safety finding found by independent execution, not a release certification
**BEFORE source observation:** `frontend/lib/features/journal/ai_summary_screen_presentation.dart` displayed normatively phrased KPI cards using `kpis.tirPct ?? 0.0`, `kpis.gmi ?? 0.0` and `kpis.cvPct ?? 0.0`; the AGP widget could use `summary.dailyAverages` even though they were not a verified CGM time series; the hero selected an unfavorable TIR assessment when TIR was absent. These violate the D19 fail-closed clinical presentation contract.

**Written target/mockup:** when a normative CGM metric is unavailable, show no corresponding numeric card and never claim 0%; show neutral `insufficientData` text in the hero when CGM TIR unknown; show an AGP card only if an actual `summary.agpProfile` is supplied and public TIR/TAR/TBR are verified. Preserve existing layout, spacing, colors and localization strings.

**AFTER implementation:** commits `0518b65e` (Flutter presentation fix), `d5096ec9` (three Flutter regression contract tests), `85426e4f` (type promotion for nullable widget reference). No clinical thresholds changed. Unit/CI build proof **PASS** on `85426e4f`; dynamic patient scenario remains to prove.

**BEFORE browser observation:** [TinyFish before run](https://agent.tinyfish.ai/runs/9d54ed85-7af4-4f1c-8758-9b51326a884f): protected preview was accessible; actual first-use page displayed in English with 'Continue without an account', but navigation to `#/login` left an empty canvas in that run. FR/AR and AI Summary unavailable to the browser tool. No fixed-viewport BEFORE screenshots of the D19 AI-summary feature. This observation alone is not conclusive evidence of a product bug.

**AFTER browser observation:** [TinyFish after run](https://agent.tinyfish.ai/runs/fda799e8-7a28-4d8e-a26b-a8f3da215c46): first-use page rendered, but browser automation was unable to advance via 'Continue without an account'; state remained at `#/login`, and the actual AI-summary screen, FR/AR/RTL, KPI absence/recovery and synthetic cross-account flows remained **UNREACHED**. The cause could be Flutter canvas interaction, app lock or a real application issue; **not diagnosed**. No login or patient data used.

**Visual screenshots examined:** GitHub Actions artifacts `iamina-ui-browser-cert-390x844`, `...-768x1024`, `...-1280x900` from run #40864022552. In the synthetic `summary` surface they render 'Rapport de vos mesures' in French, adaptive card layout, counts and recorded glucose averages with explicit statement 'Ce rapport reste descriptif'. This is a **different screen** from `AISummaryScreen`; do not use as proof that actual AI Summary correctly handles normative null CGM fields at runtime. All three samples were inspected for legibility, but not a complete Target↔Render comparison of D19 because BEFORE AI-summary images are missing.

### FUE gate / final scoped verdict

| Gate | Status |
| --- | --- |
| Backend D19 manual-only/verified CGM/nonstandard target unit and PostgreSQL CI | **PASS** |
| Frontend CGM-null and manual-AGP fail-closed code regression tests / build | **PASS** |
| Web preview deployment on exact code SHA, protected isolated origin | **READY** |
| Backend preview health and declared preview DB config | **HTTP 200 / DB OK**, cache unavailable; isolation runtime partially assessed |
| Synthetic Chrome screenshots 390/768/1280, descriptive report | **PASS / scoped**, not actual AI-summary |
| Real Web D19 AI-summary, FR/AR RTL, keyboard, positive/negative/recovery, account A/B | **NOT_RUN / BLOCKED by navigation** |
| Genuine clinical/privacy review and Perfection Pass | **OPEN** |
| Production merge/deploy | **NO_GO**; no authorization |

**Scores are provisional:** EXECUTION 8.8/10, ADVERSARIAL 8.5/10, retained 7.9/10 due to essential FUE and clinical gates. Do not report 9.0+, 'CERTIFIED', 'production-ready' or 'D19 closed'. No patient-visible production aliases have changed.

**Next exact:** resolve whether the browser click/navigation issue is a genuine first-use regression (reproduce via an authenticated local-only Chrome CDP or inspect browser console), then run real Web D19 AI summary with strictly synthetic sensor/manual data, FR/AR/RTL and user A/B isolation at all three viewports; re-run affected checks/visual Target↔Render, obtain qualified clinical/privacy review; reconcile D19 CAL-01 PR #1183 before any merge request. If a tool/browser cannot reach the patient screen, record FUE as NO_GO, do not replace it with static or isolated screenshot evidence.
