# IAMINA D20-D — durable descriptive notice reservation (15 October 2026)

## Goal
No repeated notification attempts for the same weight evidence after application restart. Consent, OS permission and user-defined criteria checked BEFORE any notice candidate can be reserved. This is not a delivered notification.

## Independent scope
Parent D20-C PR #1077 is a local patient-vault user-initiated preference store. D20-D adds its own local SQLite reservations table keyed by current vault owner and final measurement UUID. Attempts are deduplicated across new store instances and conservatively rate-limited from past reservations, including a crashed/unfinished attempt; fail-closed rather than duplicate a health-related push. It reads actual local D18 weight records and D20-C preferences, not arbitrary model-provided weights or caller-supplied owner IDs. Does not send or schedule any notification, no LLM, no network or biomedical interpretation.

## Observable tests
Nine synthetic tests: default OFF; OS permission absent; successful source-bound reservation; repeated evidence same vault; preference revoked; physical A/B isolation; stale/future/no history; foreign-row intrusion; legacy/audit fail closed.

## Open gates
Targeted CI on exact head. Before any real user notification: qualified D18 storage and D20 privacy reviews; tested UI controls with BEFORE → goal → mockup → AFTER across 390/430/768/1280; separate permission UX (not assumed from this code), OS transport with actual authenticated delivery result, persistence of successful delivery & safe retry, settings localization, actual device tests. D19 medical signatures remain open. No merge/main, no Vercel, no real-patient traffic. Historical P5 6/12 = 50%.

## 15 Oct 2026 — audited exact CI and prospective-consent correction

First source candidate SHA `94d5b601c8090881a609bdd6a7d542ab840da83e` passed GitHub CI [#38775193525](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38775193525) with 32/32 synthetic tests and Flutter analyzer with no issues, after fixing unused test constant from an initial red lint run. **Independent code review finding:** it was possible to reserve an older measured weight trend after opt-in, causing an unsolicited retroactive message once transport is added. The present candidate fails closed if latest source reading predates opt-in UTC. Fixture updated for prospective weight readings and separate negative test added for earlier-only history. No OS dispatch, push or clinical interpretation added. **New SHA requires its own full test evidence before marking the amended scope green**.

Proceed only with local/pre-release work; qualified D18 ownership, D20 opt-in UX, device notification audit, D19 clinical gate and P5 real-patient gate remain open. No merge/Vercel from this branch.

## 15 Oct 2026 — verified D20-D exact-head regression result

- [CI #38776813066](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38776813066), SHA `66dd3da07d4e5ea2347d7c8f5a009707ad865cb6`: **SUCCESS, 33/33 synthetic Dart tests PASSED; Flutter targeted analyzer NO ISSUES**, including `consent does not retroactively reserve pre-consent readings`. Runs use local in-memory SQLite; no installed Android/native device, OS notification or browser delivery is certified.
- [PR #1078](https://github.com/hraaaaf/IAMINA-MVP/pull/1078) remains DRAFT / UNMERGED, based on D20-C #1077 which depends on D20-B #1076, D20-A #1074 and D18-C #1066. This is a tested **reservation library**, not a delivery service.
- **Remaining**: D20 UI with BEFORE→mockup→AFTER and same viewports, persistent privacy-first user switch/criteria integrated into selected native patient vault, native OS permission consent, actual dispatch ledger with verified results (not presumed), cross-owner switch safety and independent medical/privacy/localization review. No production / Vercel from this branch; D19 clinical gate remains OPEN. P5 historical global 6/12 = 50% unchanged.
