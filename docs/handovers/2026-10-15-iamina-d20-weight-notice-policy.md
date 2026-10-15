# IAMINA — D20-B optional notice decision gate (2026-10-15)

## Scope & source
Approved IAMINA product decision #20 (2026-10-08): weight-change messages only as voluntary, user-configured, throttled, source-traceable descriptive notifications; never automatically on each weighing; no medical-danger inference; do not mix with scheduled reminders (#2). Reference issue #1073 and parent D20-A PR #1074, itself based on unmerged D18-C.

## Technical result (candidate)
Pure Dart policy gate returns null (fail closed) when OFF, OS notification permission missing, no comparison, missing/nonpositive user thresholds, insufficient elapsed history, stale/future timestamps, recently surfaced notice, matching source evidence ID or incomplete consent. Explicit values are supplied by caller; no default clinical cutoffs, no persistent changes, push, schedule, AI or external processing. A returned object is only a descriptive **candidate**, NOT a sent notification or approved clinical event.

## Success / proof
D20-A+B synthetic Flutter tests, analyzer on exact SHA; prove that OFF prevents evaluation independently of reminder settings, that new user preferences must be specifically captured and stored in active patient vault in later D20-C, and that eventual end-to-end UI notifications require opt-in, actual OS permission, rate-limit after a durable delivery, no duplication and multi-locale BEFORE/AFTER.

**Status**: CANDIDATE, no test run verified yet. Does not authorize real-patient use; D18, D19 human gates and P5-6A/B intact. No Vercel D20 deployment. P5 historical 50% unchanged.

## Next
Validate CI on exact SHA; then integrate owned local preferences + actual notification permission and durable dedup. UI must satisfy BEFORE/mockup/AFTER same viewports and accessibility; full D20 remains OPEN.
