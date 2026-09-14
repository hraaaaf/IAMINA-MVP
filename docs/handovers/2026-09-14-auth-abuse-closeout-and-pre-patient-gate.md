# IAMINA — Auth abuse closeout / pre-real-patient gate handover

## Goal

Close TD-013 with retained exact-main evidence, then reconcile release governance so regulatory/restricted evidence is deferred until preparation for the first real-patient pilot, without waiving any gate.

## TD-013 retained implementation evidence

- PR #623: `feat(security): add persistent native auth abuse protection`
- exact PR head: `f60cc9516c3d72ef59408d53e6d5d4bab1a0351d`
- merge commit: `f045491a3e07db388067fe54c60fd0c4b543e050`
- exact-head CI #4238 / run `34826154523`: SUCCESS
- exact-head migration drift #3760 / run `34826154519`: SUCCESS
- backend proof: Ruff, import-linter, anti-bypass gates, Bandit, OpenAPI and pytest all passed; pytest retained `2237 passed, 5 skipped, 3 xfailed, 80 subtests passed`
- PostgreSQL source-of-truth job: SUCCESS, including migration validation and full PostgreSQL suite
- post-merge migration drift #3761 / run `34826542606`: SUCCESS
- post-merge CI #4241 / run `34826542521`: still in progress when this handover entry was created; TD-013 must not be removed until it succeeds

Implementation properties:

- PostgreSQL-backed fixed-window auth abuse buckets
- login, registration and password-reset request protection
- per-IP and per-account limits
- HMAC-SHA256 opaque identifiers; no raw email/IP persisted in limiter rows
- typed `429 auth_rate_limited` + `Retry-After`
- works with Redis/cache unavailable
- recovery-window and account-isolation tests retained

## Owner policy decision — 2026-09-14

IAMINA remains demo/synthetic/non-patient during current engineering work.

Issues #318 and #320 remain OPEN but are `PRE_REAL_PATIENT_GATE / DEFERRED`, not waived. They are not the active day-to-day engineering critical path.

Strict boundary: before the first real user is allowed to enter identifiable health data, IAMINA must:

1. cut/freeze the then-current release candidate;
2. bind genuine safety-review/qualification evidence to that exact candidate;
3. select and evidence actual processors and processing geography;
4. obtain applicable CNDP/foreign-transfer evidence;
5. obtain explicit owner authorization before any Vercel deployment;
6. freeze actual deployed topology;
7. run the three exact-SHA release audits and retain PASS outputs;
8. retain an explicit human real-patient release decision.

Until then `NOT_RELEASE_AUTHORIZED` remains unchanged.

The historical `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` package remains useful retained release-gate evidence, but ordinary engineering commits do not require repeated regulatory re-freezes while no real-patient release is being prepared.

Owner-decision comments retained:

- #318 comment `5661668282`
- #320 comment `5661670278`

## Next exact

If post-merge CI #4241 succeeds: remove TD-013 from `docs/TECHDEBT.md`, close #622, reconcile `docs/ROADMAP.md` and `docs/P5_6_RESTRICTED_EVIDENCE_WORKBOOK.md` to the deferred pre-patient policy, validate docs-only PR, merge, then audit the remaining technical debt for stale wording before starting new implementation work.
