# HANDOVER — IAMINA Vercel routing + consent CSRF

Date: 2026-09-17

Repository: `hraaaaf/IAMINA-MVP`

Primary active branch: `fix/vercel-routing-isolation-20260917`

Primary open PR: #659 — `fix(vercel): isolate frontend/backend routing contracts`

## GOAL

Make the production chain reliable and explicit:

`iamina-review` (Flutter) → `iamina-certified` (Django) → PostgreSQL → LLM provider

Immediate success criteria:

- `iamina-review` builds only the Flutter frontend.
- `iamina-certified` builds only Django/Python.
- frontend API base is the backend origin only; callers append `/api/v1/...` exactly once.
- consent POST reaches `/api/v1/account/consent` and returns 2xx instead of 403.
- onboarding no longer remains indefinitely on `Enregistrement…`.
- no production Vercel deployment without explicit human authorization.
- after consent is fixed, test dashboard + `/api/v1/ai/chat` and prove the actual LLM provider from runtime evidence.

## VERIFIED CURRENT PRODUCTION STATE

### Frontend — `iamina-review`

Project ID: `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`

Latest redeploy verified READY:

- deployment: `dpl_Bdzc5Qj27iX7RUXzuiz7nc3VKKHe`
- production alias: `https://iamina-review.vercel.app`
- source commit: `50ea288ae68a2b2f8c2a3d2c791ae39f4daad094`
- source PR: #658 — merged
- source change: backend base injected as `https://iamina-certified.vercel.app` (origin only, no embedded `/api/v1`)

PR #658 is already merged. Do not treat it as pending.

### Backend — `iamina-certified`

Project ID: `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`

Verified production deployment:

- deployment: `dpl_AUrXMmDbq7B5P9kFJhbNbLzBb2iZ`
- alias: `https://iamina-certified.vercel.app`
- commit: `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`
- `/api/v1/health` returned HTTP 200 with `status=ok`, `db=ok`, `cache=unavailable`

This proves Django is live and PostgreSQL connectivity is healthy. It does not prove Groq.

## ROOT CAUSE ALREADY FIXED — DOUBLE `/api/v1`

Old frontend build injected:

`https://iamina-certified.vercel.app/api/v1`

while Flutter services also appended `/api/v1/...`, producing broken paths such as:

`/api/v1/api/v1/account/consent`

Runtime evidence before the fix showed requests on duplicated paths.

PR #658 fixed this and is merged. Current frontend production redeploy uses the corrected commit `50ea288…`.

## NEW VERIFIED BLOCKER — CSRF TRUSTED ORIGIN

After the corrected frontend redeploy, the consent button now reaches the correct backend endpoint.

Runtime evidence on `iamina-certified`:

- `POST /api/v1/account/consent` received 3 times
- all returned HTTP 403
- Django log:

`Forbidden (Origin checking failed - https://iamina-review-cyutt5fcm-achraf-benmoussa-s-projects.vercel.app does not match any trusted origins.)`

Therefore:

- routing is now correct for consent;
- the current blocker is Django origin trust / CSRF configuration;
- the failing origin is the concrete Vercel frontend deployment hostname, not the stable alias.

## REQUIRED NEXT FIX

Audit backend Django settings for:

- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS` / regex equivalents
- any production environment overrides

Goal of the fix:

- keep stable frontend origin trusted: `https://iamina-review.vercel.app`
- safely support legitimate `iamina-review-*.vercel.app` deployment/preview hostnames without broadly trusting unrelated `*.vercel.app` origins
- add regression tests for trusted frontend origins
- do not deploy backend until explicit user authorization

Do not assume CORS alone is enough: the observed runtime error is specifically Django CSRF origin checking.

## OPEN PR #659

Branch: `fix/vercel-routing-isolation-20260917`

PR #659 status at handover creation:

- open
- draft
- mergeable
- HEAD before this handover commit: `c71edf62927d1c9ba967f5c4181281cd7dba2d44`

PR body currently includes:

- fail-closed Flutter Vercel project ID guard
- `CompanionService` reuse of canonical frontend API origin
- onboarding local persistence timeout/recovery
- regression tests

Do not merge #659 automatically without re-checking its current diff, CI, and Vercel production implications. A merge may trigger production deployment through Git integration.

## ONBOARDING `Enregistrement…` ISSUE

Separate from the consent 403.

Verified code path previously inspected:

- final onboarding save performs local preference persistence / secure storage / Drift before navigating to `/dashboard`
- this path is not primarily a Django network call
- PR #659 adds bounded persistence and `_saving` recovery so the UI cannot remain stuck indefinitely after a local persistence timeout/failure

This must be retested after the routing/CSRF work because the user observed both issues during the same setup flow.

## LLM / GROQ STATUS

Not yet verified.

Do not claim Groq is live merely because Django health or dashboard loads.

After consent/onboarding works:

1. send an authenticated message through `/api/v1/ai/chat`
2. inspect backend source/provider selection
3. inspect runtime logs for provider/model evidence
4. only then state whether Groq is actually serving the request

## SYSTEMIC ROUTING AUDIT — STILL RELEVANT

Both Vercel projects are connected to the same monorepo and have received Git-triggered deployments from the same repository history.

This proves trigger overlap exists; it does not by itself prove the wrong artifact was built on every deployment.

Continue auditing:

- Root Directory for both Vercel projects
- build commands
- Git deployment / ignore rules
- project-specific environment variables
- frontend API URL construction
- backend URL prefixes
- CSRF/CORS configuration

Target architecture remains strict:

- `iamina-review` → Flutter only
- `iamina-certified` → Django only
- Django → PostgreSQL + approved LLM provider

## DO NOT DO

- Do not request or expose API secrets.
- Do not claim Groq is verified without runtime/provider evidence.
- Do not redeploy Vercel production without explicit authorization.
- Do not reintroduce an API base containing `/api/v1`.
- Do not trust all `*.vercel.app` origins globally unless a narrow project-specific pattern is impossible and the security trade-off is explicitly reviewed.

## NEXT EXACT

1. Read this handover.
2. Re-check repo `main`, PR #659 HEAD, CI and current Vercel deployment states.
3. Locate Django CSRF/CORS settings and their tests.
4. Implement the narrow frontend-origin trust fix on an appropriate branch.
5. Run focused backend tests + normal CI.
6. Stop at the Vercel backend deployment gate and ask for explicit authorization.
7. After deploy: retest `POST /api/v1/account/consent` and require 2xx runtime proof.
8. Retest onboarding completion to `/dashboard`.
9. Test `/api/v1/ai/chat` and prove the real LLM provider.

## COMPLETION CONDITION

This routing/consent lot is not complete until all of the following are proven:

- consent endpoint 2xx from the production frontend origin
- no duplicated `/api/v1`
- onboarding exits `Enregistrement…` and reaches dashboard
- frontend/backend project isolation remains intact
- CI green on exact merged candidate
- production deployment(s) identified and verified
- actual LLM provider traced separately before claiming Groq success
