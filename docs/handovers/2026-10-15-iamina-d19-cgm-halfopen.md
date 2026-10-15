# IAMINA — D19 / CGM half-open time windows (15 Oct 2026)

## Goal / observable success / proof
A reading exactly at `window_end` must not belong to the preceding CGM sufficiency, TIR/CV or AGP window, but must be available to the following period. Success: Django+PostgreSQL boundary tests on the exact commit and independent reviews with no regression in thresholds, patient isolation or API projections.

## Evaluated state
- Parent D19: #920, baseline `81bf4d6ac4e182f3058ca6ff52b504ce8404beb9`, 17/17 historical CI green.
- Child: #1071 DRAFT, isolated half-open query and cadence denominator correction from `e9911fd66b2bb9326c25bfe4bd9f5577b4988acd` plus partial cadence test `969ca1f405b29d5099ce6ee978ee9931129b2845`.
- CI-only draft #1072 targets main because workflows only run PRs based on main/dev; it must NEVER merge.
- Clinical threshold, patient locale/day policy, database model, patient-facing UI and Vercel untouched.

## Authority boundaries and open gates
Code/test evidence is candidate only until executed on final HEAD. Human clinician must approve CGM sufficiency and wording; security/privacy reviewer must examine data lineage; independent MENA/localization and Release Certifier gate remain. CAL-09/10 patient-local day, CAL-11 USDA rows, CAL-12 typed PDF/consent and cross-surface parity are still OPEN. No merge/main/Vercel or real patients before explicit approvals.

## Next exact
Verify exact SHA workflows; if no jobs triggered, diagnose GitHub Actions event pathway rather than claiming success. If red: inspect logs, fix and rerun. If green: independent adversarial reviewers and clinical/privacy human gate, then merge into D19 parent only after review and keep parent DRAFT until final lot certification. P5 historical 6/12 = 50% unchanged.
