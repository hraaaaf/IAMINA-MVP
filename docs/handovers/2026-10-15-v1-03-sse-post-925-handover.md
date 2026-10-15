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

## 2026-10-15 — Chrome POST SSE integration proven on candidate HEAD

**Observed candidate HEAD:** `07ecdab1e015792f7ad52a744cf998739d9742c6`, [PR #1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056) DRAFT. **Observed main:** `851117c16c74aa514dfde23f89629f1e9207c48f`; comparison 11 commits ahead and 4 behind. The 4 commits unique to main are D10 iOS/backup and handover, with no overlap in the #925 paths. No rebase/merge to main.

**Exact evaluated CI source/merge:** [CI #38722994272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38722994272) SUCCESS, all 6 jobs. GitHub checkout in CI used temporary PR merge commit `dbeb814` combining branch HEAD `07ecdab1` with main `851117c1` (not a merge to `main`). SQLite **2830 passed, 5 skipped, 3 xfailed**; PostgreSQL **2834 passed, 1 skipped, 3 xfailed**; Flutter **785 passed, 1 skipped**, PWA release built. Ruff, anti-bypass, SAST, generated OpenAPI, frontend analysis are included in the completed CI job. [Migration drift #38722994348](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38722994348) SUCCESS; [synthetic pilot #38722994266](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38722994266) SUCCESS; [Chrome browser E2E #38722994381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38722994381) SUCCESS.

**New observable POST SSE proof:** `.github/workflows/companion-chat-e2e-screenshot.yml` now issues a real Chrome `fetch` request through its localhost streaming proxy into Django using a purely synthetic urgent glucose prompt and native synthetic bearer identity. The workflow output includes `Synthetic Chrome POST SSE → proxy → Django: event/DONE, no URL canary.` It asserts 200, text/event-stream, no-store, canonical emergency flag and `[DONE]`, body-only request canary, and canary absence in backend local access logs. Proxy streams incrementally instead of reading all bytes first. The existing Flutter request builder is covered by separate Flutter unit tests. This does **not** claim the live Flutter chat UI uses SSE; existing UI E2E uses `POST /ai/chat`, not `/ai/chat/stream`.

**Residual gate/limitations (NO-GO):** Test proxy/log checks are localhost, not Vercel reverse proxy/CDN/WAF/APM; clean production entrypoint first-install and same-version JS/service-worker cache refresh/rollback remain unproven. Current service-worker cache schema is `0.1.0+1`. An isolated security/privacy reviewer, clinical-safety/native reviewer as required and Release Certifier have not approved the current candidate. Contract cutover must be owner-approved before merge. Owner reports **zero installed clients**, not an existing fleet. Clinical/legal/CNDP/D31 gates remain independent. **Do not merge, deploy or activate real patients.**

**Next exact:** obtain targeted first-install/cache/rollback and ingress log proofs without real patient traffic; obtain genuinely independent security/clinical/Release Certifier reviews and owner cutover acceptance. A documentation update after this section advances the branch HEAD again; check exact new SHA/CI rather than transferring the green above.

## 2026-10-15 — first-run PWA synthetic verification and release NO-GO

**Snapshot before this documentation commit:** PR #1056 source HEAD `41f5c828f0af25c1fb33f0ed6b4ff987a90f80dd`, DRAFT. Current `main@ea3ad7bafaae669d2cd978fa6894a9df814539f0`, branch divergence 15 commits ahead / 5 behind. Fifth main-only change is `docs/handovers/2026-10-14-iamina-d10-option-b.md`; no path overlap with the V1-03 source diff. No rebase or merge.

**Fresh engineering evidence on that code HEAD**:
- [CI #38728499180](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38728499180) **COMPLETED/SUCCESS** (all 6 jobs) on temporary PR merge checkout `cbedd23`, pairing `41f5c82` with `main@ea3ad7ba`. SQLite **2830 passed, 5 skipped, 3 xfailed**; PostgreSQL **2834 passed, 1 skipped, 3 xfailed**; Flutter **785 passed, 1 skipped** and PWA release bundle built. Also Ruff/SAST/egress checks and OpenAPI pass.
- New `scripts/tests/test_sse_pwa_cache_contract.mjs` executed **PASS** by the frontend CI job. It simulates a fresh release cache and force-reload precache, removes an old fake cache, verifies that GET/POST clinical `/api/` requests are *never service-worker-intercepted*, tests current shell retrieval, and validates hosted-review cache deletion. This is **synthetic service-worker logic**, not production rollback proof.
- [Chrome E2E #38728499322](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38728499322) **COMPLETED/SUCCESS** from a genuinely blank temporary Chrome profile. The browser confirms IAMINA service-worker registration, active release version, current PWA shell cache and no competing old-version cache. The same run proves synthetic authenticated Chrome `POST /api/v1/ai/chat/stream` over localhost proxy to Django, deterministic emergency SSE and `[DONE]`, no synthetic canary in URL or inspected localhost backend logs. Browser registration is **not** proof that a real-world PWA release is installed or clinically certified.
- [Migration drift #38728499289](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38728499289) SUCCESS and [synthetic pilot #38728499225](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38728499225) SUCCESS.

**Infra constraints:** Vercel projects `iamina-review` and `iamina-certified` are observable read-only. `GET /v1/drains` returns HTTP 404 both without scope and with observed team scope. Therefore log-drain destination/retention is **UNKNOWN** (404 is not evidence of zero drains); no real logs were retrieved and no deployment took place. Desktop Commander test device remains offline at the last observation.

**Human gates not discharged:** independent security/privacy and clinical-safety/native review (no actual PR approvals); a distinct Release Certifier; real-target edge/WAF/APM log hygiene with synthetic-only request; production entrypoint first-distribution frontend/backend/PWA version pairing and safe rollback without GET PHI; owner's explicit first-release POST-only contract acceptance. 0 installed clients is owner-confirmed, so do not invent a legacy installed cohort. #1029 real isolated agent council, #1038 main protection, D31 and Morocco+CCG legal/CNDP remain separate. **No merge, no Vercel deploy, no real patients, no patient text to third-party LLMs.** P5 canonical **6/12 = 50%** unchanged.

**Post-doc HEAD condition:** this note plus diagnostic step-name changes move the branch SHA; recheck the fresh exact-head runs before claiming green again. Next exact: review CI and browser E2E on new SHA; if green, stop only at the independent human/target-ingress gate, leave PR DRAFT and #925 OPEN. After explicit approval: SHA-lock merge then postmerge CI and canonical closeout, never before.

