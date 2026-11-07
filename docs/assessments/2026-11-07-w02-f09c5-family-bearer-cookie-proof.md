# IAMINA W02-F09-C5 — Family-bound Web bearer and host-only cookies
Date 2026-11-07. Parent C4 SHA 5474fd240da6fb0d97380b6ea61074c0e76a4e59. PR Draft: https://github.com/hraaaaf/IAMINA-MVP/pull/1314
Branch: test/w02-f09c5-family-bearer-cookie-20261107.

## GOAL / SUCCESS / PROOF
Goal: bind candidate Web access bearers to a server-held refresh family, revoke exactly one family on logout, fail closed on account-wide revocation, and keep existing native bearer/clinical auth unchanged.
Success: exact-head PG16 test of current refresh secret issuance, one-family logout, sibling isolation, expired family, 60s synthetic bearer, account version revoke and issue/logout race; JS cookie flags, regression C1-C4 and all Django tests. This is strictly synthetic, not browser/hosted acceptance.
Proof workflow: .github/workflows/w02-f09c5-family-bearer-pg16.yml. At initial document creation run 42414384754 had been started but not concluded. Actual verdict must be checked on the document commit.

## SOURCE BOUNDARIES
backend/core/web_refresh_c5_family_bearer.py is not mounted. The novel prefix iamina-web. is rejected by existing iamina. native verifier; Django clinical routes continue to accept only existing native (or migration) credentials, not C5. Issuance requires current opaque secret and active family/profile under row lock; verification checks family, account generation, idle/absolute deadline on each call. Explicit feature+TTL flags must be set in synthetic tests. Logout revokes only one family under PG16 lock.
frontend/api/w02_f09c5_cookie_policy.js is a PURE, UNMOUNTED serializer: host-only Secure SameSite=Strict and explicit synthetic Max-Age. Refresh secret/family ID cookies HttpOnly on /api/v1/auth/refresh; CSRF non-HttpOnly on / so JS can read it; Django C2 separately validates CSRF MAC and current family. Logout cookies clear the same names/path/security attributes. No real Set-Cookie header is sent.
Live frontend/api/session-refresh.js still always responds HTTP 404. frontend/vercel.json retains git.deploymentEnabled=false. No HTTP API, Neon, patient or cookie issuance.

## ACTIVATION BLOCKERS
Real OIDC JWT provenance/JWKS, cookies on actual HTTP response, family-bound bearer on reviewed clinical auth adapter, logout/refresh race and single-flight browser tabs, short bearer TTL human policy, live two-tab and offline/Chrome/WebKit FR/AR E2E, anti-XSS and log redaction and independent certification remain unproven.
F09-B spent secret replay conservatively revokes account generation; benign double-tab versus theft semantics are unresolved. This C5 candidate does not revoke an already in-flight authorized Django request; release security must review those races.
NO Vercel Preview/Production deployment without explicit authorization, no merge, no Neon migration, no real patient data. W02 SECURITY_NO_GO / PATIENT_NO_GO.

Next: verify latest exact SHA GitHub CI, repair failures, update PR and Notion. Only proceed to separately reviewed HTTP auth adapter after gates.