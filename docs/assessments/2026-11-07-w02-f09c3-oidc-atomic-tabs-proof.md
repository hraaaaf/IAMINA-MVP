# W02-F09-C3 — Isolated Web service-JWT + atomic session-family candidate

Date: 2026-11-07. Parent: [C2 #1311](https://github.com/hraaaaf/IAMINA-MVP/pull/1311). Candidate: [C3 #1312](https://github.com/hraaaaf/IAMINA-MVP/pull/1312). Web-only. **DRAFT / NO RELEASE / NO PATIENTS**.

## Goal, Success, Proof

**Goal:** Prepare three *non-activated* controls together: trusted Web-BFF service identity, database-lock-preserving family CSRF + secret rotation, and adverse/revocation/two-tab synthetic PostgreSQL tests.

**Success condition for this sublot:** exact-head C3 test suite GREEN under Python 3.12/Node22/PostgreSQL16; no HTTP activation, no cookies/bearer minted, no Vercel/Neon change; C2 and C1 guards remain deny-only. This does **not** equal hosted Web patient-session security or production readiness.

**Proof:** GitHub Actions branch workflow `.github/workflows/w02-f09c3-oidc-atomic-pg16.yml` on exact source HEAD; check output and unexpected skips/xfails. PR #1312 tracks current head and evidence.

## Code boundary and threat model

- `backend/core/web_refresh_c3_candidate.py` is unmounted: no new Django endpoint. `frontend/api/session-refresh.js` remains unconditional HTTP 404 and generic `frontend/api/index.js` forbids refresh. Code can be exercised only by tests or future separately reviewed server adapter.
- Service identity is independently checked from an RS256 Vercel team-issued JWT: pinned `https://oidc.vercel.com/{owner}/.well-known/jwks` (no redirects), exact `iss/aud/sub/owner/project/project_id/environment=preview`, bounded time and JWT parsing. No browser-supplied JWKS. The only injected keyset is gated by `F09_C3_SYNTHETIC_JWKS_ALLOWED=True` in disposable tests; absent/false by default.
- BFF still signs exact method, path, origin, timestamp, nonce and body digest through C2. A verified service signature *never* grants patient identity, clinical authority or access bearer.
- Signed BFF nonce is burned outside the family transaction, so a rejected session cannot resend the same valid transport envelope. PostgreSQL `WebRefreshFamily.select_for_update()` is held while validating the current family CSRF and invoking already governed F09-B single-use rotation. Unexpected failures refuse with one non-disclosing error. No raw secret is persisted.
- Same-family parallel requests with independent BFF nonces and the same old CSRF produce one rotation and one denial; the stale second tab does not gain access. This is a **database/thread simulation**, not browser E2E or proof of cross-tab coordination.
- Replay revocation semantics remain a security-policy question: a stale old-CSRF request is denied prior to F09-B replay revocation. Differentiate benign duplicate tabs from stolen-token replay explicitly before allowing any real adapter. Never call this a certified replay response.

## Explicit negative controls

Missing/invalid service JWT; wrong issuer/audience/subject/owner/project/ID/environment, time and alg; tampered RS256 signature; duplicate signing key; malformed non-string JWT typ; invalid synthetic key-source gate; cross-account CSRF; stale rotation CSRF; family revocation and auth-version mismatch; two concurrent PG16 workers; C1 still 404, C2 HMAC+nonce, BFF generic route isolation.

## Hard activation blockers

1. Actual Vercel OIDC team-issuer mode, trusted-service token provenance and pinned JWKS reachability/configuration must be validated on approved real hosted infrastructure. Read-only Vercel inspection on 2026-11-07 identified Web project `iamina-review` (`prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`), API project `iamina-certified` (`prj_Pn9FnyconF3h2w9gOU74iV98kJoU`), team slug `achraf-benmoussa-s-projects`; no configuration changed.
2. No reviewed HTTP adapter or HttpOnly/Secure/SameSite cookie lifecycle. No Django bearer bound to Web refresh family; no real logout/cross-tab invalidation semantics, no device boundary.
3. Real browser FR/AR RTL / 390/768/1280 + two-tab, idle/absolute expiry and multi-device first-user E2E not performed. User-approved expiry policy and security/clinical reviewer gates outstanding.
4. Production key provisioning/rotation, JWKS caching/failure policy, C2 nonce ledger retention and log-redaction/anti-XSS assurance not proven. A green CI does not prove those.
5. No Vercel deployment without explicit user authorization. No Neon migration or real patient use. W02 SECURITY_NO_GO / patients NO_GO.

## Next exact

Use the latest exact-HEAD GitHub CI evidence to fix defects, update PR and canonical Notion truth. Then define a separate dedicated reviewed HTTP adapter + bearer-family revocation contract, without activation; require the applicable approval gates before live testing, merge, migration or deployment.
