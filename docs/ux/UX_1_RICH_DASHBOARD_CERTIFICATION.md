# UX-1 — Populated Dashboard rich-state certification

> LOT: UX-1 — populated Dashboard locale parity + hierarchy
> PR: #84
> Baseline date: 2026-08-10
> This file records certification evidence only. `docs/ROADMAP.md` remains the single forward tracker.

## Baseline

Fresh UX-0 rendered evidence exposed a product state that the historical empty/first-use Dashboard matrix did not exercise:

- run `31403179971` — SUCCESS;
- artifact `9068596037`;
- 8/8 FR/AR renders across `1440×1000`, `768×1024`, `390×844`, `360×560`;
- zero page errors;
- populated Dashboard cross-locale score **8.4/10 — CHANGES REQUIRED**.

Blocking finding: raw canonical meal IDs such as `dinner` and hard-coded French rich-state strings appeared in Arabic Hero/KPI/chart/insight surfaces.

## Remediation contract

UX-1 is deliberately limited to populated Dashboard presentation.

Delivered:

- canonical and legacy meal/context identifiers are mapped to localized patient-facing labels before display;
- Hero, GMI, CV, AGP, event, insight and recent-entry rich states use FR/EN/AR localization;
- RTL directional placement is preserved;
- no clinical formula, threshold, eligibility rule, target band, persistence behavior, API contract or patient-data semantics changed;
- no diagnosis, dose calculation, treatment recommendation, causal claim or treatment optimization was introduced;
- permanent UX-1 locale regression coverage prevents known hard-coded French rich-state residues from returning;
- the existing clinical explainability contract now verifies GMI/CV truthfulness through localized FR/EN/AR corpus rather than requiring French literals inside widget source.

## Validation

Runtime/test head `2b1483fb89b6dcbb6885f017085a98b48d0d7e76`:

- CI #1449 — SUCCESS, including complete Flutter suite and PostgreSQL source-of-truth;
- Django migration drift #1261 — SUCCESS.

Rendered remediation evidence:

1. run `31407376293` — SUCCESS;
   - artifact `9070305707`;
   - digest `sha256:ea150de67056d74d6209ea3d862445d1235aaf9084e7f0b4ff971a23e604d`;
   - 32 FR/AR top/mid/lower/full captures;
   - zero page errors.
2. run `31408059463` — SUCCESS;
   - artifact `9070602793`;
   - digest `sha256:13d13788927edd5e29cafe5915b6ed2a33cb7fdadc92599b8aac680abbc5e2b7`;
   - product source `1f4cb1c34e8b4eb47e3bdaef1f22a693bc61753d`;
   - 24/24 FR/AR top/mid/lower captures;
   - zero page errors.
3. run `31408987292` — SUCCESS;
   - artifact `9070877958`;
   - digest `sha256:32bd9febba08e6a0c44d8378f69d91d133bef46513460c487f6052be97d5832c`;
   - product source `48d1eeb69ade2c5ca5846e2e144424b3132cdf0a`;
   - 24/24 FR/AR top/mid/lower captures across the full viewport matrix;
   - one Flutter view per capture and zero page errors.

## Independent review

### UX Auditor

**PASS — 9.2/10.**

The raw `dinner` leak and mixed-language Arabic rich-state defect are removed. Hero → KPI → AGP/events/insights hierarchy remains stable, RTL is coherent and no blocking overlap is visible at 390×844 or 360×560. Long AGP/GMI headings may ellipsize on the hostile 360×560 viewport but remain identifiable and non-blocking.

### Clinical Safety Reviewer

**PASS.**

GMI and CV calculations are unchanged. GMI continues to disclose method/coverage and laboratory limitation; CV remains framed as a general reference rather than a personalized success target. No new diagnosis, prescription, dose logic, causal claim or treatment optimization is introduced. This technical review does not replace the separate native-language/safety-corpus gates tracked under P0-MENA-2.

## Final closure

UX-1 is **100% closed**.

- exact final PR head: `27ee9b00c2326add7642bb0f544f5658ebf4d949`;
- CI #1452 — SUCCESS;
- migration drift #1264 — SUCCESS;
- final visual run `31409668306` — SUCCESS;
- artifact `9071144760`;
- digest `sha256:fb2490f8a4d293206917adbcfb56dbc57c24a49f67a61f27eea3a9db391e088f`;
- 24/24 FR/AR rendered views, one Flutter view each, zero page errors;
- UX Auditor FINAL PASS — **9.2/10**;
- Clinical Safety Reviewer FINAL PASS;
- Release Certifier — CERTIFIED;
- PR #84 merged with expected-head locking as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`;
- post-merge CI #1453 — SUCCESS;
- post-merge migration drift #1265 — SUCCESS.

No further visual remediation LOT is implied by this closeout. A new UX LOT requires fresh rendered evidence at <=9.0/10 or a new product requirement that changes a certified surface.
