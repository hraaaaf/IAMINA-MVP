# IAMINA — Handover V1-03 / #925 — SSE POST privacy and deferred AI scope

**Snapshot:** 2026-10-15, after GitHub/CI recheck. **Status: PREPARED IN DRAFT; NOT MERGED; NOT RELEASE AUTHORIZED.** This is an engineering handover, not clinical/regulatory certification.

## Goal → success → proof

- **Goal:** remove free-form patient messages from SSE URL query strings; keep emergency and prescription/insulin refusals deterministic and authenticated; ensure the real deferred generator executes under exactly one patient's AI-egress context, without bypassing consent.
- **Observable success:** SSE `POST /api/v1/ai/chat/stream` JSON with `message/context_days`, legacy GET → 405; Flutter POST body and no URL query/fragment; authenticated/CSRF-safe clinical SSE `data:` plus `[DONE]`; denied consent fails closed; A/B patient context separation with reset; same-SHA SQLite, PostgreSQL, Flutter, OpenAPI, SAST and E2E.
- **Evidence source:** [#925](https://github.com/hraaaaf/IAMINA-MVP/issues/925) and [draft PR #1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056). No real patients or model calls in test data.

## Exact Git state at snapshot

- **Repo:** `hraaaaf/IAMINA-MVP`.
- **Current main:** `0851cdf014f559aa31a84884b4e49876e8638275` (branch `protected:false`, repo rulesets `[]` on 2026-10-15).
- **PR #1056 branch:** `fix/v1-03-post-sse-egress-925-20261015`; **pre-handover code SHA** `496a685ba23047ce27742750af5476b8d0918144`.
- **PR target:** `main`; original frozen base `f41778fcb1cfb0608de2b11e37fe290afc1332e9`.
- **Divergence compared with current main:** head 6 commits ahead and 3 behind; GitHub REST reported `mergeable=true`, `mergeable_state=clean` **at snapshot only**. No rebase or merge done. The documentation commit containing this handover will produce a **new branch HEAD**; resolve it from GitHub rather than citing `496a685ba23047ce27742750af5476b8d0918144` for future CI.
- **Prior engineering docs:** `docs/security/2026-10-15-sse-post-migration-gates.md`; previous security closeout `docs/security/2026-10-15-patient-logging-redaction-verification.md`; agent-council register `docs/agent-council/2026-10-15-single-executor-specialist-reviews.md`.

## Completed engineering work on #1056 (source inspection)

1. `backend/ai/api/v1/ai.py`: old SSE GET replaced by POST `ChatRequest` JSON, 405 GET; no URL redirect; canonical `compose_emergency_for_patient` SSE + `[DONE]`, deterministic insulin refusal; response `no-store`; explicit per-patient `ai_egress_scope` at each lazy generator `next()` and `close()`.
2. `frontend/lib/services/api_client.dart`: `buildChatStreamPostRequest` builds POST JSON; rejects URL query/fragment; `chatStream` retains auth-epoch, app-lock, timeout and SSE token parsing.
3. `backend/core/middleware/triage_vital.py`: SSE bypasses pre-auth JSON emergency interception; authenticated Ninja view owns deterministic urgency.
4. `backend/core/tests/test_sse_post_privacy.py`: 8 tests (GET 405, anon POST denial, forged bearer cookie CSRF 403, valid-session CSRF emergency SSE, urgent provider-free, insulin provider-free, interleaved A/B scopes, denied-consent gate).
5. `backend/core/tests/test_input_safety.py` and `backend/core/tests/test_chat_log_privacy.py`: legacy test calls updated for `ChatRequest` and POST; existing canary privacy maintained.
6. `frontend/test/services/sse_post_transport_contract_test.dart`: POST JSON with synthetic medical canary, URL query/fragment denied.
7. `docs/api/openapi.json`: generated contract snapshot aligned to POST. `docs/security/2026-10-15-sse-post-migration-gates.md` documents semantics and release gates.

**Perfection/adversarial items not yet discharged:** verify real browser-to-backend **POST SSE** (the green 'Companion real chat E2E screenshots' is not by itself evidence that the streaming transport was exercised), middleware/auth with both session and bearer, request/access-log hygiene with synthetic canary, disconnect mid-stream and scope cleanup under real streaming server conditions, and clinician/native triage response parity. An explicit independent reviewer and release certifier are not demonstrated here.

## Exact-head code CI — GREEN on pre-handover head `496a685ba23047ce27742750af5476b8d0918144`

| Workflow | Run | Verified outcome |
| --- | --- | --- |
| CI | [#38717063878](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717063878) | SUCCESS; Ruff, SAST, egress anti-bypass, SQLite **2829 passed / 5 skipped / 3 xfailed**, PostgreSQL **2833 passed / 1 skipped / 3 xfailed**, 121 subtests each, Flutter analyze+tests+PWA build SUCCESS |
| Django migration drift | [#38717063843](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717063843) | SUCCESS |
| Synthetic pilot rehearsal | [#38717063770](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717063770) | SUCCESS |
| Companion chat browser E2E | [#38717063862](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717063862) | SUCCESS (not proof of POST SSE end-to-end specifically) |

Previous draft SHAs had test/lint failures and cancelled superseded runs, subsequently addressed. **Never transfer these green results automatically to the forthcoming documentation-only HEAD or a later rebased/merged SHA.**

## Critical correction: owner says **zero installed clients**

The project owner explicitly stated on [#925](https://github.com/hraaaaf/IAMINA-MVP/issues/925#issuecomment-6126173521), 2026-10-12: **IAMINA has 0 clients**; Vercel review/cert is development/certification, not patient production. A reviewed bundle had no `chat/stream` use and the active path was `POST /ai/chat`. This is an owner-supplied assertion recorded in GitHub; **do not invent an installed legacy-client fleet, real-patient incidents or data leaks.**

- **Actual decision/gate:** demonstrate first **clean synthetic installation** and matching backend/frontend deployment contract before any first real patient; verify old GET fails closed, POST works, and service worker cache does not revive GET.
- **Cutover risk remains:** the endpoint is breaking for any old build, but there is no current installed client migration plan to execute. If evidence of an actual installed fleet emerges later, update the gate rather than silently assuming compatibility.
- **No Vercel deploy without explicit approval**. A rollback must not introduce patient text back into URLs.

## Wider IAMINA state (do not conflate)

- Earlier privacy logging fixes [#1036](https://github.com/hraaaaf/IAMINA-MVP/pull/1036), [#1050](https://github.com/hraaaaf/IAMINA-MVP/pull/1050), [#1041](https://github.com/hraaaaf/IAMINA-MVP/pull/1041): merged, postmerge CI passed, #1035/#1049/#1040 closed; the security evidence markdown is in `main`.
- **#1029** genuine council 15 independent subagents: **0/15** executed; 15 same-session reviews recorded, not 15 independent agents.
- **#1038** `main` branch protection not yet enabled. Governance requires administrative policy decision.
- Clinical, legal/CNDP, native languages and real device **D31** gates remain independent. AI models have **no** autonomous clinical authority. V1-03 prohibits patient information going to third-party LLMs regardless of a valid scope.
- Canonical P5 roadmap history is **6/12 = 50%**; no new patient-production release candidate and no Vercel deployment.

## Next exact (for new conversation or autonomous continuation)

1. Read this handover and `docs/security/2026-10-15-sse-post-migration-gates.md`; **verify `main` and PR #1056 branch SHA, compare head/base and exact-head CI anew**, because both may advance.
2. Verify the changed security/clinical/Flutter/OpenAPI files and synthetic test collection; inspect backend PG, SQLite, Flutter/PWA, migration and E2E jobs **by SHA**. If docs-only handover commit changed SHA, let its new CI complete and distinguish scoped/skipped jobs from the prior full suites.
3. Reconcile any drift against `main` on **a short-lived isolated candidate** with no unrelated D10/D11 merges; rerun relevant tests if code changes. Do not edit/force-push `main`.
4. Prove POST SSE in a synthetic end-to-end client/server flow and request-log canary absence; test both valid/invalid CSRF, A/B interleaving, disconnect and refusal under stream iteration. Never use a real patient or make external patient LLM calls.
5. Record separate security, clinical-safety and release-certifier reviews. **Owner's 0-client statement is the baseline**: require first clean-install/cached-bundle/rollback proof, not fictional legacy client inventory.
6. Keep #1056 **DRAFT / NO MERGE** until these actual gates pass and the first-release contract decision is confirmed; no Vercel without explicit approval. Update this .md, issue #925, PR and Notion with observed evidence.
7. After genuine approval and merge later: SHA-locked merge, postmerge `main` CI and migration drift, exact-front/backend client contract readback, canonical docs/roadmap; only then close #925. Then return to #1029 and other open gates.

**Stop condition now:** handover is requested; PR #1056 is deliberately not merged due to security-sensitive clinical/auth/API cutover and missing independent/human gates. Do not claim whole-app certification.

**Resume prompt:** “Reprends IAMINA #925 sur la PR #1056. Lis `docs/handovers/2026-10-15-v1-03-sse-post-925-handover.md` puis `docs/security/2026-10-15-sse-post-migration-gates.md`. Vérifie `main`, HEAD PR et CI exacts avant d'agir, respecte 0 client, ne merge ni déploie sans vrais gates.”

## 2026-10-15 continuation — fresh exact-head CI required

- Pre-change PR HEAD `f5ee38067793c4af5bf8d5a62d8c471455f92dc3`, main `0851cdf014f559aa31a84884b4e49876e8638275`: 7 ahead/3 behind. The three main-only commits touch D10 iOS backup/config/tests, with no path overlap with #925; no reconciliation merge was performed.
- Exact pre-change CI [#38721038775](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38721038775) SUCCESS: SQLite 2829 passed/5 skipped/3 xfailed; PostgreSQL 2833 passed/1 skipped/3 xfailed; Flutter 785 passed/1 skipped and PWA built. Separate migration drift, synthetic pilot and general Companion browser E2E succeeded, but not browser-to-server SSE.
- Added a synthetic **Django HTTP stack** test: `test_http_post_session_normal_sse_disconnect_scopes_provider_cleanup`; checks valid session/CSRF, nonurgent POST body-only canary, no URL canary, lazy iteration, first SSE frame, stream disconnect, upstream generator cleanup under the correct patient egress scope and scope reset. **Its own exact-head CI is pending at this documentation update; do not inherit the previous green.**
- Unresolved gates: a real browser-to-server POST SSE run, reverse-proxy access-log canary inspection, first clean-install/cache-version and safe rollback acceptance, independent security/clinical reviewers and release certifier. The static `IAMINA_CACHE_SCHEMA = '0.1.0+1'` requires first-release cache coordination. Desktop Commander device was offline during this verification, so no local live-server run was possible.
- PR remains DRAFT; no merge, Vercel deployment, provider egress or real-patient use is authorized. Record final CI outcome in PR/#925/Notion without fabricating release certification.

