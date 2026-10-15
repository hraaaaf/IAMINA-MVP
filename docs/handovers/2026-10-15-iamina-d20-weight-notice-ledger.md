# IAMINA D20-D — durable descriptive notice reservation (15 October 2026)

## Goal
No repeated notification attempts for the same weight evidence after application restart. Consent, OS permission and user-defined criteria checked BEFORE any notice candidate can be reserved. This is not a delivered notification.

## Independent scope
Parent D20-C PR #1077 is a local patient-vault user-initiated preference store. D20-D adds its own local SQLite reservations table keyed by current vault owner and final measurement UUID. Attempts are deduplicated across new store instances and conservatively rate-limited from past reservations, including a crashed/unfinished attempt; fail-closed rather than duplicate a health-related push. It reads actual local D18 weight records and D20-C preferences, not arbitrary model-provided weights or caller-supplied owner IDs. Does not send or schedule any notification, no LLM, no network or biomedical interpretation.

## Observable tests
Nine synthetic tests: default OFF; OS permission absent; successful source-bound reservation; repeated evidence same vault; preference revoked; physical A/B isolation; stale/future/no history; foreign-row intrusion; legacy/audit fail closed.

## Open gates
Targeted CI on exact head. Before any real user notification: qualified D18 storage and D20 privacy reviews; tested UI controls with BEFORE → goal → mockup → AFTER across 390/430/768/1280; separate permission UX (not assumed from this code), OS transport with actual authenticated delivery result, persistence of successful delivery & safe retry, settings localization, actual device tests. D19 medical signatures remain open. No merge/main, no Vercel, no real-patient traffic. Historical P5 6/12 = 50%.
