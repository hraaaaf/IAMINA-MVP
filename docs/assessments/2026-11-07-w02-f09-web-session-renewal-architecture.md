# IAMINA W02-F09 — Web session renewal / revocation architecture (PROPOSAL ONLY)

**Status:** DESIGN_CANDIDATE / HUMAN_SECURITY_UX_GATE / NOT_IMPLEMENTED / SECURITY_NO_GO  
**Date:** 2026-11-07  
**Only decision under study:** how to renew a Web patient session after a short-lived Django native bearer without reintroducing a long-lived, JavaScript-readable credential.  
**Parent:** W02-F08 Draft PR #1299, exact HEAD `9cc220edb5b38c9e0ab37362d02d3cd4fc777851`. Its 900-second access-token ceiling is experimental, **not** accepted clinical/product policy.  
**Scope:** Web/PWA, Django + Vercel BFF trust boundary, access bearer, renewal, Django cookie/CSRF, idle/absolute session limits, concurrent tabs and offline logout. No native-only feature, release, runtime config, SQL, migration, or patient data.

## 1. Verified observations (not an approval)

- Django `backend/core/native_auth.py` currently signs `uid` and account-wide `auth_token_version`; W02-F08 candidate caps bearer validity at 900 seconds and rejects malformed/oversized settings. Test-only PR #1298 proves immediate replay remains HTTP 200 if logout never reaches Django, and 16-minute replay is HTTP 401 at F08 HEAD (PG16, 2,928 pass). A server cannot know an offline logout took place without communication.
- Flutter `AuthService.refreshToken()` retires the native bearer and returns null. It does **not** rotate or issue a native bearer; the Firefox/Chrome cross-tab F06/F07 local lock evidence does not prove Django revocation.
- `login_native` and `register_native` invoke Django `login()` through `_open_session`, **in addition** to returning a bearer. `SESSION_COOKIE_AGE=1209600` (14 days), `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`; `SessionAuth` accepts cookie-only requests on a protected API route if there is no Authorization header, with CSRF checks. The current Web BFF intentionally strips cookies upstream, but that does **not** prove the cookie credential is harmless on other accessible paths. Deployment routing and effective hosted settings have not been verified.
- F05B original Flutter physical-delete-under-permanent-storage-fault assertion remains red; PR #1290 `/auth/me` native bearer fix is separate/unmerged and must not be presumed integrated with F08.
- Exact F08 SHA CI: 10 workflows complete, 9 success, 1 Flutter failure from existing F05B. No patient release, merge, Preview, or Neon authorization follows from this evidence.

## 2. Recommended option, still subject to human choice

**Prefer WEB BFF-managed renewal with server-owned opaque, single-use rotating refresh credentials, not a durable refresh bearer in Flutter Web storage.** This is a recommendation, **not an accepted decision**. The browser should hold only a `Secure; HttpOnly; SameSite` BFF-origin renewal cookie, scoped narrowly to the refresh/logout routes; JavaScript must not read it. The BFF must never forward it as an ordinary Django patient session cookie. Django remains the authoritative account/session and protected-resource decision maker; PostgreSQL must store only a cryptographic hash of refresh secrets and minimal metadata, not raw secrets.

**Trade-off:** this requires BFF route design, secure cookie + CSRF/origin coverage, a server-side family/session data model, a migration and Web auth client integration. Do not fake a secure renewal with a second 30-day JS-readable bearer. It improves resistance to token exfiltration, but an attacker exercising the authenticated browser session (e.g. via XSS) is still a threat; HttpOnly alone is not a complete defense. No Web refresh may silently unlock an offline patient vault or bypass app-lock.

Alternative A: server reauthentication at access-token expiry, no refresh token. Lower attack surface and simpler code; frequent interruptions make it a poor choice unless explicitly chosen for a constrained rollout.  
Alternative B: long-lived rotating refresh token in Flutter secure storage. Rejected as default for Web until its encryption, isolation, theft/replay resistance and failure semantics can be independently proven.  
Alternative C: wholesale cookie-only patient sessions. Not automatically safer: the existing 14-day Django cookie and CSRF/idle/absolute semantics must be hardened first, and using a cookie alone does not imply revocation or an absolute limit.

## 3. Proposed server contract — must be proven before code accepted

1. **Separate credentials:** short-lived access bearer is never used as refresh authority. Each refresh family is tied to one user, one logical Web session and a bounded client/BFF purpose. Its opaque secret is CSPRNG-generated, secret bytes never logged and never stored in plaintext on the server. Restrict audience and paths.
2. **Atomic one-time rotation:** `POST refresh` (BFF-mediated) validates the current family, server idle deadline, fixed absolute deadline, revocation generation and CSRF/origin; under a PostgreSQL transaction/row lock, consumes the old secret and issues a new one. One concurrent refresh wins. Re-use of a consumed secret is a compromise signal: revoke the active family/access credentials and require reauthentication. Do not accept a stale token using a silent replay grace window.
3. **Access token invalidation:** a rotated-out refresh secret cannot itself authorize clinical API routes. An access bearer minted by a family must carry a server-verifiable family/session binding or equivalent revocation handle; otherwise family revocation does not invalidate already-issued bearers. Account-wide `auth_token_version` remains a global emergency/password reset revocation boundary. Per-session vs all-device logout semantics need an explicit contract.
4. **Expiry:** server enforces **access max age**, **refresh inactivity limit**, and **session absolute limit**. A refresh cannot extend the absolute origin timestamp. Recommended numbers and risk tolerance require human security + UX selection; 900 seconds is still only the F08 access-token candidate, not a renewal/session policy.
5. **Cookie / CSRF:** Web refresh cookie must be Secure, HttpOnly, scoped Path, and an appropriate SameSite; unsafe methods require CSRF token plus exact Origin/Host checks. Browser requests must not allow arbitrary cross-origin credentialing. Ensure BFF headers/cookie forwarding are allowlisted. Avoid token disclosure in JSON, URLs, logs, errors, browser persistent storage and telemetry.
6. **Existing Django cookies:** inventory all `/api/v1` routes that can authenticate cookie-only, plus login/register, admin, legacy sessions and CSRF. Decide whether native Web API login should issue a Django session cookie at all; prevent the 14-day cookie from bypassing the shorter patient access/session rules. Admin and legacy behavior require explicit compatibility tests. `SESSION_COOKIE_AGE` by itself is neither an activity timeout nor a full absolute session policy.
7. **Client and offline boundary:** when refresh fails (401, replay, idle/absolute expiry, network error, storage error), never grant patient scope or replay clinical egress under stale credentials. Distinguish offline temporary unavailability from authenticated authority, preserve local encrypted data without unlocking, and maintain F06/F07 cross-tab retirement. A late refresh must not republish after logout, account switch, AuthEpoch change or local lock.
8. **Logout:** revoke family on server when request reaches Django, retire Web local authority synchronously even if network/storage fails; queueing a logout is not server-revocation proof. If a copied access bearer is used before expiry while logout is offline, remote replay risk remains until expiration or another server-side revocation event. Present this limitation honestly.
9. **Migration/ops:** new PostgreSQL schema requires migration/backfill/rollback and isolated PG16 proof. Existing F08 and #1290 branches are unmerged: plan ordering/rebasing, OpenAPI, Django auth and Flutter lifecycle together. No migration on Neon QA or prod without separate authorized gate.

## 4. Red-first acceptance matrix (ALL NOT_RUN at design publication)

| ID | Security/UX oracle | Expected evidence |
| --- | --- | --- |
| F09-T01 | expired access bearer alone cannot refresh and cannot call `/api/v1/logs`; properly authorized refresh returns new bounded access credential | cookie-less + cookie-mediated Django HTTP on ephemeral PG16 |
| F09-T02 | two simultaneous refresh requests for same old secret cannot both succeed | transactional PG16 concurrency, one winner |
| F09-T03 | old refresh secret reused after rotation revokes family, all family-bound access credentials 401 | PG16 replay test; account/global version semantics explicitly checked |
| F09-T04 | logout, password reset, account deactivation/revocation invalidate refresh and associated access; other account unaffected | patient A/B and device isolation tests |
| F09-T05 | idle limit and fixed absolute session max reject refresh even with repeated activity; configuration cannot silently disable limits | patched server time; negative setting tests |
| F09-T06 | cookie-only bypass of patient session limits, expired/invalid bearer + valid conflicting Django cookie, and CSRF/origin bypass all denied | real protected routes, Django/BFF parity |
| F09-T07 | Web refresh unavailable, HTTP 401, delayed response after logout/switch/lock never republishes patient authority or egress | Flutter VM + real two Chrome tabs; F05B/F06/F07 unchanged |
| F09-T08 | no browser-readable persistent refresh secret and no token in logs/URL; app-lock/locked offline vault unchanged | browser storage/network inspection, privacy audit |
| F09-T09 | valid session renews without interruption; absolute/idle expiry requires honest reauth and does not erase unsynced local entries | FR/AR RTL Web FUE at 390/768/1280 where relevant |
| F09-T10 | Neon migration not attempted; isolated PG16 forward/rollback and indexes safe; no production credentials in tests | migration drift, isolated restore and database reviewer |

All are **NOT_RUN**, not failed or passed. In particular no design text certifies the implementation or the Web BFF topology.

## 5. Independent adversarial objections / open human gates

- **BLOCKER SECURITY:** a persistent refresh mechanism can extend a stolen browser session. Rotation detects concurrent use, but not a thief who uses the refresh credential first and is never challenged. Consider sender-constraining or step-up authentication for sensitive actions.
- **BLOCKER DESIGN:** Django currently creates a cookie session for native login; shortening only the bearer may leave another API authentication route alive. Map and test both before treating F08 as protective across all API calls.
- **MAJOR UX:** 15-minute expiry with absent renewal would disrupt legitimate diabetes journaling; server idle and absolute durations cannot be guessed from a benchmark. User/safety owner must approve a risk-based policy and reauthentication experience.
- **MAJOR COMPATIBILITY:** actual BFF cookie handling and cross-tab token storage differ from the recommended design and require a no-bypass migration with real Chrome evidence.
- **DEPENDENCY:** PR #1290 bearer-aware `/auth/me` is not stacked on F08, and F05B original test remains red. No independent human reviewer signature.
- **UNKNOWN:** effective hosted runtime config, CSRF and cookie-domain behavior, family store availability, device/session policy, approved idle/absolute timeouts.

## 6. Gate / next exact

**This document changes NO runtime code.** It offers a narrow architecture proposal for an explicit human security/UX choice. Before implementing, map actual Web BFF request/cookie flows and Django cookie-only authorization entry points; derive an independent RED test for cookie-only access after patient-session expiry and for refresh replay/concurrency. Build on isolated F08 stack **only after the architecture is selected**, keep new PR Draft, run exact-head PG16, Flutter and real browser checks, perform independent security and adversarial reviews.

**No merge, no Vercel deployment (including preview), no Neon modification, no real patients; W02 SECURITY_NO_GO.**

Sources: [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet), [IETF RFC 9700 §4.14 refresh protection](https://www.rfc-editor.org/rfc/rfc9700.html), [Django sessions official documentation](https://docs.djangoproject.com/en/5.1/topics/http/sessions/). RFC 9700 is an OAuth 2.0 BCP and is used here as a relevant replay/rotation **benchmark** for IAMINA's custom token protocol, not a claim IAMINA implements OAuth or is legally required to.
