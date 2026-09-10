# Dashboard global certification closeout — 2026-09-10

## Status

**ENGINEERING + FINAL RESPONSIVE VISUAL CERTIFICATION PROVEN ON THE CLEAN CLOSEOUT BRANCH; MERGE/POST-MERGE CLOSEOUT PENDING.**

This document records synthetic/non-patient engineering evidence only. It is not real-patient, clinical-human, regulatory, CNDP or deployment approval.

## Goal

Converge IAMINA on one canonical Dashboard implementation and certify its responsive UI, backend wiring and bounded clinical KPI semantics without inventing continuous-CGM evidence.

## Success criteria

1. One production Dashboard authority; legacy `DashboardConvergentScreen` absent from runtime/tests.
2. Responsive evidence at 390×844, 768×1024 and 1280×900, with `top`, `mid` and `lower` captures proven pixel-distinct for every viewport.
3. Real Django backend against isolated PostgreSQL 16 with synthetic non-patient data.
4. Dashboard API contracts return successfully during browser certification.
5. Episodic glucose rows cannot be promoted to governed continuous-CGM metrics without verified coverage/provenance.
6. Browser certification has no page error, no console error and no observed API response >=500.
7. All nine responsive captures are manually reviewed before assigning a final visual score.

## Retained engineering proof

- Original engineering PR: #547, merge `32e04d3de707257a1a08ff28bf6978c4a0e92bfd`.
- Canonical Dashboard route resolves through `DashboardCompanionEntryScreen` to `DashboardPremiumScreen`.
- `frontend/lib/features/dashboard/dashboard_convergent_screen.dart` is removed.
- Django backend + ephemeral PostgreSQL 16 service; synthetic identity/data only; no Supabase.
- Dashboard tests protect latest-reading truthfulness, future-date fail-closed behavior, configured-target behavior, recorded-data KPI semantics, CGM coverage gating, trend factuality, responsive composition, action parity and navigation contracts.
- Backend governed-CGM promotion tests protect the advanced-metric authority boundary.

## Final responsive visual proof

Clean closeout branch: `fix/dashboard-visual-cert-evidence-20260910`.

Certified visual run:

- workflow run: `34535253185` — **SUCCESS**;
- exact visual head: `38e23b3ee0f7203ad9fa6a6903741088f93f2b2b`;
- artifact: `iamina-dashboard-responsive-visual-cert`, id `10175229046`;
- artifact SHA-256 digest: `11dbe42c718cbab9206136823da4a737a41c554280e82ad45f0ae40baae4ee63`;
- all responsive/truthfulness contracts passed;
- canonical Flutter web Dashboard build passed;
- isolated Django + PostgreSQL 16 setup passed;
- no page errors, no console errors and no observed API response >=500 in `browser-report.json`.

The artifact contains exactly the required nine PNGs:

- mobile 390×844: `top`, `mid`, `lower`;
- tablet 768×1024: `top`, `mid`, `lower`;
- desktop 1280×900: `top`, `mid`, `lower`.

Decoded-pixel proof was executed in CI and independently rechecked in RGB. Every pair is distinct:

| Viewport | Pair | Changed pixels | Changed area |
|---|---|---:|---:|
| 390×844 | top ↔ mid | 272,178 | 82.69% |
| 390×844 | mid ↔ lower | 217,611 | 66.11% |
| 390×844 | top ↔ lower | 272,589 | 82.81% |
| 768×1024 | top ↔ mid | 611,263 | 77.73% |
| 768×1024 | mid ↔ lower | 602,773 | 76.65% |
| 768×1024 | top ↔ lower | 658,948 | 83.79% |
| 1280×900 | top ↔ mid | 798,922 | 69.35% |
| 1280×900 | mid ↔ lower | 731,692 | 63.51% |
| 1280×900 | top ↔ lower | 828,197 | 71.89% |

## Harness root cause and correction

Run `34534206725` was a false-negative visual failure. The nine screenshots were genuinely different, but the inline Pillow gate converted screenshots to `RGBA` and then called `getbbox()` on the difference image. Pillow's `Image.getbbox()` defaults `alpha_only=True`; with an alpha channel present, an unchanged alpha plane can therefore make this check unsuitable for deciding whether RGB content changed.

The clean workflow now compares `RGB` images before `ImageChops.difference(...).getbbox()`. The deterministic certification-only scroll path uses an explicit `ScrollController`, waits for content layout to establish a sufficient `maxScrollExtent`, then applies `jumpTo()`. Normal production construction still passes no certification controller.

Primary references:

- Pillow `Image.getbbox`: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.getbbox
- Flutter `ScrollController`: https://api.flutter.dev/flutter/widgets/ScrollController-class.html
- Flutter `ScrollController.jumpTo`: https://api.flutter.dev/flutter/widgets/ScrollController/jumpTo.html
- Flutter adaptive UI guidance: https://docs.flutter.dev/ui/adaptive-responsive/general

The Flutter documentation explicitly notes that scroll metrics such as `maxScrollExtent` are not available until the scrollable has finished laying out its contents. This matches the observed reason the earlier initial-offset-only strategy was insufficient for asynchronously populated Dashboard content.

## TARGET ↔ AFTER review

Reference TARGET is the retained P7 responsive product state in `docs/assessments/2026-08-17-dashboard-p7-responsive-convergence-closeout.md`: one governed Dashboard authority; one canonical brand identity; mobile single-column composition; bounded/adaptive wider layouts; factual recorded-point trend; no invented continuity; same semantic sections across sizes.

Observed AFTER on the final nine-image artifact:

| Viewport | TARGET | AFTER |
|---|---|---|
| 390×844 | Single-column patient flow with bottom navigation and unchanged semantic authority | Met. Header, latest reading, Today, Trend and KPI content remain vertically coherent; no horizontal overflow observed. |
| 768×1024 | Same product authority with navigation adapting to available width | Met. Compact rail and bounded content preserve the same clinical hierarchy and sections without route/product fork. |
| 1280×900 | Bounded wide composition, single identity, efficient multi-column use | Met. Full navigation rail + centered content; Trend/KPI and Insight/Next Action compose side-by-side while keeping the same data semantics. |

Across all nine captures, the trend is rendered as discrete recorded observations, the target band is visually subordinate, the latest observation is emphasized, and advanced CGM metrics remain explicitly unavailable without governed sensor coverage.

## Expert-style UX/UI review

No external human expert was consulted; this is an expert-level model review grounded in the nine observed captures and the retained product contract.

- Information hierarchy and reading order: **9.3/10**.
- Responsive consistency and product continuity: **9.4/10**.
- Clinical truthfulness communicated in the UI: **9.5/10**.
- Navigation and action affordance: **9.0/10**.
- Visual polish / obstruction management: **8.6/10**.

**Final observed visual score: 9.1/10.**

The remaining visual debt is minor and non-blocking for this certification: the floating Companion quick-action can touch or partially overlap a secondary card edge/badge at some intermediate scroll positions, most visibly around the mobile `mid` capture. In the reviewed evidence it does not obscure the primary glucose value, the main add-reading CTA, the navigation bar, or the governed-CGM warning. This should be treated as polish debt, not hidden by an inflated score.

## Clinical truthfulness boundary

The Dashboard distinguishes recorded episodic readings from continuous-CGM metrics. A synthetic episodic dataset may produce ordinary descriptive values such as count/mean, but advanced CGM metrics remain unavailable when governed coverage is not established. This certification proves fail-closed engineering behavior; it does **not** claim that synthetic episodic readings constitute valid TIR/TAR/TBR evidence.

## Roadmap arithmetic

This certification is Dashboard engineering maintenance over an already-closed Dashboard workstream. It does **not** add a P5 closed lot and does not change canonical MENA or Pilot Readiness arithmetic by itself.

## Residual boundaries

- No Vercel deployment is authorized or performed by this closeout.
- No real-patient data was used.
- Real-device, human clinical review, legal/regulatory/CNDP and production authorization remain governed by their own pilot/release gates.
- Final repository closeout still requires corrective PR merge to `main` and post-merge verification of merged HEAD/CI and legacy Dashboard absence.
