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
