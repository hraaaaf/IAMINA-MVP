# IAMINA Web L0 — SSE POST/JSON security integration (2026-10-23)

**Goal**: recover prewritten [PR #1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056), including GET→POST SSE cutover, CSRF cookie+spoofed-Bearer checks, patient-isolated deferred SSE egress, no patient message in URL, and deterministic urgent/insulin refusals. This is **not** an authorization to expose patient messages to a remote model.

**Success**: (a) `GET /api/v1/ai/chat/stream` returns 405; (b) valid `POST application/json` with auth+CSRF yields SSE `[DONE]` without PHI in URL; (c) anonymous/cookie-forged-Bearer rejected; (d) `context_days` bounded 1–365; (e) A/B streams isolated and consent-denied provider never entered; (f) Flutter matches backend POST and PWA first-install cache clears obsolete GET shell, tests run on **this exact SHA**, plus hosted synthetic verification before any release.

**Source provenance**: exact `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`, source [#1056 `f57917c37ea18dad672e248422022224213cafbf`](https://github.com/hraaaaf/IAMINA-MVP/commit/f57917c37ea18dad672e248422022224213cafbf) (historical **4/4 CI SUCCESS**). All **13 modified paths** compared by Git blob against source's Git merge-base `f41778fcb1cfb0608de2b11e37fe290afc1332e9`: `main` has identical blobs (including paths absent from both), so copying each source blob cannot silently overwrite newer main code. The inherited 4/4 source CI is **not proof of this integration**.

**Guardrails**: `backend/ai/api/v1/ai.py` affects clinical chat SSE, but the [L0 local-only Web UI #1140](https://github.com/hraaaaf/IAMINA-MVP/pull/1140) intentionally disables network chat in RELEASE and remains a separate unmerged draft. This security fix does **not** enable that UI, authorize clinical triage, patient LLM calls, or deploy. W01 [#1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128) NO-GO, W02 frozen. A source-only POST test cannot certify real hosted SSO/BFF, log-sink/PHI absence or disaster recovery.

**Gates**: exact-HEAD GitHub CI (Django/PGSQL/Flutter/Chrome/PWA/contract) → inspect failures and artifacts → negative A→logout→B→A and fake Bearer/CSRF on isolated hosted API Preview under SSO (authorized access only; no bypass) → independent privacy/security/clinical review (including emergency response) → explicit owner release/POST cutover acceptance → eligible merge/postmerge **without triggering any unapproved Vercel deployment**. No real patients/test money/Neon Production, no automatic merge.

**Status**: DRAFT integration only. No certification score assigned until test proof.
