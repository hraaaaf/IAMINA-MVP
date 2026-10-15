# IAMINA — D20-G consent/vault preflight before eventual OS notification
Date: 15 October 2026

## Goal / observable success / proof
Before an already-reserved descriptive weight notice is eligible for any *future* OS transport, verify again active patient vault, explicit consent episode, source weight IDs/dates/values, user thresholds, data freshness, durable reservation and current OS permission. Fail closed on changed state. Success = exact-HEAD CI with adversarial synthetic SQLite/Flutter tests; no real sending, no medical claims.

## Status and prior authority
Parent D20-F #1083 HEAD `9c52c1c438c566ba3574166392b1865b4fe2cdc4` verified targeted UI CI #38787976930, D18 raster #38787985411, Android vault #38787985538, UX geometry #38787985407, browser #38787985406 all SUCCESS. D20 A-F are all still DRAFT/unmerged, dependent on D18 A/B/C. Historical P5 6/12=50% unchanged.

## Implementation boundaries
Read-only `PatientWeightNoticeDispatchPreflight.check` with no OS notification transport, push, timer, network, LLM, persistence mutation or clinical inference. Inputs are source-bound `LocalWeightNoticeReservation`, caller-supplied current OS-permission status and UTC time. Re-read preferences and source history from *selected physical patient vault* and compare with the exact persisted reservation in one SQLite transaction. Reject revoked/re-consented state, different owner, changed threshold, stale/updated source, altered reservation, bad clock and missing OS permission. A true preflight response is NOT a sent notification and cannot eliminate the race with a separate asynchronous OS API: actual dispatch must use a securely bound OS adapter and revocation lifecycle and requires independent release review.

## Synthetic tests and scope
11 tests: valid local candidate, OS permission refusal, revocation, newer opt-in episode, two vaults, changed latest reading, freshness, threshold changes, ledger mutation and bad clocks/audit scope. Run A–G in CI, no real user/patient data. No UI change so existing D20-F BEFORE/AFTER evidence remains relevant but no new visual score claimed.

## Remaining
Native OS permission/transport adapter with verified actual delivery reporting, status/cancel and explicit user consent, registry/foreground/background handoff, avoid stale cross-vault sends and duplicate OS deliveries; QA on real Android/iOS, privacy/medical/RTL accessibility independent review and P5-6A/6B gate before real patient release. Do not merge or deploy Vercel D20 without authorization.

**Proof state:** candidate, exact SHA CI not yet verified. D19 separate #946 clinical review OPEN. No release.

## Independent preflight integrity hardening

Reject the entire selected vault if a foreign owner has inserted even a *different* reservation row: checking only the candidate owner's row could mask physical-vault cross-contamination. One negative SQLite test injects owner 812 into the vault for owner 734 and requires a false preflight despite a matching owner 734 reservation. Technical proof pending new exact-head CI; still no sender or user data.

## Exact-head test and security review outcome — 15 October 2026

[GitHub Actions #38798293941](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38798293941) completed **SUCCESS**, HEAD `060f5044912b34524bed64c63c8490c34847ae02`, targeted Flutter analyzer **NO ISSUES**, **56/56 synthetic Flutter tests PASS**, including 11 D20-G cases: current opt-in and reservation, missing OS permission, revoked or newer consent, owner vault A/B, changed/future/stale reading, changed user-selected threshold, tampered durable reservation, and foreign-owner reservation inside same physical vault (explicit fail-closed). Earlier first candidate CI #38798067322 SUCCESS on `af06eeb` but lacked the final foreign-reservation test.

**Proven limit:** no OS sender, no actual delivery/a11y/device certification and no atomicity across an eventual OS transport outside local SQLite. These tests do not certify medical/clinical notifications, patient production or D18. D20-G is only the last-mile **preflight component**, still unmerged DRAFT. Independent clinical/privacy review and native Android+iOS transport remain necessary before D20 full feature release. P5 historic 6/12 50% unchanged.

**Documentation-only closeout**: the above exact-code-head green proof remains tied to `060f5044912b34524bed64c63c8490c34847ae02`. A subsequent documentation-only commit is not an additional runtime change; its own CI state must still be read before calling that new HEAD all-green.
