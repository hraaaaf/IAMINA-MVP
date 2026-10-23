# IAMINA WEB — W03 D21+D3 × L0 four-lot integration — 23 October 2026

## Goal / observable success / proof
Bring existing W03 D21 Web Ramadan-hidden Profile and D3 local reminder count together with the L0 network/CGM/Companion local-only, finite glucose and saving guard, D11 no-demo patient-seed and SSE POST/CSRF protections in **one exact HEAD**. Success requires CI on this joint HEAD, six W03 FUE scenarios (FR/AR × 390/768/1280), native-vs-Web legacy Ramadan parity, local reminder A→B→A, no clinical HTTP egress, D11 PostgreSQL denial, SSE POST, dashboard screenshot checks, and independent review. No production, main merge or Vercel deployment permitted by this integration.

## Exact provenance and reconciliation
- main baseline `8ada5aab8e8006bbbdc275eabbabf014a4714e0b`.
- L0 four-lot #1145 source commit `e13a03ebd7ef823154e5719b8648854078c00aea`, Git base tree `827a0850d94b9e18e3bd01efaa2696c87ebec86a`. All four safeguards, backend/security tests, SSE workflow and frontend code are inherited unmodified from this parent except the deliberate two-hunk joint edit.
- W03 D21+D3 #1148 source `130161c6c6d024a4eef50811bcd4387b55e2ebe7`: 19 non-overlap blobs copied by exact Git SHA (includes browser/RTL/FUE, Profile, local reminders and tests). The **only** collision is `frontend/lib/features/dashboard/widgets/add_log_sheet.dart`. Reconciled two W03 hunks using `shouldApplyRamadanProfileContext(isWeb:kIsWeb)` and `mealTypesForSurfaceDate(...,isWeb:kIsWeb)`, without changing L0 finite input conversion or `_saving` leave guard. Reverse-hunk check proves L0 blob is otherwise unaltered.
- Port the already-green L0 #1147 `tools/dashboard_capture.js` blob `a3f7bd8a90d6e2f42e2360ed6556d518e25e750b`: wait for Flutter Web DOM mount rather than impossible Companion HTTP response; explicitly assert zero clinical Companion HTTP. Original #1145 was 16/17 workflows, failing Dashboard on obsolete `waitForResponse` oracle.
- Add `frontend/test/features/dashboard/w03_l0_joint_contract_test.dart` to test the combined policy and guard.

## Evidence status / human gates
Pre-commit checks: 19 unmodified W03 blobs verified in source Git tree; exact two-hunk reconciliation and L0 restoration checks PASS. These are structural, not runtime claims. Run exact-SHA GitHub Actions before asserting automation passes. The source W03 #1148 was 13/13 green; L0 three-lot #1147 was 16/16 green, but neither independently certifies this four-lot joint build.

Blocked for any real-patient rollout: W01 #1128 hosted A→B→A/Neon/Redis/DR E2E, independent clinical/privacy/security signoff and emergency handling #1134, real touch/RTL on device, delayed Drift write/back race, required independent adversarial review and score ≥9.0 (D21 previous 8.8/10), and explicit authorization for any Vercel deployment. D3 local reminder count is not the full 2–3 upcoming reminders feature. D2 #1135 Dashboard collision remains a future integration gate. No real patient data, no merge or Vercel change here.

**NEXT exact**: collect the new joint HEAD's CI outcomes, investigate failures, inspect W03/Dashboard image artifacts and browser reports, review clinical/security implications, address human gates, and only then consider integration/main release with an explicit separate Vercel approval.
