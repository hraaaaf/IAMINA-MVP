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
- Open PR: [#1185](https://github.com/hraaaaf/IAMINA-MVP/pull/1185), DRAFT.
- Paths: `backend/ai/api/v1/ai.py`, `backend/diabetes/api/v1/kpis.py`, `backend/diabetes/tests/test_d19_summary_cgm_authority.py` and this assessment. No frontend change, schema migration, new clinical thresholds, new model egress route, or patient mutation.

## Before / target / implementation
**BEFORE (source verified):** `/kpis/` assessed verified CGM windows and recomputed metrics from `CGMReadingRecord`; `/ai/summary` directly returned `compute_kpis()`'s row-derived CV/TIR/TAR/TBR/GMI. The SQL AGP helper was also called regardless of sensor eligibility, while the narrator was built from those same raw KPI fields.

**TARGET:** use the pre-existing `assess_cgm_window` + `compute_verified_cgm_metrics` + `project_public_kpis` contract for both public endpoints. Keep descriptively recorded values separate from normative CGM claims. Do not promote additional clinical thresholds.

**IMPLEMENTED candidate:** `project_patient_kpis` extracts the existing `/kpis/` governed projection, reused by `/ai/summary`. The summary builds a separate immutable descriptive-only analytics snapshot for pattern generation and narrator compression (CGM normative values and row-provenance fraction withheld). The response includes only public projected KPI fields. Legacy row-based AGP is fail-closed to an empty list until a separately proven sensor-based AGP exists. Daily recorded-glucose averages remain descriptive.

**Deliberate limitation:** even if a verified CGM session permits a public TIR/CV field, the narrator is kept descriptive only for this sublot. Introducing safe CGM-verified narration or a real sensor AGP is a different reviewed change, not a reason to leak row-based metrics.

## Scenario-to-evidence matrix

| ID | Scenario | Expected candidate behavior | Evidence status |
| --- | --- | --- | --- |
| R2-01 | 60 synthetic manual readings, 14 days | Public GMI/TIR/TAR/TBR/CV and confidence null, no raw CGM claims in generated AI pivot, descriptive mean retained, AGP absent | Test authored; exact-HEAD CI pending |
| R2-02 | Verified synthetic CGM session | Public TIR/TAR/TBR/CV recomputed from sensor records, not SQL row fractions; GMI remains unpromoted; no unsupported narration | Test authored; exact-HEAD CI pending |
| R2-03 | Verified session, non-standard target interval | No promotion of normative CGM percentages and no sensor metric function call | Test authored; exact-HEAD CI pending |
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
