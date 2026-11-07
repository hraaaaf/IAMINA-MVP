# IAMINA W02-F09 — Hosted Preview origin + synthetic two-tab gate

Date 2026-11-07 · Web only · C7+C8+C9 parent `9a31d343003406781c3e57347d7827a9f9704c9c` · branch `test/w02-f09-hosted-preview-e2e-20261107` · Vercel PREVIEW authorized by owner, Production and Neon DDL NOT authorized.

## GOAL / SUCCESS / PROOF
**GOAL:** eliminate the obsolete W01 `API_BASE_URL` from W02 Web Preview builds while preserving fail-closed Vercel OIDC BFF routing. Exercise the actual Flutter C8 code in a separate browser-only synthetic probe path without mounting C7 or changing the production clinical `AuthService`. Prove the web site is buildable, proper URLs are selected by Vercel system vars, and two browser tabs clear RAM tokens after logout/reload.
**SUCCESS:** immutable `VERCEL_URL` for exact `iamina-review` project, Vercel environment `preview` only; reject alias/project/header/URL injection and Production; full native Flutter main remains normal. No clinical endpoint registered, `/api/v1/auth/refresh` deny-only. Publish separate `__w02_f09_probe` ONLY for this dedicated preview branch (test-only synthetic tokens, not backed by Django). Two-tab Chromium/WebKit test in CI, exact HEAD and logs. Only afterward manual Vercel Preview deploy; never merge or deploy Production.
**PROOF:** `.github/workflows/w02-f09-hosted-preview-origin-browser.yml` and `tools/w02_f09_hosted_preview_origin.test.js`; CI run and preview URL to be added AFTER verification.

## PRE-FLIGHT DATABASE GATE — MATERIAL LIMITATION
On 2026-11-07 the already established Neon project `noisy-truth-00115950`, branch `br-sweet-frog-b9ok6ptp` `synthetic-only`, DB `iamina925_empty`, read-only SQL with role `iamina_preview_app` confirmed PostgreSQL `core_webrefreshfamily` **ABSENT** and `core_webrefreshconsumedsecret` **ABSENT** (zero `core_webrefresh%` tables). Vercel backend Preview `IAMINA_EXPECTED_DB_ROLE=iamina_preview_app` and `IAMINA_EXPECTED_DB_NAME=iamina925_empty`; Vercel `DATABASE_URL` is protected and not proven cryptographically against the branch just from env metadata. No patient records were queried. **DO NOT run migrations or issue C7 sessions against Neon without separate explicit database schema authorization.** The W01 synthetic branch is not automatically compatible with C7.

## CHANGES / SECURITY PROPERTIES
- `frontend/scripts/w02_preview_origin.sh`: pure Bash resolvent of immutable preview host. Rejects project/env/domain/alias mismatch; no network, no fallback.
- `frontend/vercel_build.sh`: Preview `API_BASE_URL` becomes `https://${VERCEL_URL}` via strict resolver, never previous W01 deployment alias; Production unchanged. For exact test branch and only Vercel Preview, compiles a second Flutter static bundle at `/__w02_f09_probe/` containing only C8 synthetic two-tab diagnostic. The normal IAMINA app remains default `/`.
- `scripts/w02_f09_c9_real_browser_probe.py`: accepts optional nested test-only origin while default is local. Does not access the real API.
- `tools/w02_f09_hosted_preview_origin.test.js`: injection, bad project/env, production and non-mounted refresh contracts.
- `.github/workflows/w02-f09-hosted-preview-origin-browser.yml`: shell+Node, Flutter, real local Chromium+WebKit E2E for fixture; synthetic only, anonymized proof artifact.

## IMPORTANT LIMITATIONS / HUMAN GATES
**This is not a passing C7 hosted authenticated E2E.** The C7 PG16 issuance/CSRF/OIDC/nonce code is unmounted, C8 is not connected to production AuthService, the preview backend database does not have the required refresh tables, and the browser-only fixture uses simulated tokens. Do not misrepresent a real-browser test of the fixture as a real clinical login. Vercel Backend preview identity/source and TLS/HTTP deny-only checks can be done read-only, but no patient data, Neon DDL, live token/cookie routes, rollout or merge.

**NEXT exact:** CI exact HEAD; manual Preview to `iamina-review` exact SHA; if isolated backend metadata and no write remain safe, deploy backend Preview code unmounted, verify health fingerprint only. Execute 2-tab hosted fixture as browser infrastructure allows. A true C7→C8 authenticated refresh requires explicit Neon synthetic-schema migration authorization and independent security review of the mounted endpoints and their runtime secrets.