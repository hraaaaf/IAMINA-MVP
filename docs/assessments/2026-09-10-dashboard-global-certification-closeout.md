# Dashboard global certification closeout — 2026-09-10

## Status

**CLOSED — ENGINEERING + FINAL RESPONSIVE VISUAL CERTIFICATION VERIFIED ON `main`.**

This closeout records synthetic/non-patient engineering evidence only. It is not real-patient, clinical-human, regulatory, CNDP or deployment approval.

## Goal

Converge IAMINA on one canonical Dashboard implementation and certify responsive UI, backend wiring and bounded clinical KPI semantics without inventing continuous-CGM evidence.

## Success / proof

1. One production Dashboard authority: `DashboardCompanionEntryScreen` → `DashboardPremiumScreen`; legacy `frontend/lib/features/dashboard/dashboard_convergent_screen.dart` is absent from `main`.
2. Required responsive evidence exists at 390×844, 768×1024 and 1280×900, with `top`, `mid` and `lower` captures pixel-distinct for every viewport.
3. Django backend against isolated PostgreSQL 16 passed with synthetic non-patient data.
4. Dashboard API/browser certification passed without page error, console error or observed API response >=500.
5. Episodic glucose rows remain fail-closed from governed continuous-CGM metrics unless coverage/provenance is established.
6. All nine captures were manually reviewed; final observed model UX/UI score: **9.1/10**.
7. Corrective PR #549 merged to `main` as `22baebdeb57e11be9bea362197ac4c54629dfd5a`.
8. All five workflows triggered on that exact merged `main` SHA completed successfully:
   - UI geometry golden audit: `34537140622` — SUCCESS;
   - CI: `34537140662` — SUCCESS;
   - Dashboard responsive visual certification: `34537140633` — SUCCESS;
   - Dashboard global certification v2: `34537140596` — SUCCESS;
   - UI browser screenshot certification: `34537140657` — SUCCESS.

## Retained visual evidence

Clean pre-merge visual proof:

- run `34535253185` — SUCCESS on exact visual head `38e23b3ee0f7203ad9fa6a6903741088f93f2b2b`;
- artifact `iamina-dashboard-responsive-visual-cert`, id `10175229046`;
- SHA-256 `11dbe42c718cbab9206136823da4a737a41c554280e82ad45f0ae40baae4ee63`;
- 9/9 required captures decoded-pixel distinct and manually reviewed.

Independent RGB changed-pixel recheck:

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

The post-merge `main` responsive visual certification run `34537140633` independently passed the corrected harness on the merged SHA.

## Harness root cause and correction

Run `34534206725` was a false-negative. The screenshots differed, but the gate compared `RGBA` differences with Pillow `getbbox()`. Pillow defaults `alpha_only=True`; unchanged alpha made that check unsuitable for deciding whether RGB content changed. The final gate compares `RGB` images.

Certification scrolling is deterministic: an explicit `ScrollController` waits until layout establishes sufficient `maxScrollExtent`, then applies `jumpTo()`. Normal production Dashboard construction does not receive this certification controller.

Primary references:

- Pillow `Image.getbbox`: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.getbbox
- Flutter `ScrollController`: https://api.flutter.dev/flutter/widgets/ScrollController-class.html
- Flutter `ScrollController.jumpTo`: https://api.flutter.dev/flutter/widgets/ScrollController/jumpTo.html
- Flutter adaptive UI: https://docs.flutter.dev/ui/adaptive-responsive/general

## TARGET ↔ AFTER

Reference TARGET: retained P7 state in `docs/assessments/2026-08-17-dashboard-p7-responsive-convergence-closeout.md`.

- **390×844:** single-column flow, bottom navigation, canonical identity, no observed horizontal overflow.
- **768×1024:** compact rail + bounded content, same clinical hierarchy and authority.
- **1280×900:** full rail + centered bounded content, efficient multi-column composition with unchanged semantics.
- Across all nine captures, trend data is shown as discrete recorded observations; the target band is subordinate; latest observation is emphasized; advanced CGM metrics remain unavailable without governed sensor coverage.

## Expert-style UX/UI review

No external human expert was consulted. Model review grounded in the nine retained captures:

- hierarchy/read order: **9.3/10**;
- responsive consistency/product continuity: **9.4/10**;
- clinical truthfulness communicated in UI: **9.5/10**;
- navigation/action affordance: **9.0/10**;
- polish/obstruction management: **8.6/10**;
- **final observed score: 9.1/10**.

Minor non-blocking visual debt remains: the floating Companion quick-action can touch/partially overlap a secondary card edge or badge at some intermediate scroll positions, most visibly around mobile `mid`. In retained evidence it does not obscure the primary glucose value, main add-reading CTA, navigation or governed-CGM warning.

## Clinical truthfulness boundary

Recorded episodic readings are not continuous-CGM evidence. Ordinary descriptive values may be computed from synthetic episodic data, but TIR/TAR/TBR-style advanced metrics remain unavailable when governed coverage is not established. This closeout proves fail-closed engineering behavior only.

## Roadmap arithmetic

Dashboard certification is maintenance over an already-closed workstream. It adds no P5 closed lot and does not alter canonical arithmetic: **Pilot Readiness 2/9 = 22.2%; MENA 32/38 ≈ 84.2%.**

## Residual boundaries

- No Vercel deployment was performed or authorized by this closeout.
- No real-patient data was used.
- Real-device, human clinical review, legal/regulatory/CNDP and production authorization remain governed by their own pilot/release gates.
- Repository merge and post-merge engineering verification for this Dashboard certification are complete.
