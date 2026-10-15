# IAMINA V1-03 — SSE POST/JSON cutover: evidence and release gates

**State: DRAFT / NOT RELEASE AUTHORIZED.** This is the preparation for [#925](https://github.com/hraaaaf/IAMINA-MVP/issues/925), not a production migration or clinical certification.

## Goal → observable success → proof

- **Goal:** remove all patient-authored SSE messages from URL path/query, preserve authenticated deterministic urgent/insulin SSE behavior and ensure external provider calls are in their patient's consent/egress scope when Django consumes streaming output after the view has returned.
- **Success:** new client transmits `POST /api/v1/ai/chat/stream` with JSON `message`/`context_days`; GET returns 405 without redirect; no query/fragment; auth 401, session-cookie CSRF 403 with forged bearer; positive urgent SSE and medication refusal return `[DONE]` without LLM; interleaved patients remain isolated and denied consent cannot enter the provider; Flutter unit tests, Django/PGSQL/SQLite and OpenAPI all green on the same HEAD.
- **Proof sources:** frozen baseline `main@f41778fcb1cfb0608de2b11e37fe290afc1332e9`; draft branch [PR #1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056); negative tests `backend/core/tests/test_sse_post_privacy.py`, `backend/core/tests/test_input_safety.py`, `frontend/test/services/sse_post_transport_contract_test.dart`. Exact-head CI links/results belong in the PR after execution. No clinical release score from merely static checks.

## Source-level BEFORE → candidate AFTER

| Contract | BEFORE | Candidate AFTER |
| --- | --- | --- |
| SSE HTTP | GET, `message` in URL query | POST JSON; GET refuses without compatibility redirect |
| Flutter client | raw message in `Uri.replace(queryParameters)` | request body JSON with query/fragment rejected |
| Streaming consent scope | decorator spans view function only, not later generator consumption | distinct scope around each lazy `next()` and `.close()`, reset before outgoing SSE yield |
| Emergency | GET bypasses POST triage middleware; generic SSE fast-path | POST bypasses pre-auth middleware; authenticated view uses canonical deterministic emergency composer and SSE event + `[DONE]` |
| Medication refusal | deterministic response without provider call | same deterministic gate, SSE + `[DONE]`, `Cache-Control: no-store` |
| Cookie + forged Bearer | generic middleware can set a CSRF exempt flag before bearer is verified | SSE view forces cookie-session CSRF validation even if Bearer-looking header exists |

## In-scope adversarial checks

1. **URL leakage:** synthetic PHI canary appears only inside request body, never path, query, redirect, analytics breadcrumb, API logs or provider invocation.
2. **Transport:** method/Content-Type/Accept/body correct; auth cookie/bearer, timeouts, auth-epoch reset, app-lock, no-store and `[DONE]` semantics retained.
3. **Urgent safety:** canonical deterministic composer, no untrusted LLM; `TriageVitalMiddleware` does not intercept SSE into incompatible JSON prior to Ninja authentication.
4. **Consent/patient isolation:** verify actual deferred generator `next()` and cleanup/disconnect, consent-off and patient A→B→A interleaving, exact purpose/modality. `ai_egress_scope` is not *by itself* a provider approval.
5. **CSRF:** cookie+forged Bearer MUST 403 if no CSRF token; no global exemption, genuine browser session can be tested with valid token.
6. **Convergence:** backend SQLite/PostgreSQL, Flutter test/analyze/PWA build, OpenAPI, E2E synthetic local chat and pilot rehearsal; no feature activation, unreviewed language or physical device claim.

## Real cutover gate: breaking GET clients

**Human decision required before merge/release:** GET→POST with 405 for GET intentionally breaks older Flutter/PWA/mobile builds. Never silently reintroduce GET+message for compatibility. Inventory active client versions from authorized release metadata (no personal data); map minimum supported build and server build digest; verify web cache/service worker can pick up POST bundle; decide explicit upgrade notice and rollback procedure. A rollback MUST NOT re-enable a PHI-bearing GET endpoint in any real-patient runtime. Until proof exists, keep this PR DRAFT and do not deploy.

**Rollout policy:** this is dev/cert preparation only. If later approved, freeze matched frontend/backend SHA and deploy through a separate explicitly authorized release process with synthetic ingress URL-log checks, fail-closed old clients, monitoring with no raw content and documented rollback. Vercel deployment is specifically unauthorized for this task.

## Residual boundaries

- This transport fix **does not authorize** external LLMs to see raw patient text/clinical facts. Canonical V1-03 requires generic/opaque allowlisted content or no LLM; provider policy, consent, clinical model authority, D31 physical proof and legal/CNDP review remain separate.
- Source-level review is by one GPT session, not independent Builder/Reviewer/Certifier identities or the genuine 15-agent council (#1029). No human medical/regulatory certification claimed.
- Repository #1038 branch governance remains open. No real patient data, no expense, no new model provider and no Vercel.

## Standards

- OWASP REST Security — sensitive fields in POST body rather than URLs: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Logging — avoid sensitive personal health data in logs: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Django StreamingHttpResponse — stream consumed after handler return: https://docs.djangoproject.com/en/5.2/ref/request-response/
- Django CSRF request protections: https://docs.djangoproject.com/en/5.2/topics/security/

## Next exact

Read exact-head CI, repair any failing test without weakening gates, reconfirm all touched diffs and rerun. Obtain separate reviewer + certifier and explicit client cutover acceptance before converting to mergeable; no automatic merge or deployment.