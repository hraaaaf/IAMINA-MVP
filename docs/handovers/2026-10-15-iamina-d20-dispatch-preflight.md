# IAMINA — D20-G consent/vault preflight before eventual OS notification
Date: 15 October 2026

## Goal / observable success / proof
Before an already-reserved descriptive weight notice is eligible for any *future* OS transport, verify again active patient vault, explicit consent episode, source weight IDs/dates/values, user thresholds, data freshness, durable reservation and current OS permission. Fail closed on changed state. Success = exact-HEAD CI with adversarial synthetic SQLite/Flutter tests; no real sending, no medical claims.

## Status and prior authority
Parent D20-F #1083 HEAD `9c52c1c438c566ba3574166392b1865b4fe2cdc4` verified targeted UI CI #38787976930, D18 raster #38787985411, Android vault #38787985538, UX geometry #38787985407, browser #38787985406 all SUCCESS. D20 A-F are all still DRAFT/unmerged, dependent on D18 A/B/C. Historical P5 6/12=50% unchanged.

## Implementation boundaries
Read-only `PatientWeightNoticeDispatchPreflight.check` with no OS notification transport, push, timer, network, LLM, persistence mutation or clinical inference. Inputs are source-bound `LocalWeightNoticeReservation`, caller-supplied current OS-permission status and UTC time. Re-read preferences and source history from *selected physical patient vault* and compare with the exact persisted reservation in one SQLite transaction. Reject revoked/re-consented state, different owner, changed threshold, stale/updated source, altered reservation, bad clock and missing OS permission. A true preflight response is NOT a sent notification and cannot eliminate the race with a separate asynchronous OS API: actual dispatch must use a securely bound OS adapter and revocation lifecycle and requires independent release review.

## Synthetic tests and scope
10 tests: valid local candidate, OS permission refusal, revocation, newer opt-in episode, two vaults, changed latest reading, freshness, threshold changes, ledger mutation and bad clocks/audit scope. Run A–G in CI, no real user/patient data. No UI change so existing D20-F BEFORE/AFTER evidence remains relevant but no new visual score claimed.

## Remaining
Native OS permission/transport adapter with verified actual delivery reporting, status/cancel and explicit user consent, registry/foreground/background handoff, avoid stale cross-vault sends and duplicate OS deliveries; QA on real Android/iOS, privacy/medical/RTL accessibility independent review and P5-6A/6B gate before real patient release. Do not merge or deploy Vercel D20 without authorization.

**Proof state:** candidate, exact SHA CI not yet verified. D19 separate #946 clinical review OPEN. No release.
