# Skill — UX/UI Certification

## Purpose
Certify UX/UI LOTs against real rendered evidence, not implementation intent.

`docs/QUALITY_SCORING_POLICY.md` is mandatory and overrides any weaker scoring convention.

## Mandatory sequence
1. Capture or exercise the current baseline before remediation when the defect is visual/interactive.
2. Define the visual/interaction target and the required identical viewports/states/locales for Target ↔ Render comparison.
3. Audit hierarchy, spacing, typography, navigation, responsive behavior, accessibility, FR/AR parity and RTL where applicable.
4. Score critical visual dimensions explicitly; no weak critical dimension may be hidden by an average.
5. Builder remediates; do not lower acceptance criteria to fit the implementation.
6. Re-run real viewport/locale evidence on the exact product SHA.
7. Record an `EXECUTION_SCORE /10` for the rendered result.
8. Conduct a **fresh, adversarial evidence pass** and score the same rendered result as `ADVERSARIAL_SCORE /10`, actively checking clipping, overflow, hierarchy, target fidelity, accessibility, locale/RTL and regressions. An independent reviewer may be used but is **not required for a D**: the full FUE is its user-experience gate; apply the same-executor score cap.
9. Retain the lower score, after applying all caps from `docs/QUALITY_SCORING_POLICY.md`.
10. If Execution and Adversarial scores differ by more than `0.5`, investigate the discrepancy, fix/justify, rerun affected evidence and rescore.
11. Any critical/high defect blocks certification.
12. If real Target ↔ Render comparison is absent, the visual-fidelity dimension is capped at `7.5/10`.
13. A UX/UI LOT may be `VERIFIED` only with final retained score `>= 9.0/10` and all required binary gates green; **for each D, that includes a full FUE of every in-scope feature and a 100% required PASS matrix**. Test first-user interactions, not only screenshots.
14. Even at `9.0+`, perform the mandatory final **Perfection Pass**: identify remaining weaknesses, fix every materially improvable in-scope issue, rerun the affected captures/tests, and rescore.
15. Claiming `9.5+` requires a genuinely independent review; **this high-score cap is not an independent-review gate for D**. Same executor for Builder/FUE/adversarial pass is capped at `9.4/10`.
16. Record capture run/artifact/digest when available.
17. Update `docs/ROADMAP.md` before closure.

## Truthfulness rules
- No fabricated metrics, clinical precision, availability, synchronization, privacy or capability claims.
- Loading, error, empty, offline and success states must be distinguishable when relevant.
- Arabic must be real RTL/localization, not a superficial mirror or French fallback.
- Real screenshots/rendered runtime evidence outrank implementation intent.

## Minimum viewport doctrine
Use the LOT's acceptance matrix. When mobile is in scope, include a harsh small-screen case such as 360x560 if the canonical audit requires it.

## Required scoring record
For each affected screen/state, record critical dimensions plus the LOT-level Execution, Adversarial and retained scores, applicable caps, score-gap investigation when needed, remaining weaknesses, and Perfection Pass result.
