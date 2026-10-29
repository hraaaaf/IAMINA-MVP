# D19 — Calculations and clinical authority, Web/PWA (2026-10-29)

**Status: IN PROGRESS — not clinically certified.**
**Baseline:** `main@07477defc3ad7f99fc5186b13008627865e88156`.
**Prior research / unmerged candidate:** [PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920), `docs/assessments/2026-10-09-v1-01-calculation-authority-audit.md` on `audit/v1-01-calculation-authority-20261009`. Do not cherry-pick or merge the 59-file historical PR wholesale.

## Goal / success / proof

**Goal:** only measurements with validated unit, source, patient identity, window and sufficiency may acquire clinical/normative labels across API, Web screens, reports and AI. Manual samples must never masquerade as verified CGM time in range or GMI.

**Success:** CAL-01…12 producer → authorization → consumer inventory, deterministic negative oracles on SQLite/PostgreSQL and Flutter Web, model-output safety; qualified independent clinician and privacy/security review. No patient data or live account required for engineering tests. No medical target is invented or changed by this audit.

## Verified current-main findings

1. **CAL-01 cache collision (confirmed source defect).**
   `backend/diabetes/api/v1/kpis.py::_kpi_cache_key` on main uses `int(target_low)` / `int(target_high)`, so for one patient and period target lows 70.1 and 70.9 share a key. Distinct clinical inputs may receive a cached result computed for another target.
   **Isolated fix**: `float(... )!r` per bound; identical values share a key, fractional values do not. Adopted from previously tested limited patch in PR #920, not automatically merged. New negative tests `backend/diabetes/tests/test_d19_fractional_target_cache.py` cover low/high distinctions, patient/period isolation and two separate endpoint calculations. **No threshold changed**.
2. **CAL-02 AI summary claim authority (confirmed source gap).**
   `backend/ai/api/v1/ai.py::get_summary` in current main serializes `compute_kpis` raw `tir_pct`, `tar_pct`, `tbr_pct`, `cv_pct` and `gmi` directly, whereas `backend/diabetes/api/v1/kpis.py::get_kpis` already gates normative metrics using verified CGM sufficiency. Thus equivalent manual/mixed data can be labeled differently by distinct public endpoints. **Not fixed by the cache change**.
3. **CAL-12 AI Doctor Brief claim boundary (confirmed source gap).**
   `get_doctor_brief` in main builds prompt statistics directly from raw `compute_kpis`, then returns free-form `narrative`, `key_insight`, `doctor_brief` from LLM after a prescription-pattern filter. A source/provenance allowlist for every returned number is not established. Historical PR #920 contains a deterministic `consultation-brief.v1` projection with additional tests, but remains DRAFT and requires independent clinical review before adoption.
4. **CAL-07 unit mismatch to reconcile (verified source divergence).**
   Main Flutter `GlucoseFormatter.mgdlToMmolFactor = 18.018`; historic PR #920 uses `18.016`, and main legacy backend unit guard cites `18.018`. **No conversion factor has been changed here**; reconcile authoritative normalization, rounding and cross-surface contracts before a clinical decision.
5. **CAL-03–06/08–11 still require exact producer→consumer oracles.**
   Preserve manual descriptive vs CGM-verified semantics, patient-scoped windows and optional target context, including timezone/meal pairing, FR/AR/RTL typography, food provenance and typed PDF output. The previous 12-row audit is a starting inventory, not a completed certification.

## First isolated lot — CAL-01

- Branch `audit/d19-web-clinical-authority-20261029` from main; no Production deploy.
- Changes confined to `backend/diabetes/api/v1/kpis.py`, independent synthetic tests and isolated CI. Preserve standard 70/180 config (existing constants only; **not** a clinical recommendation to an individual).
- CI: [D19 isolated Actions workflow](https://github.com/hraaaaf/IAMINA-MVP/actions/workflows/d19-clinical-authority-ci.yml) — **result must be verified before labeling PASS**.
- Decision: never merge clinical calculation changes without qualified review / authorization.

## Next critical path

1. Verify and repair CAL-01 isolated CI; add PostgreSQL parity before claiming complete calculation correctness.
2. Add failing negative synthetic manual-only tests for `/ai/summary` and Doctor Brief final response; port smallest vetted authority/projection patch from #920 only with matching API/schema and review.
3. Trace CAL-01…12 across Web Home/Reports/AI and missing-data cases; no borrowed CGM coverage.
4. Independent medical reviewer (sufficiency labels, units, thresholds, localized claims) + security/privacy/egress reviewer — **human gate**.
5. Candidate PR/merge only with explicit approval and separate Vercel authorization; post-merge exact-SHA CI.

**Scope:** Web/PWA, synthetic data, no clinical/patient enrollment, no Neon writes, no Production.
