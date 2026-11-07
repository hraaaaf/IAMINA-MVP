# W02-F09 — Django clinical cookie CSRF boundary (RED → PG16 GREEN, global NO-GO)

**Date:** 2026-11-07
**Status:** TARGETED_CSRF_PG16_GREEN / FULL_CI_RED_F05B / D19_FUE_RED / F09_POLICY_NOT_APPROVED / DRAFT / NO_MERGE / NO_DEPLOY
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

One production auth-boundary file changed: `backend/amina/vercel_session_auth.py` (no migration, no production data). **The first strategy — only changing `SessionAuth._get_key` — was REJECTED by real PG16 CI**: at SHA `c1753902d3648832499a4b9709b19aa3096e2c26`, cookie-only clinical POST without CSRF and cookie+hostile Origin both still returned HTTP 200 and created synthetic rows ([CI #42376985022](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42376985022), PG16 2,934 pass / 2 fail / 4 xfail / 2 skip). This is a measured fail, not a resolved incident.

**Successful second strategy:** enforce `check_iamina_csrf(request)` from `ExplicitBearerCookieIdentityMiddleware.process_view` for `/api/v1/` requests **before Django Ninja view dispatch** when Django has authenticated an actual cookie session and no explicit bearer header is present. Invalid/missing CSRF or hostile Origin must block the request before mutation, including public auth-route cookie logout. Retain the secondary `SessionAuth` guard and an explicit no-cookie/no-bearer 401 path. A verified bearer remains separate and does not need a browser CSRF token. Production code change SHA `41332e69aabc5b7cdc5f20662841a511a125568f`; tests SHA `1ecd6d375c597b73b2b73a6f13d4304a6d93eb0c`. No claim is made about browser-exploitable external CSRF without independent browser-origin testing.

The primary failing test is **not softened**. Additional safeguards in the fix branch require:
- cookie-only unsafe method with missing CSRF: **403** and zero LogEntry mutation;
- cookie + *valid* CSRF: write succeeds **200**, exactly one authorized row;
- valid CSRF but hostile Origin: **403**, zero mutation;
- explicit bearer-only write without cookie CSRF: **200**, bearer auth unaffected;
- expired native bearer and cookie identity conflicts remain rejected, while cookie-only lifetime is explicitly flagged as `strict=True` XFAIL pending owner policy.

These tests measure Django direct behavior; **the synthetic W01 Preview BFF strips Cookie and Set-Cookie**. The fix must not broaden cookie forwarding or disable CSRF in BFF. Hosted compatibility, same-site behavior and real browser cross-origin exploitability have NOT been evaluated.

## 3. Exact-sha CI evidence and remaining failures

**Proof on exact code SHA `1ecd6d375c597b73b2b73a6f13d4304a6d93eb0c`:**
- [CI #42377812522](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42377812522) — backend SQLite: **2,935 PASS / 0 FAIL / 5 SKIP / 4 XFAIL**; Ruff, import architecture, egress anti-bypass, Bandit/SAST and OpenAPI contract PASS.
- Same CI — **PostgreSQL 16: 2,938 PASS / 0 FAIL / 2 SKIP / 4 XFAIL**, including 138 subtests PASS and migrations. Real HTTP tests require: cookie-only unsafe write without CSRF -> 403 & zero mutation; valid CSRF -> 200 & one row; hostile Origin with otherwise valid CSRF -> 403; bearer-only write -> 200; anonymous write -> 401; cookie-only logout without CSRF -> 403 and bearer unrevoked; logout with valid CSRF -> 200 and bearer revoked.
- D30 local-first and W01/W02 targeted workflow evidence must be inspected by exact SHA rather than inherited from unrelated commits.
- **CI Flutter is a separate existing F05B FAIL**: 1,003 PASS / 1 FAIL (permanently failing secure-storage token delete and fence write) / 9 SKIP; self-contained PWA build behind the failing test is NOT certified.
- [D19 Web PG16 #42377812466](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42377812466) is a separate FUE FAILURE; previous exact SHA `c1753902` showed 9/9 expected titles PASS, HTTP login 200, no console errors, but 2 observed clinical requests vs `tools/d19_real_auth_summary_pg_browser_check.js` hard-coded `requests.length >= 4`. Both `ApiClient.getAiSummary` and `getKpis` make a single distinct API call. This suggests a stale threshold, **not** proof that the patient clinical screen was adequately verified: do not simply relax this gate without checking actual rendered data and each HTTP status. D19 still NO-GO.

**Quality/adversarial self-review:** target CSRF test proof is strong but **the W02-F09 LOT cannot be VERIFIED**. `EXECUTION_SCORE=8.0/10` (PG16/SQLite direct HTTP successful but browser/session policy incomplete), `ADVERSARIAL_SCORE=5.9/10` (blocking independent TTL/cookie authorization path and F05B; no independent security review), **retained score 5.9/10 / NO_GO** under the policy's security-blocker cap. This is a same-executor provisional review, not an independent signoff.

## 4. OPEN gates and next exact

1. CSRF direct HTTP PG16/SQLite GREEN at code SHA 1ecd6d; **after this documentation commit exact HEAD CI must be refreshed**; D19 FR/AR and Flutter F05B remain RED, browser CSRF FUE NOT_RUN. No green can be inherited for release.
2. Source/diff review, security/CSRF reviewer independent of code author and explicit privacy/UX validation for cookie login and reauthentication.
3. F09 remains unapproved: design for secure refresh, access + cookie TTL, idle/absolute limits and per-session revocation; the XFAIL is **not** F09 acceptance.
4. Confirm test-only PR #1301 stacked on F09 design PR #1300, patch PR #1303 stacked on test-only PR, no temporary diagnostics in final patch; no merge, Vercel Preview/production, Neon mutation, PHI or patient production.

**Verdict: narrow direct-Django cookie CSRF fix GREEN on disposable PG16 / SQLite, but full W02-F09 remains SECURITY_NO_GO (F05B, D19 FUE, session TTL, independent review and real browser gates). Patient NO-GO; no Vercel, Neon, or merge.**
