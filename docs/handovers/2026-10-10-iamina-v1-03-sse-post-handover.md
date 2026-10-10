# IAMINA V1-03 — SSE POST privacy #925 — 2026-10-10

**Authority:** docs/ROADMAP.md remains the canonical roadmap. This is the technical continuation file for [PR #926](https://github.com/hraaaaf/IAMINA-MVP/pull/926), stacked on draft [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922).

## Goal — success — evidence

**Goal:** keep free-form patient chat text out of request URLs and preserve deterministic emergency SSE, patient-specific deferred AI egress authorization, and no unexpected sensitive logging.

**Success:** POST JSON ChatRequest (not GET query), Flutter SSE token/DONE contract for ordinary/urgent chat, per-next patient TEXT egress scope resetting between yields, closing deferred provider iterator within authorized scope, no-store caching, denied global consent and no patient messages in exception/emergency logs.

**Verified code-only baseline:** HEAD 44d6c27dd3aaa4bf5b60bdac6e112efba92a523c, [CI #38069507466](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38069507466) **15/15 SUCCESS**: SQLite 2831 passed/5 skipped/3 xfailed; PostgreSQL 2835 passed/1 skipped/3 xfailed; Flutter 660 passed/1 skipped; PWA, iOS/mobile, browser and all other workflows success. Prior CI #38068847596 found two old direct str-based SSE tests; fixed tests-only in 44d6c27. This new test/documentation commit requires **its own exact-head CI**; do not claim that the old CI covers it.

## Session CSRF red / root-cause hardening

The newly added Django Client(enforce_csrf_checks=True) regression on candidate 1bc5cb returned HTTP 200 **without CSRF token** for an authenticated session POST, so **that candidate is red and unsafe to certify** ([CI #38070369320](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38070369320), backend SQLite failure, other jobs may still run). Source review: Django-Ninja session fallback may be skipped by an operation-scoped _ninja_csrf_exempt flag; IAMINA's existing SessionAuth had a conditional skip; CsrfExemptApiMiddleware also exempted any bearer-looking HTTP header at Django middleware level, which could allow an invalid bearer to fall back to session without CSRF. No real-patient exploit or incident established.

The following **candidate, not yet certified** hardening changes require new exact-head CI: SessionAuth checks CSRF on *all unsafe cookie-session requests*, regardless of Ninja operation flag, but skips checking requests that do not actually have a session cookie. The check temporarily ignores prior bearer-looking-header CSRF bypass and restores the original request flag afterward; a forged invalid bearer can no longer waive cookie-session CSRF. New synthetic tests expect 403 without token, 403 with invalid bearer header, 200 with valid cookie+CSRF token. Existing bearer-only authentication is still not subject to cookie CSRF. Do not merge/release until exact-head backend and full workflows succeed.

## Reviewed changes

- backend/ai/api/v1/ai.py — POST JSON SSE, deferred per-next scoped egress, sanitized error logs.
- backend/core/middleware/triage_vital.py — urgent POST yields canonical deterministic SSE instead of JSON; emergency log excludes raw patient text and user ID.
- frontend/lib/services/api_client.dart — constant path POST JSON body, bearer if present.
- docs/api/openapi.json — POST schema; prior code CI validated generated OpenAPI.
- backend/core/tests/test_v1_03_sse_post_privacy.py, test_input_safety.py — client contract, consent, egress, urgent, logs; latest tests add disconnect and session CSRF.
- frontend/test/services/v1_03_sse_privacy_contract_test.dart — actual request builder method, body and URL verified.

Parent branch security/v1-03-summary-local-only-20261010 at cce2b5716d59add380846f3b3a18ef84e33fa41c. PR #926 is DRAFT and **temporarily based on main for CI** because workflow PR triggers target main/dev. Restore base after exact-head CI and recheck diff.

## Remaining / exact continuation

1. Run and inspect **all workflows on the new exact HEAD**; fix red, repeat as required. Confirm post-change code and tests. 
2. Restore PR #926 base to security/v1-03-summary-local-only-20261010; confirm DRAFT/unmerged and limited diff; sync [Notion master](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6), PR and [issue #925](https://github.com/hraaaaf/IAMINA-MVP/issues/925).
3. Verify production ingress/proxy request-body log hygiene, Flutter session-only CSRF/bearer behavior, backwards compatibility for existing GET clients (now 405) and rollout/rollback; independent privacy/security review.
4. **Human gates remain:** clinician OCR unknown glucose unit semantics [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923); product/privacy local vs global AI withdrawal and multidevice persistence [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924); CNDP/processor, native FR/AR/Darija-RTL, accessibility, P5-6A/B and release approvals.

**No merge, Vercel deployment or real-patient release authorized.** V1 product decisions 29/29 approved, 0/29 fully delivered.
