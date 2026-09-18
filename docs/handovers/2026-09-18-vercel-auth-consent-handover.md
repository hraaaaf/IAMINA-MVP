# HANDOVER — IAMINA Vercel dev/test routing → auth → consent

Date: 2026-09-18

Repository: `hraaaaf/IAMINA-MVP`

Canonical previous handover:
`docs/handovers/2026-09-17-vercel-routing-consent-csrf-handover.md`

## GOAL

Make the hosted IAMINA dev/test chain work end-to-end:

`iamina-review` (Flutter) → native IAMINA auth → `iamina-certified` (Django) → PostgreSQL → consent → onboarding → dashboard → AI provider.

Observable success:

1. frontend calls backend paths with exactly one `/api/v1`;
2. signup/login obtains a native IAMINA bearer;
3. authenticated `POST /api/v1/account/consent` returns 2xx;
4. consent screen exits and dashboard loads;
5. onboarding exits its saving state;
6. actual AI provider is proven from runtime evidence.

Do not call this complete before all six are observed.

## PRODUCT SEMANTICS

The Vercel deployments are the shared DEV/TEST environment used to try the app.

Vercel may technically label deployments as target `production`; this must not be treated as IAMINA real production.

True IAMINA production-only gates are controlled separately by `IAMINA_ENV=production`.

## VERIFIED REPO STATE AT HANDOVER

Main:

- `main@5faa480f23e383e7b17f020c83304597d50615c6`
- latest main commit at handover is unrelated nutrition work: `feat(nutrition): add Morocco depth foods batch 24 (#680)`.

Relevant merged fixes:

- #664 — normalize legacy frontend API base suffix.
- #666 — separate IAMINA runtime mode from Vercel target.
- #670 — route Django-Ninja SessionAuth CSRF through IAMINA origin policy.
- #673 — enable native account enrollment for hosted IAMINA review app.

#673 merge commit:

- `0093569e40ad65857bb675fb68cb2b409f9c7b6b`
- CI #4485 SUCCESS.
- Developer portability #152 SUCCESS.

## VERIFIED FRONTEND DEPLOYMENT

Project: `iamina-review`

Project ID:
`prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`

Current tested deployment:

- deployment: `dpl_E3JnCpMpDdyt63tvo8cTaCKTvkTb`
- URL: `iamina-review-15t0d9ywm-achraf-benmoussa-s-projects.vercel.app`
- stable alias: `https://iamina-review.vercel.app`
- exact source SHA: `0093569e40ad65857bb675fb68cb2b409f9c7b6b`
- state: READY
- aliasError: null.

Build evidence:

- Vercel cloned exact commit `0093569`.
- build logged:
  `Building IAMINA web with configured backend: https://iamina-certified.vercel.app`
- Flutter web build completed successfully.
- deployment completed.

The source contract at this commit is intended to inject only backend origin:

`https://iamina-certified.vercel.app`

and Flutter callers append `/api/v1/...`.

#673 also builds the known `iamina-review` project with:

`IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true`

so hosted signup can use the native Django registration endpoint and obtain an IAMINA bearer.

## VERIFIED BACKEND DEPLOYMENT

Project: `iamina-certified`

Project ID:
`prj_Pn9FnyconF3h2w9gOU74iV98kJoU`

Current tested deployment:

- deployment: `dpl_89bM9ipENTXYwzMDheDfFxg942s9`
- URL: `iamina-certified-hxm27juga-achraf-benmoussa-s-projects.vercel.app`
- stable alias: `https://iamina-certified.vercel.app`
- exact source SHA: `1bac5bff2c635dcc6c4f0f0760e518d899991ac2`
- state: READY
- aliasError: null.

Known backend health evidence from this deployment:

- `GET /api/v1/health` returned 200.

## IMPORTANT: CURRENT LIVE BLOCKER

The user reports that after clicking the consent action the UI spins and remains on the same page.

Most important runtime evidence after the frontend redeploy:

At approximately 06:23–06:24 UTC, backend logs on `dpl_89bM9ip...` showed:

- `GET /api/v1/api/v1/profile/locale` → 404
- `POST /api/v1/api/v1/account/consent` → 404 repeatedly.

Therefore the live client used in that test was STILL sending a duplicated `/api/v1/api/v1` path.

This is the highest-priority blocker.

Do not continue debugging CSRF, consent payload, onboarding, or LLM until the active browser/runtime artifact is proven to send exactly one `/api/v1`.

The contradiction is explicit:

- build log for frontend `0093569e...` says backend origin is `https://iamina-certified.vercel.app` with no suffix;
- runtime backend logs after that deploy still show doubled `/api/v1/api/v1`.

This means one of the following must be proven or eliminated rather than guessed:

1. stale browser service worker/cache is serving an older Flutter bundle;
2. stable alias is serving a different artifact than expected;
3. another runtime URL/base composition path exists in the compiled Flutter app;
4. an environment/build-time value is being embedded elsewhere;
5. user was still on an older open tab/session when testing.

## PREVIOUS ERRORS — DO NOT CONFUSE THEM WITH CURRENT BLOCKER

Earlier stages already exposed and partially resolved separate issues:

1. duplicated `/api/v1` → 404;
2. Django CSRF origin mismatch → 403;
3. Django-Ninja own SessionAuth CSRF path bypassed custom origin policy;
4. Vercel technical production target incorrectly activated IAMINA SMTP production gate;
5. hosted frontend could navigate locally without obtaining backend auth.

Relevant fixes are already merged (#664, #666, #670, #673).

The current latest observed failure returned to #1: duplicated routing in the live client.

## AUTH PIPELINE AS DESIGNED

Frontend native auth:

- `AuthService.signInWithEmail()` posts to `/api/v1/auth/login`.
- `AuthService.registerWithEmail()` posts to `/api/v1/auth/register` when `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true`.
- successful native auth accepts `access_token` and stores it.
- `AuthInterceptor` adds `Authorization: Bearer <IAMINA token>` to ApiClient requests.

Backend native auth:

- Django `/auth/register` creates the Django identity + BasePatientProfile.
- Django `/auth/login` authenticates the native account.
- native bearer is verified by HybridBearerAuth / IAMINA token path.

Consent:

- frontend `VersionedConsentApi.giveVersionedConsent()` posts to `/api/v1/account/consent`.
- UI only advances after exact server response verification, secure local evidence persistence, local consent timestamp, then navigation to dashboard.

Thus a spinner with repeated 404s is expected to fail closed and remain on the consent page.

## NEXT EXACT — START HERE IN NEW WINDOW

1. Read this handover.
2. Re-check:
   - repo main HEAD;
   - frontend deployment `dpl_E3JnCpMp...`;
   - backend deployment `dpl_89bM9ip...`.
3. Inspect the actual currently served Flutter artifact from BOTH:
   - stable alias `https://iamina-review.vercel.app`;
   - exact deployment URL.
4. Prove whether the compiled artifact contains:
   - `https://iamina-certified.vercel.app`;
   - `https://iamina-certified.vercel.app/api/v1`;
   - any literal `/api/v1/api/v1`;
   - native register/login paths.
5. Inspect service-worker/cache behavior and versioning. If stable alias or old tab can keep an old bundle, fix cache invalidation/versioning or temporarily disable service-worker caching for this shared dev/test environment.
6. Reproduce with a clean browser context / cache-busted load only after source evidence is clear.
7. Require backend runtime proof:
   - exactly one `/api/v1`;
   - then `/api/v1/auth/register` or `/api/v1/auth/login`;
   - then authenticated `POST /api/v1/account/consent`.
8. Only after routing is correct:
   - diagnose any 401/403;
   - verify consent 2xx;
   - verify dashboard navigation;
   - verify onboarding;
   - verify actual AI provider.

## TEST ORDER — DO NOT SKIP AHEAD

A. Frontend artifact identity
B. Browser/service-worker cache
C. URL composition
D. native signup/login request
E. bearer issuance and storage
F. authenticated locale/consent request
G. CSRF/auth response
H. consent persistence
I. dashboard navigation
J. onboarding completion
K. AI chat request
L. provider/model runtime proof.

## SAFETY / GATES

- No Vercel redeploy without explicit user authorization.
- No direct mutation of a possibly shared PostgreSQL DB for debugging.
- Normal user-driven signup/login/consent in the dev/test app is allowed.
- Do not expose credentials or tokens.
- Do not claim Groq or any other LLM is active until runtime evidence proves it.
- Do not call the lot fixed merely because source code looks correct.

## COMPLETION CONDITION

This lot closes only when runtime evidence proves:

- frontend active artifact is the intended one;
- no duplicated `/api/v1`;
- native auth request occurs;
- valid IAMINA bearer is used;
- consent returns 2xx;
- consent screen exits;
- onboarding completes;
- dashboard is usable;
- AI request succeeds or fails with a separately diagnosed provider-layer reason;
- real provider/model is identified from evidence.
