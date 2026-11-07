# W02-F09 — Django clinical cookie CSRF boundary (RED → candidate fix)

**Date:** 2026-11-07
**Status:** SECURITY_BLOCKER / PATCH_DRAFT / GREEN_NOT_YET_PROVEN / NO_MERGE / NO_DEPLOY
**Web-only scope:** direct Django/Ninja `/api/v1/logs` with session-cookie authorization; no Vercel BFF routing changes, native-only features, patient data or hosted mutation.
**Baseline:** F08 900-second bearer limit is an unapproved experiment; separate Django session cookie age is 14 days. The Web Preview synthetic bridge forwards Authorization but never Cookie/Set-Cookie.

## 1. Independent RED evidence

[Test-only PR #1301](https://github.com/hraaaaf/IAMINA-MVP/pull/1301) established the following with actual Django HTTP and disposable PostgreSQL 16, exclusively synthetic identities, at test SHA `4915f74d0e1fb2e4154330aad8a4542761f253cb`:

- `POST /api/v1/auth/login` creates both signed native bearer and a Django session cookie.
- A native bearer rejected at the **candidate** 16-minute boundary returns 401, including when a cookie is also sent; the **cookie-only** direct Django `GET /api/v1/logs` continues returning 200. That is an open independent-session-policy gap; does **not** prove Preview cookie forwarding.
- Invalid bearer+valid cookie and conflicting patient bearer+cookie are rejected 401.
- **Critical security RED:** `Client(enforce_csrf_checks=True)` with Django session cookie, **without Authorization and without CSRF token**, sent `POST /api/v1/logs` with a valid synthetic payload `{"blood_sugar":110}`. The server returned **200**, created a synthetic clinical LogEntry, rather than returning 403. [PostgreSQL CI #42375587940](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42375587940): 2931 passed / **1 failed** (this new security oracle) / 4 xfailed / 2 skipped / 138 subtests passed.
- The first version of the CSRF probe had an invalid payload and returned 422; this was **not** used to claim a vulnerability. Correcting the body to valid schema exposed HTTP 200. A browser-exploitable cross-origin attack and hosted BFF behavior are separate, unproven claims.

## 2. Candidate narrow code fix (NOT approved)

Change one auth-boundary file `backend/amina/vercel_session_auth.py`:
`SessionAuth._get_key` must always call `check_iamina_csrf(request)` for its cookie branch, rather than being gated on `self.csrf` and the internal `_ninja_csrf_exempt` marker. Authorization-bearing requests continue to use the separate bearer branch. This is intended to avoid relying on Django's outer CsrfViewMiddleware for Django Ninja routes, which may be exempted during Ninja dispatch. Candidate source commit `547c93dc23feb7891dc0c345d4971f4bd2cd6d32`; do not assume the fix succeeds until fresh HTTP/PG16 results are available.

The primary failing test is **not softened**. Additional safeguards in the fix branch require:
- cookie-only unsafe method with missing CSRF: **403** and zero LogEntry mutation;
- cookie + *valid* CSRF: write succeeds **200**, exactly one authorized row;
- valid CSRF but hostile Origin: **403**, zero mutation;
- explicit bearer-only write without cookie CSRF: **200**, bearer auth unaffected;
- expired native bearer and cookie identity conflicts remain rejected, while cookie-only lifetime is explicitly flagged as `strict=True` XFAIL pending owner policy.

These tests measure Django direct behavior; **the synthetic W01 Preview BFF strips Cookie and Set-Cookie**. The fix must not broaden cookie forwarding or disable CSRF in BFF. Hosted compatibility, same-site behavior and real browser cross-origin exploitability have NOT been evaluated.

## 3. OPEN gates and next exact

1. Exact final-head CI PostgreSQL16 + SQLite, lint, migration drift, Flutter/Chrome/Web FR/AR — all require observed results, no inherited green.
2. Source/diff review, security/CSRF reviewer independent of code author and explicit privacy/UX validation for cookie login and reauthentication.
3. F09 remains unapproved: design for secure refresh, access + cookie TTL, idle/absolute limits and per-session revocation; the XFAIL is **not** F09 acceptance.
4. Confirm test-only PR #1301 stacked on F09 design PR #1300, patch PR #1303 stacked on test-only PR, no temporary diagnostics in final patch; no merge, Vercel Preview/production, Neon mutation, PHI or patient production.

**Verdict until exact-head GREEN and security approval: W02 SECURITY_NO_GO, patient NO-GO.**
