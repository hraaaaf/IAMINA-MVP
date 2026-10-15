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

## 15 Oct 2026 — CI run 38765408701 root cause + sensor-boundary cross-check

**Observed actual GitHub run:** CI [#38765408701](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38765408701) on candidate `63f13e4e07a59a90422f2900fec6fcc5666607ee`. PostgreSQL job `116527334922` and SQLite/backend `116527335182` both FAILED at `pip install -r requirements.txt` before any clinical test: obsolete `google-genai==0.3.*` unavailable on package index. `main` at `ea3ad7bafaae669d2cd978fa6894a9df814539f0` already pins `google-genai==2.30.1`, main CI [#38728145583](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38728145583) SUCCESS; candidate aligns with this exact version. This isolates the pip failure but does not demonstrate backward compatibility until tests run.

**Independent code review finding:** after the first half-open report-window change, the CGM metrics and AGP still had `recorded_at <= session.ended_at`, but eligibility considered sensor sessions as `[started_at,ended_at)`. This could count a session-end reading in CGM metrics but not coverage. Candidate switches both analytics queries to `recorded_at < session.ended_at` and adds two Django DB regression tests for CGM count, TIR, AGP and eligibility. Existing thresholds unchanged.

**Status:** candidate only until exact new HEAD CI SQLite+PostgreSQL fully passes; clinician/privacy/RTL and CAL-01…12 gates open, no merge/Vercel.

## 15 October 2026 — D19 CI #38768317677 failure and targeted recovery candidate

- The workflow at source SHA `eb1dfe2fe4db72a5b13f861e205b891fdfa7f8d4` ran backend SQLite: 2814 passed, 2 failed, 5 skipped, 3 xfailed. Two legacy CAL CGM oracle tests expected 337 readings including exactly `window_end`; the current half-open contract excludes that row (336). Correct independent 336-sample oracle is TIR=69.6%, TAR=20.2%, TBR=10.1%, CV=39.3%, percentages sum 99.9% at independent one-decimal rounding; numerical invariant now allows 0.11 percentage points rounding residue. Clinical cutpoints unchanged.
- Same run PostgreSQL job #116537343431 failed before test startup: external public ECR image `postgres:16-alpine` rejected all three pulls (toomanyrequests / data limit). New CI-only proposal runs on pinned Ubuntu 24.04 with pre-installed PostgreSQL 16, starts service, explicitly sets CI-only password/DB, verifies version and TCP auth, runs unchanged migrations and full PG test suite. Reference GitHub runner image specification: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md.
- Status: code candidate pending exact new SHA CI; no D19 clinical, security or release certification; no merge and no Vercel.
