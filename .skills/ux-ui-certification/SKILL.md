# Skill — UX/UI Certification

## Purpose
Certify UX/UI LOTs against real rendered evidence, not implementation intent.

## Mandatory sequence
1. Capture or exercise the current baseline before remediation when the defect is visual/interactive.
2. Audit hierarchy, spacing, typography, navigation, responsive behavior, accessibility, FR/AR parity and RTL where applicable.
3. Assign a baseline score and record blockers.
4. Builder remediates; do not lower acceptance criteria to fit the implementation.
5. Re-run real viewport/locale evidence on the exact product SHA.
6. Reviewer scores each affected screen critically.
7. Any critical/high defect blocks certification.
8. Global UX/UI score must be strictly greater than 9.0/10. A score <=9.0 keeps the LOT open and requires remediation + full recertification of affected evidence.
9. Record capture run/artifact/digest when available.
10. Update `docs/ROADMAP.md` before closure.

## Truthfulness rules
- No fabricated metrics, clinical precision, availability, synchronization, privacy or capability claims.
- Loading, error, empty, offline and success states must be distinguishable when relevant.
- Arabic must be real RTL/localization, not a superficial mirror or French fallback.

## Minimum viewport doctrine
Use the LOT's acceptance matrix. When mobile is in scope, include a harsh small-screen case such as 360x560 if the canonical audit requires it.