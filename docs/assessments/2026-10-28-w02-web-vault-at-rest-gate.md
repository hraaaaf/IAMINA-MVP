# W02 — Web clinical vault at-rest safety gate (2026-10-28)

## Goal, success criterion and proof

Goal: prevent new persistent unencrypted clinical Web SQLite writes until an encrypted storage executor, key lifecycle and recovery are independently proven.

Success (interim gate only): AppDatabase.forPatientVault() refuses native-Django and device-local patient scopes on Web, before opening Drift OPFS/IndexedDB; native platform behavior remains unchanged; explicit synthetic audit vault remains usable. Pre-existing Web files are neither deleted nor modified. An encrypted and recoverable Web patient vault remains the unresolved product Goal.

Source: W02 isolated branch feat/w02-web-bff-readonly-preflight-20261028; parent acd68e48873f50efcf5b9a31eb0d2a64916dcfa2. Scope: Web runtime only, not a release.

## Risk demonstrated by source and primary documentation

- frontend/lib/data/drift/database.dart opens patient vaults through driftDatabase(name: scope.databaseName, web: DriftWebOptions(...)).
- Drift Web persists SQLite in OPFS or IndexedDB according to browser capabilities; current source supplies no encryption key, encrypted VFS or serialized AEAD storage adapter.
- WebAuthn app-lock signs an assertion; it does not provide Drift a vetted symmetric encryption key. App-lock is not encryption at rest.
- Existing Web legacy amina storage and previously written patient namespaces could contain plaintext. This guard does not purge, migrate or protect such existing data.

Primary technical references:
- https://drift.simonbinder.eu/platforms/web/
- https://drift.simonbinder.eu/platforms/encryption/
- https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API/WebAuthn_extensions

## Interim implementation; no cryptographic certification

- Pure policy allowUnencryptedPatientVaultForPlatform: native allowed; Web native/device clinical DENY; Web auditOnly permitted (synthetic only).
- AppDatabase.forPatientVault calls _openPatientVaultConnection; policy is checked before any persistent SQLite executor is constructed.
- PatientVaultSessionController catches unavailable vaults and keeps them unpublished; this does not certify full patient UX. Real-patient Web sessions intentionally remain unavailable until the encrypted vault is designed and tested.
- AppDatabase.defaults remains a historical read/probe path; existing bytes are quarantined, not silently reassigned to a user. A legacy quarantine/retention and all-writer audit is still required.

## Verification and follow-up

Test authored: frontend/test/data/drift/web_patient_vault_storage_policy_test.dart covers Web/native scope matrix and actual Web constructor refusal. Test execution NOT claimed; run Flutter VM + Chrome tests on exact SHA. Update existing tests expecting plaintext persistence only after review, not silently skip them.

Required before enabling Web patient writes:

1. Design a reviewed encrypted Web persistence layer: AEAD, unique nonces, per-vault keys, authenticated metadata, no plaintext OPFS/IndexedDB/WAL/backups, atomic crash-safe commits.
2. Specify unlock and recovery authority (supported WebAuthn PRF or a separately verified strong credential + backup/recovery); never store decrypting key beside ciphertext without protection, never confuse assertion with key.
3. Test reload, offline reopen, wrong key, ciphertext tampering, rollback, credential loss, A-to-B-to-A two-tab separation, delete/rotation, quota failures, each browser backend; inspect physical browser storage for plaintext.
4. Independent security/privacy review, recovery and controlled pre-existing plaintext migration, with no unapproved deletion.
5. Exact-HEAD Flutter/Chrome tests, one final GitHub CI per owner rule, then explicit human GO for Vercel Preview, followed by hosted W02 browser to BFF to API to Neon and independent SQL cleanup zero.

Status: W02 DRAFT / patient NO-GO / Production NO-GO. This guard is not encryption. No Vercel deployment, Neon mutation, plaintext migration or merge authorized.
