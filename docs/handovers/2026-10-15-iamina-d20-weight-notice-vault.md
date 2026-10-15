# IAMINA — D20-C patient-local opt-in persistence (15 Oct 2026)

Goal: persist optional #20 weight-trend notice preference in the physically selected D18 patient vault, OFF by default. This is separate from D20-A descriptive arithmetic #1074 and D20-B candidate-gate #1076, both draft and dependent on D18.

## Candidate scope
- New `PatientWeightNoticePreferencesStore` with no external services, OS notification permission call, scheduler, push or outbound AI/HTTP.
- Consent only via explicit user-action argument with UTC instant and four complete patient-selected criteria; no normative/medical default, no implicit migration from weight history or OS permission.
- SQLite table created lazily within the active native patient vault, row bound to the existing owner/profile, cannot be used on legacy/audit vaults. Cross-owner rows fail closed.
- Revocation DELETEs the opt-in and all thresholds; no notices occur from this store.
- Nine synthetic Flutter tests for OFF, persisted constraints, revocation, missing consent, malformed timestamps/policy, vault A/B isolation, foreign row detection. This is not a physical Android or actual UI proof.

## Success / proof
Run targeted analyzer and Flutter tests on exact SHA via D20-C workflow. Keep D20-A/B baselines intact; no notifications are sent during tests. No UI affected; before/mockup/after applies to later profile control. No deploy or real patient data.

## Remaining
Consumer must wire `read().policy` to policy evaluator only under actual OS permission, and implement durable delivery ledger, automatic dedup after genuine delivery, UI opt-in with explicit understandable settings, consent revocation on A/B vault switch, FR/EN/AR/Darija/RTL visual checks at 390/430/768/1280. D18 qualification and P5-6A/B remain mandatory prior to real patient release. P5 historical 6/12 = 50 %; full D20 OPEN.
