# IAMINA D11 — No fabricated glucose history in real patient accounts (Web, 2026-10-29)

**Status: CANDIDATE / NOT_VERIFIED / NO_DEPLOY.**

## Goal → Success → Proof
- **Goal:** no real patient account or patient Drift vault can receive synthetic demo readings or have pre-existing legitimate medical entries overwritten by a demo initializer.
- **Success:** authenticated `POST /api/v1/demo/seed` always refuses (403), anonymous remains 401; new patient registration begins with zero fabricated readings; local/native patient vaults reject both audit helpers and direct demo seeding **before** any deletion; only explicitly isolated `auditOnly` fixture supports demo content; `setup_demo` cannot run on PostgreSQL or in non-debug environments.
- **Proof pending:** exact HEAD backend SQLite/PostgreSQL, Flutter tests, Web/PWA and relevant Chrome checks; deliberate second adversarial pass, score and Perfection Pass. No real patient accounts or DB writes in tests.

## Historical source and divergence
- New branch `fix/d11-web-zero-fabricated-20261029` starts from `main@bcbf2798b7d14fdeee09447d8a1f1015c9bb323a`, after D19 merged/deployed.
- Existing D11 [candidate #1142](https://github.com/hraaaaf/IAMINA-MVP/pull/1142) at `450c0f935e355df76a89faa0d5b9235ee0a0d1a9` had six workflows SUCCESS on its **historical** head but diverged by 31 commits behind `main`, 4 ahead. **Do not merge it wholesale**.
- Reused its tested fail-closed code on current `main`, preserving D19/main differences: backend demo endpoint, admin fixture safeguards, client audit-only helper, Drift patient vault guard, backend + Flutter negative tests, CLI tests.
- Current main **before** change contained a real defect: `backend/diabetes/api/v1/demo.py` accepted authenticated `/demo/seed` and inserted random readings into `request.user` plus possible synthetic profile; `AppDatabase.seedDemoData()` deleted all entries unconditionally; `seedOfflineDemoAuditData` checked flags but not vault scope.
- The endpoint remains registered with explicit denial and its OpenAPI `description` is updated **without altering any other schema field** (object-equality check before commit).
- The entire main `database.dart` was verified byte-identical to historical candidate when its D11 guard was removed; therefore adding that guard does not overwrite newer code. No DB migration, auth token rotation, real patient records or clinical thresholds touched. Existing hosted-review bootstrap not changed: startup changes require separate observed bug/scope.

## Current release and boundaries
- Previous D19 production Web+API builds remain on `cc37d3a5da1c035a9d0fcd185762a42acc6ba93e`. These builds **do not contain D11 fixes**.
- No new production deployment authorized for D11; GitHub branch/PR is only a candidate. A PR may trigger GitHub CI, not permission to deploy.
- Backend `/api/v1/health` reported `cache=unavailable` on prior D19 production sample; independent operational observation, not a D11 pass/fail.
- No independent external human reviewer automatically required per `docs/QUALITY_SCORING_POLICY.md`; execution/adversarial scoring and evidence-based FUE/Perfection Pass still required before certification.

**Next exact:** create Draft PR from branch; inspect exact-HEAD GitHub Actions and repair any RED; use synthetic-only Web/PG tests to verify no fake records and original persistence; finalize score/Perfection Pass, then request distinct GO before any merge that deploys or any production deployment. Do not assume previous CI result applies to this SHA.

## 2026-10-29 — GREEN at tested head, adversarial auth pass, and Web FUE expansion

**Baseline exact-HEAD GREEN:** commit `0aeec0db2a9d92f5074cab1d5a984b1fc43fc809` passed 6/6 workflows: [CI #40932046066](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40932046066), migration drift, offline PWA, PWA recovery, PWA browser persistence, and P5-5 pilot rehearsal. CI job logs: **2,886 backend PASS / 5 skipped / 3 xfailed; 2,889 PostgreSQL PASS / 2 skipped / 3 xfailed; 844 Flutter PASS / 1 skipped.** This is evidence for `0aeec0db`, not subsequent commits.

**Adversarial finding (auth precedence):** `diabetes.api.main` mounts protected routes with `[HybridBearerAuth, SessionAuth()]`. An explicit invalid Authorization bearer could fall through to a valid unrelated Django session via `SessionAuth`, silently selecting cookie identity instead of rejecting the supplied bearer. A valid bearer takes precedence and sets `request.user`; a cookie-only request must continue functioning. Security correction `a732fc31c64f833f615786974889b2772c10f48c`: `amina.vercel_session_auth.SessionAuth._get_key` rejects session fallback whenever the `HTTP_AUTHORIZATION` header is present, before CSRF session processing. This preserves cookie-only session + CSRF behavior, rejects invalid explicit bearers rather than mixing identities, and does not mutate clinical records. The new `test_conflicting_cookie_and_bearer_never_fall_back` runs with synthetic A/B log records and asserts (a) valid bearer B plus cookie A yields B; (b) invalid bearer plus cookie A yields 401; (c) cookie A without Authorization still yields A. **New-HEAD CI must be checked independently; do not reuse baseline GREEN.**

**Web FUE proof introduced:** CI workflow `.github/workflows/d19-real-auth-summary-pg-browser.yml` now triggers on D11 backend/Drift/auth changed files. It compiles the *real* Flutter `AuthService` + native Django auth + `AISummaryScreen` with an isolated PG16 database, tests synthetic A→B→A, KPI data partitioning and page rendering. Script `tools/d19_real_auth_summary_pg_browser_check.js` expanded from 6 to **18 planned browser states**: FR/AR × 390×844, 768×1024, 1280×900 × A→B→A, browser screenshots and HTTP oracle. **Planned is not passed**: require exact head Actions run and artifact report. This existing D19 screen reuse proves a meaningful authenticated clinical Web journey, but not a complete native registration screen, keyboard/recovery UI or hosted Vercel production experience.

**Perfection Pass / scores:** OPEN until exact-HEAD CI + browser artifact, feature matrix covering missing D11 first-entry/negative/recovery, isolated adversarial result, and explicit execution/adversarial numeric scoring (with same-executor <=9.4 cap). No independent human reviewer blanket requirement; no clinical certification claimed. **NO_MERGE / NO_VERCEL_DEPLOY** without distinct owner GO. Previously deployed D19 production source is separate.

**Next exact:** verify CI and D19 real-Web PG browser job on the latest branch head, inspect 18-state artifact, fix any regression, finish FUE matrix/Perfection Pass and update status with tested evidence. If required FUE cannot be executed with current environment, report FUE_NO_GO, not VERIFIED.
