# W02-F09-C4 — Web BFF to Django HTTP transport, non-activated
Date: 2026-11-07.
PR: https://github.com/hraaaaf/IAMINA-MVP/pull/1313 (DRAFT).
Base: C3 commit 288d3f622f1128deb9c9421b642dc49abe2d563b.

## GOAL / SUCCESS / PROOF
Goal: Prove isolated Node22-signed Web-only request preparation and Django RequestFactory parsing into C3 service OIDC and PostgreSQL family-locked rotation, without enabling real HTTP refresh.
Success criteria: Node22 and PG16 tests green, C1/C2/C3 regressions and Django full PG16 green on exact code SHA; no deployment, migrations or patient data.
Proof workflow: .github/workflows/w02-f09c4-http-contract-pg16.yml. At initial write, CI #42410915180 pending: https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42410915180. Recheck latest source HEAD before declaring pass.

## SCOPE
- frontend/api/w02_f09c4_prepare.js is NOT imported by the live Vercel handler. It validates Preview origin/host/project, unique browser cookie values and signed CSRF shape; constructs exact signed JSON request from BFF-only signing key and separately supplied runtime OIDC proof. No fetch, cookie issuance or arbitrary browser Authorization/Cookie/proof headers upstream.
- backend/core/web_refresh_c4_http_candidate.py is NOT mounted into Django URLs. It requires explicit F09_C4_HTTP_ADAPTER_ENABLED=True in synthetic tests only; verifies POST/path/host/content-type/size/no upstream cookies or Authorization, then delegates to C3 JWT verification, signed nonce burn and atomic locked-family CSRF+refresh rotation. Internal raw replacement never becomes an HTTP response.
- Synthetic tests cover valid request, public 404, disabled flag, tampered body, bad JWT/host, forwarded cookies and bearer, duplicate JSON, duplicate nonce, and two parallel PG16 requests.
- Updated C3 JWT typ compatibility after Vercel docs example says lowercase jwt. It remains string-only and case-insensitive, while non-string typ fails. Reference: https://vercel.com/docs/oidc/reference.

## SAFETY GATES
The live frontend/api/session-refresh.js remains always 404. Generic proxy stays isolated; frontend/vercel.json auto deployment disabled. No HTTP refresh routes enabled, no actual browser cookies, no bearer linked to family, no clinical patient authority. Real Vercel OIDC tokens, JWKS configuration, key rotation, XSS/logging, cross-tab real browser flows, logout and idle/absolute UX policy remain unproven.
No merge or Vercel Preview/Production deployment without explicit authorization. No Neon or real patient data. W02 SECURITY_NO_GO, PATIENT NO_GO.

NEXT: check exact-HEAD CI, fix any red, update GitHub and Notion with actual evidence, then separately design and test bearer-family/cookie contract under activation gates.
