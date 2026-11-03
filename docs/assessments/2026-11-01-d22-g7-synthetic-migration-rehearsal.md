# D22-B — G7 candidate migration rehearsal, synthetic only

Date: 2026-11-01 · parent PR #1214.

**Decision:** stage a reversible *in-memory* SQLite sidecar rehearsal for unknown-provenance personal glycemic targets. Do not change the deployed AppDatabase version 12, user data or production SQL defaults until clinical G1/G4 and architecture G7 approvals.

**Goal:** prove no unit is guessed from the currently stored 70/180-like values or the display preference. **Success:** tests demonstrate original numeric values preserved byte-for-byte as doubles, sidecar source units/provenance left NULL, authority set to `unknown`, transaction rollback on induced failure, and separate vaults cannot see one another's candidate rows. **Evidence:** `frontend/test/d22_g7_migration_rehearsal_test.dart`; execution in CI is required before PASS.

## Preflight facts (source)
- `frontend/lib/data/drift/database.dart`: schemaVersion **12**, `patient_profiles.target_range_low/high` are NOT NULL REAL with SQL defaults **70.0/180.0**; `unit_preference` is an independent display field and does not prove the original target's unit.
- Existing `MigrationStrategy` handles earlier v2–v12 additive steps and D7 isolated vaults. Rewriting or deleting the legacy columns now is unsafe.
- Existing `getProfileForLocalUserId` resolves scoped owner; legacy `watchProfile()` remains unscoped and must not be used as an authentication proof.

## G7 candidate model; NOT approved for runtime migration
- Add a **sidecar** with `owner_id`, verbatim legacy numeric bounds, **nullable** per-bound source units, `authority_state=unknown`, nullable provenance, version/author/date/trust context to be defined at an approved boundary.
- First migrator stage does not infer either unit from numeric magnitude, `unit_preference`, or apparent 70/180 pattern; even an arbitrary `provenance` string is not clinical authorization.
- A later reviewed v13+ migration needs an explicit backup/export, source DB version verification, transaction, idempotence, A/B vault binding, restore/rollback and a post-restore audit. Separate target records require signed clinical authority and auditable provenance; merely satisfying sidecar SQL constraints cannot authorize classification.
- Runtime retains fail-closed status while G1/G4/G7 are unsigned. Do not automatically promote a row to approved or display targets. Review and cross-check all API/export/report consumers and CGM-vs-manual classification.

**Known gap:** rehearsal does not amend existing SQL defaults or build an activated authoritative new schema; no patient data migrated. It deliberately tests only synthetic SQLite/Drift and therefore cannot substitute for a browser FUE, a native-vault backup restore, privacy review or medical certification.

**Next exact:** exact-HEAD Flutter test proof; review sidecar versioned design with DB/privacy and endocrinology authority; then implement production migration under separate gate, run data integrity+rollback and F01–F07 real Chrome before release. No Vercel deploy or merge authorized.

## 2026-11-01 — adversarial SQLite NULL-check fix (candidate only)

CI of SHA `7725ef7` demonstrated **919 PASS, 1 FAIL, 7 SKIP**: the first rehearsal's nullable units were accepted by SQLite's three-valued `CHECK` expression when `authority_state` was changed to `approved` (NULL does **not** fail a SQLite CHECK). This was a genuine weakness in the proposed synthetic schema, not a medically approved state.

**Decision:** the pre-authority sidecar must NEVER contain an `approved` state. Its only permitted states are `unknown` and `review_pending`, enforced by `NOT NULL CHECK`; nullable unit fields each enforce `IS NULL OR unit IN ('mg/dL','mmol/L')`. Source strings, even with typed units, cannot grant clinical approval. Only a later independently reviewed and authenticated patient-specific clinical record may support approval, with explicit G1/G4/G7 specialist sign-off, a migration plan and audit trail.

New synthetic negative cases test `NULL`, invalid aliases and forged approval even when both units + a plausible reference are supplied. **No change to AppDatabase v12 or real user data; added tests not yet CI-verified**.
