# IAMINA — W02-F09 C7+C8+C9, lot unique Web/PWA

Date: 2026-11-07. Parent C6 SHA `1f51d445848af7f1e835c94b9548c9801e3ca469`. All changes isolate under branch `test/w02-f09-c7c8c9-integrated-security-20261107`, no live auth or Vercel deployment. This file is the canonical handover, not a product certification.

## GOAL / SUCCESS / PROOF
- **C7**: verify team-scoped Vercel OIDC JWT (synthetic keys in CI), signed BFF request + consumed nonce BEFORE transaction, family CSRF + current opaque secret + PG row lock; rotate refresh secret, issue C5 family-bound short bearer and rotate CSRF in ONE PostgreSQL16 atomic transaction. Roll back ALL family changes when post-rotation creation fails. After commit return a **server-signed internal receipt** (separate response-HMAC key, bound to incoming BFF timestamp+nonce), verified with Node22 before pure C6 cookie serializer. C7 is **not mounted**.
- **C8**: Flutter Web isolated in-memory coordinator, candidate only (no AuthService import). Explicit test flag, short bearer, single-flight refresh, memory purge first during logout, deny late network response after logout, cross-tab BroadcastChannel signal that contains NO credentials, error/offline fail closed. No token persistence, no cold-start remote authority.
- **C9**: run tests of C7 atomic PG16/negative headers/nonce replay, Flutter VM+Chrome candidate tests; build actual Flutter Web test-only probe; test two separate browser tabs in real Playwright Chromium and WebKit on localhost, FR+AR RTL direction, pending-refresh versus logout race, offline logout, reload, and storage absence. Browser harness does NOT test a hosted Django login/refresh; backend tests are independent.

PROOF target: `.github/workflows/w02-f09-c7c8c9-integrated-security.yml`, two jobs on same SHA: PG16 full Django suite and parallel Flutter/browser; artifact `w02-f09-c7c8c9-offline-real-browser-evidence` (redacted proof JSON). Do not claim successful status until exact-HEAD job logs confirm it. No CI percentage estimates.

## Sources
- `backend/core/web_refresh_c7_atomic_candidate.py`; `backend/core/tests/test_w02_f09c7_atomic_bundle_pg.py`
- `frontend/api/w02_f09c7_verify_reply.js` (HMAC response attestation; browser never sees refresh secret)
- `frontend/lib/services/web_refresh_c8_coordinator.dart` and platform bus contract/stub/web files; `frontend/test/services/w02_f09c8_candidate_coordinator_test.dart`
- `frontend/lib/ui_w02_c9_two_tab_probe_main.dart` (CI-only Dart entrypoint); `scripts/w02_f09_c9_real_browser_probe.py` (Playwright test-only)
- `.github/workflows/w02-f09-c7c8c9-integrated-security.yml`

## RISK AND HUMAN GATES
1. NO production Django auth route uses C7/C8. `/api/v1/auth/refresh` remains HTTP 404 and existing clinical APIs reject the C5/C6 bearer. Tests have synthetic accounts, origins, signed keys and backend. No patient information.
2. Receipt HMAC validates an isolated internal BFF/backend contract but **does not prove hosted Vercel OIDC/JWKS, secure runtime key injection, backend HTTP response delivery, live cookie Set-Cookie or JS memory token provenance**. C8 synthetic `verifiedByBackend=true` is ONLY test scaffolding, not a cryptographic check; route activation MUST tie it to the C7 response verifier with an audited transport.
3. Browser C9 exercises the actual compiled Flutter candidate at localhost, independent of live Django/Ninja routes. It does NOT establish real end-to-end clinical auth, cookie renewal or the real app navigation on hosted Preview. No real hosted validation or deploy authorized.
4. Safe failure: a rejected C7 refresh spends one BFF nonce but rolls back family changes on post-rotation errors. Client cross-tab logout broadcasts a **conservative revoke-all-memory signal**, so distinct concurrent families in one browser are also locally evicted; per-family selective UI logout is NOT proven. A server without a received logout cannot instantly revoke an offline stolen bearer. In-flight already-authorized API requests and benign two-tab refresh semantics need independent security review.
5. No new migration, no Neon modification, no real patient data, no merge, no Preview/Production Vercel deploy. Human TTL/idle/absolute duration policy and signed independent security/crypto review remain unfulfilled.

## Outcome semantics
Passing targeted tests means **C7 C8 C9 SYNTHETIC ENGINEERING GREEN**, not **W02 SECURITY_GO**, not a production-ready Web refresh, and not a completed clinical C9 E2E. If WebKit or other tests fail, report exact failures and do not close the lot.

## Next exact
Check the two CI jobs at final HEAD, fix deterministic failures, rerun; record proof/PR/Notion. Then obtain explicit Vercel Preview authorization before any hosted real-browser cookie/OIDC end-to-end test. Product rollout needs independent review, live route wiring behind a secure human gate and full W02 D10/D9/D24/D26 closure.