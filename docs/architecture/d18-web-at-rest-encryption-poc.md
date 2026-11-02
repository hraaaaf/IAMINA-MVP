# D18 Web — encrypted local vault POC (security gate, NOT certified)

Status: **OPEN / NO MERGE**. Scope: browser Web, synthetic records only.
Decision goal: protect the **whole clinical patient vault** persisted by Drift, not just D18 demographic/weight rows or exported backups.

## Verified implementation baseline
- `frontend/lib/data/drift/database.dart` uses `driftDatabase` with `DriftWebOptions(sqlite3Wasm: Uri.parse('sqlite3.wasm'), driftWorker: Uri.parse('drift_worker.js'))` in both default and patient-scoped constructors.
- This is ordinary sqlite3 WASM, with **no demonstrated SQLCipher/sqlite3mc key setup** or encryption-at-rest guarantee.
- `D18EncryptedBackup` encrypts **exported files** using a passphrase; it does not encrypt SQLite browser persistence.
- Browser origin isolation, IndexedDB/OPFS namespacing and passphrase-protected backup are **not** at-rest encryption.

## Candidate implementation and hard gates
1. Isolated synthetic browser proof, no production migration: evaluate an audited encrypted SQLite WASM engine compatible with Drift's worker and OPFS/IndexedDB. Confirm the exact key hook, licensing, wasm build provenance and persistence adapter. Do **not** swap the WASM file without proving compatible API and encrypted storage.
2. Create two real Chromium browser contexts with a persistent storage directory. Context A: open keyed vault, write synthetic clinical row, close browser. Inspect raw browser-backed persistence: no known plaintext sentinel or readable SQLite schema/header. A substring scan is a **negative control only**, not proof of cryptographic confidentiality.
3. Reopen same directory: wrong key must fail closed, no destructive reset or plaintext fallback. Correct key must recover identical rows; key rotation must survive another restart.
4. Verify all clinical tables use the same protected boundary, including older migrations and background worker paths; inspect all possible browser storage copies and logs. No unencrypted shadow database.
5. Verify backup/restore and authenticated vs device-only vault identity; test crash recovery, migration from existing **unencrypted** databases, interrupted migration and rollback. Never delete the only existing patient copy.
6. Browser matrix: Chrome desktop/mobile emulation, Safari/WebKit and Firefox; origin upgrades, private mode, storage eviction and quota. Verify keyboard and 200% scaling separately.
7. Key policy requires explicit human approval: local passphrase unlock vs device-bound key, recovery if forgotten, multi-device access, session lock, threat model (stolen device/browser profile vs XSS/compromised origin). A stored key alongside ciphertext does not satisfy the threat model.

## Acceptance evidence
- Source diff (engine/worker/storage/key lifecycle) + reproducible pinned build and license.
- Automated real-browser A→close→wrong-key rejection→correct-key restore→rotate→restart.
- Evidence that persisted bytes are encrypted from engine design/key setup; raw-byte scan alone cannot establish this.
- Tests for clinical data, backup restore, migration safety and recovery.
- Reviewed security ADR and product key-recovery decision; CI green on the exact candidate HEAD.

## Stop conditions
No production migration, no claim of certified at-rest encryption, no merge or Vercel deployment until the evidence above is met. If compatible encrypted SQLite WASM cannot be established, assess an **application-level encrypted vault** with atomic authenticated snapshots; do not label ordinary Drift SQLite as encrypted.

## 2026-11-01 — OPFS research gate

CI #41315678291 proves kvvfs cannot activate sqlite3mc encryption. SQLite upstream documents OPFS VFS as Worker-only (https://sqlite.org/wasm/doc/trunk/persistence.md). SQLite3MultipleCiphers documents its file-backed VFS encryption model (https://utelle.github.io/SQLite3MultipleCiphers/docs/architecture/arch_vfs/). Current WASM worker has no OPFS VFS. Next: separate pinned worker-OPFS-capable candidate and full keyed restart/wrong-key proof; no production integration.

## 2026-11-01 — OPFS key incompatibility proven

Run [#41324645925](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41324645925) SUCCESS as diagnostic only. Worker OPFS open succeeds, but `PRAGMA key` fails with **`SQLITE_ERROR: sqlite3 result code 1: Setting key failed. Encryption is not supported by the VFS.`** Therefore the pinned sqlite3mc v2.6.1 WASM release does not provide keyed OPFS persistence in this configuration, despite OPFS VFS registration under COOP/COEP. Both `kvvfs` and `opfs` rejected keying. `encryptedPersistenceVerified:false`; no data written. **Stop** repeating this distribution's keyed VFS probe. Next architecture decision: assess a purpose-built encrypted OPFS VFS / sqlite3mc-compatible WASM build against a WebCrypto AES-GCM encrypted snapshot vault with atomic write, recovery, and multi-tab constraints. No production integration, merge or deploy.

## 2026-11-01 — Correct VFS wrapping experiment (OPEN)

Primary upstream SQLite3MultipleCiphers FAQ explicitly instructs prefixing a non-default VFS name with `multipleciphers-` to register its encryption wrapper: https://utelle.github.io/SQLite3MultipleCiphers/docs/faq/faq_overview/ . Earlier `vfs:'opfs'` failure therefore does **not** rule out `vfs:'multipleciphers-opfs'`. Probe commit `163f00bce0be032d1fca2a400b3950ecbc49c9e4` tests the documented wrapper name with a synthetic key and write. Until CI shows success, this is a hypothesis, **not** a validated encrypted backend. If keying succeeds, next require browser restart, wrong-key rejection, raw OPFS bytes, rotation and failure atomicity; do not merge/deploy. Fallback comparison: purpose-built encrypted VFS (strong SQLite semantics but custom WASM maintenance) versus WebCrypto AES-GCM snapshots (independent crypto but atomicity, rollback, crash recovery and multi-tab complexity). Prefer wrapped SQLite VFS if it passes end-to-end gates.

## 2026-11-01 — Keyed OPFS write SUCCESS (limited scope)

Run [#41326852973](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41326852973) job `124908489004` SUCCESS: `candidateVfs:"multipleciphers-opfs"`, `opened:true`, `keyAccepted:true`, `wrote:true`. This **supersedes** the earlier blanket OPFS incompatibility inference, which tested unwrapped `opfs`. The encryption VFS prefix is required by the upstream FAQ. The diagnostic does **not** yet prove persistent encrypted bytes, cross-browser support, wrong-key failure, restart, key rotation, or Drift integration (`encryptedPersistenceVerified:false`). Next implement fail-closed persistent browser A→restart→wrong key→right key, raw bytes inspection, rotation, and make gate CI-blocking. No merge/deploy.

## 2026-11-01 — Keyed OPFS same-session proof (not full certification)

Run [#41327826759](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41327826759) SUCCESS: `multipleciphers-opfs` keyed write and close, wrong-key reopen rejected (`SQLITE_NOTADB`), correct-key reopen recovered synthetic row, raw OPFS file inspected (no known plaintext sentinel or standard SQLite header). Probe reports `opfsPersistenceExploration.encryptedPersistenceVerified:true` for these **same-session** checks. Legacy overall `persistenceGate` still prints `encryptedPersistenceVerified:false`, correctly reflecting incomplete certification. The negative raw-byte scan is not by itself a cryptographic proof. Remaining gates: independent browser-process restart with persistent profile, key rotation, crash/interrupted writes, whole-clinical-vault boundary, recovery and cross-browser matrix. No merge/deploy.

## 2026-11-01 — Independent Chromium restart and key rotation verified

[Run #41328692210](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41328692210) SUCCESS: separate Chromium processes sharing a persistent profile; encrypted OPFS database reopened with correct key, wrong key rejected (`SQLITE_NOTADB`). [Run #41328844843](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41328844843) SUCCESS: `PRAGMA rekey` in a subsequent Chromium process, followed by another independent process; original key rejected (`SQLITE_NOTADB`), rotated key recovered the synthetic sentinel. This validates synthetic Chromium/OPFS behavior only; interrupted writes, migration, backup/recovery, browser compatibility, key management and clinical data boundary remain unverified. No merge or deployment.

## 2026-11-01 — Abrupt Chromium termination recovery verified

[Run #41331241148](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41331241148) SUCCESS at commit `2a3928f`: synthetic encrypted OPFS database with a committed row and a second uncommitted row inside an open transaction; Chromium root process terminated with `SIGKILL`; new Chromium process sharing the persistent profile recovered **only** `COMMITTED_BEFORE_CRASH` (`abruptProcessRecovery.ok:true`). This proves this bounded crash scenario, not mid-write disk power loss, rekey interruption, atomic backup/restore or migration. Earlier [run #41329721388](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41329721388) failed solely in the test harness before SIGKILL due to unsupported `launchPersistentContext.browser().process()` access; fixed by root PID targeting. No merge/deploy.

## 2026-11-01 — Real application root located; storage adapter still unverified

Repository `frontend/pubspec.yaml` and `frontend/README.md` confirm Flutter lives under `frontend/` (not repository-root `lib/`), with `drift: ^2.20.0` and offline-first persistence. The synthetic migration [run #41334344187](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41334344187) is green but exercises SQLite `opfs` → `multipleciphers-opfs` and **does not establish** that IAMINA's active Web connection uses either VFS. No actual Dart connection factory or IndexedDB persistence path has yet been located and verified. **Gate remains closed:** no production migration, automatic cutover, merge or deployment. Next identify actual Dart database entrypoint and schema, then test a faithful migration preserving all rows and identity boundaries, with rollback and key lifecycle.

## 2026-11-01 — Actual Drift Web connection located: migration architecture decision

Verified branch source: `frontend/lib/data/drift/database.dart` imports `drift_flutter`, uses `driftDatabase(name: ..., web: DriftWebOptions(sqlite3Wasm: Uri.parse('sqlite3.wasm'), driftWorker: Uri.parse('drift_worker.js')))`, `schemaVersion => 12`. `AppDatabase.defaults()` opens legacy unscoped `amina`, while `AppDatabase.forPatientVault(scope)` opens a distinct physical database named `scope.databaseName`; **no automatic ownership inference or migration from legacy**. `frontend/lib/data/drift/patient_vault_scope.dart` constructs native `amina_vault_v1_native_<Django ID>`, device `amina_vault_v1_device_<UUIDv4 without hyphens>` and audit `amina_vault_v1_audit`. These names represent isolation, not authentication or ownership authorization.

**Decision D18-MIGRATION-ARCH:** Do not replace Drift's live `sqlite3.wasm` or worker with sqlite3mc or migrate a vault in place. First identify the actual Drift Web storage backend on the supported browsers and verify SQLite serialization/export and import under the existing connection. Build an opt-in, fail-closed, per-vault migration that authenticates the exact principal, preserves legacy `amina` as quarantined/unassigned, snapshots and checks all tables/schema/foreign keys/row counts, encrypts into a separate destination, validates reopened destination and key, and retains original until explicit clinical/security approval and verified rollback. Include idempotence, interrupted migration, multi-tab and cross-browser tests. Synthetic `opfs`→`multipleciphers-opfs` [run #41334344187](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41334344187) **does not** validate Drift Web adapter compatibility. No merge/deploy.

## 2026-11-01 — Export/import audit: existing JSON backup is NOT a full vault migration primitive

Verified source `frontend/lib/data/drift/local_backup.dart`: `_exportRows()` serializes only `logEntries`, `patientProfiles`, `chatMessages`, `medicationEvents`, `reminders`; `exportVaultJson()` adds `patient_treatment_declarations_v1`. It does **not** enumerate all SQLite tables via `sqlite_master`, export arbitrary dynamically-created tables, preserve indexes/triggers/schema objects or prove byte-equivalent database migration. D18 stores extra SQL tables such as `patient_progressive_demographics_v1` (see `patient_progressive_demographics_store.dart`); therefore **do not use `LocalBackup.exportVaultJson`/`restoreVaultJson` as the full-vault migration channel**. The latter is destructive for its supported tables (`DELETE` before insert inside transaction) and is explicitly excluded by `D18EncryptedBackup` documentation. `D18EncryptedBackup` is a narrow D18 export, not whole-vault backup. No live migration code has been changed.

**Required next gate:** browser integration test using actual `drift_flutter` connection and `drift_worker.js`; inventory `sqlite_master` plus dynamic tables; prove faithful, read-only source snapshot and destination reconstruction (schema objects, rows, `PRAGMA foreign_key_check`, ownership, schemaVersion, checksum, reopening) under a separate encrypted database, including interrupted transfer and rollback. Test browser storage engine selection (OPFS/IndexedDB) rather than assuming OPFS. No automatic cutover/merge/deploy.

## 2026-11-02 — D18 A: real Drift Web storage selection proof (PENDING CI)

Previous exact HEAD `36c95ebb6886514ca4f9bd04926775566b67627a` fully GREEN: [D18 SQLite+key #41362721878](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41362721878) SUCCESS, job `d18-key-policy-tests` logs report 3/3 native key tests PASS and **actual Flutter Web/WebCrypto** `passed:true, stage:complete, error:null, events:[]`. [CI general #41362721919](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41362721919) SUCCESS; [UX #41362721887](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41362721887) SUCCESS.

**New isolated, synthetic-only proof:** enhanced `frontend/lib/d18_real_drift_web_probe_main.dart` to open the SAME physical test vault via `WasmDatabase.open` (the documented Drift 2.x Web API) after independent Chromium restart, force `moveExistingIndexedDbToOpfs:false`, record `chosenImplementation`, reject `unsafeIndexedDb` and `inMemory` as not sufficiently safe for the test, and demand the original persisted A sentinel. This binds the reported backend to the actual existing `driftDatabase()` vault and avoids assuming OPFS just because Chrome supports it. Playwright now mandates **6/6 phases** and includes chosen backend in report. No clinical data, no real schema migration, no switched worker.

**REQUIRES fresh exact-HEAD CI proof.** This is not at-rest encryption. Use the backend result to select a future fail-closed encrypted adapter/migration route. Drift docs: https://drift.simonbinder.eu/platforms/web/ and https://pub.dev/documentation/drift/latest/wasm/WasmDatabaseResult-class.html . No merge or Vercel deployment.
---

## 02/11/2026 — IAMINA D18 A: IndexedDB real Chrome 6/6 SUCCESS, source integrity preflight added (CI PENDING)

**Verified on previous HEAD 2718053c**: [D18 #41409014324](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41409014324), [CI #41409020240](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41409020240), [UX #41409020096](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41409020096) SUCCESS. Browser report passed **6/6** with real Drift `chosenImplementation: sharedIndexedDb`; persistent A synthetic data remains after browser restart, B isolated, legacy preserved. This is NOT OPFS and NOT encrypted.

**Next implementation:** `d18_migration_source_preflight.dart` only reads exact-scoped vault, executes `PRAGMA integrity_check` and separately `PRAGMA foreign_key_check` plus SQLite dynamic schema inventory and total row count within one transaction. Tests ensure synthetic orphan FK rejects with data still intact, triggers/dynamic tables discovered, and scope mismatches fail closed. Real Chrome `probe_backend` additionally calls this preflight. CI needs verification on the new HEAD; no real migration, no encryption, no clinical cutover. SQLite documents that integrity_check alone does not check FKs: https://sqlite.org/pragma.html. PR #1207 remains DRAFT; NO MERGE/DEPLOY.
---

## 02/11/2026 — D18-A synthetic full SQLite byte export from actual IndexedDB (STAGED, NO CI YET)

Pinned `drift:2.31.0` supports `WasmDatabase.probe().exportDatabase()` since drift 2.28.0 (primary source: https://pub.dev/packages/drift/changelog). Following source qualification PASS at HEAD bb21f69b ([D18 #41411775462](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41411775462), 6/6 browser), a new CI-only `probe_export` uses this API to export the WHOLE original A IndexedDB SQLite binary (no clinical values/bytes emitted to logs), checks the standard SQLite header and opens an entirely separate synthetic disposable copy through `WasmDatabase.open(initializeDatabase: ...) `. It compares all user schema SQL objects (including indexes/triggers), per-table row counts, `user_version`, integrity, foreign keys, and a synthetic sentinel; additional new Chromium PROCESS `verify_export` checks persistence of copied data and that source A and legacy remain unchanged. Browser harness now requires **8/8** phases.

**CRITICAL:** the exported SQLite image and destination copy are both PLAINTEXT, isolated to the synthetic CI profile. This is a fidelity/copy mechanism rehearsal, not an encrypted backup or migration implementation. Do not copy actual patients to a plaintext destination; do not auto-enable this harness in product `main.dart`. Future destination needs keyed authenticated encrypted OPFS or another proven encrypted file system, wrong-key/recovery/rollback and original copy preserved. There is no clinical cutover or Vercel deployment.

**STATUS of this staged commit:** not yet on branch, not tested in CI. No success claim. Existing CI at bb21f69b should complete before new push to avoid cancellation.
---

## 02/11/2026 — D18-A: full SQLite encrypted-snapshot restart test, synthetic-only (CI PENDING)

Previous SHA **592f8d05602dc3dd21de507e713083ed4ef25642** GREEN: [D18 #41413005477](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41413005477) 8/8 PASS real Chromium; [CI #41413005515](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41413005515) and [UX #41413005450](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41413005450) SUCCESS. Real source `sharedIndexedDb`, byte-level SQLite export and isolated unencrypted clone after restart verified. Source preflight (integrity + FK + schema) passed; no live migration.

New source `frontend/lib/d18_real_drift_web_probe_main.dart` + `tools/d18_real_drift_web_smoke.js` now mandate 10 Chromium steps. `encrypt_snapshot` uses approved `D18VaultKeyPolicy` to generate a random 256-bit DEK, then AES-256-GCM encrypts the actual exported synthetic IndexedDB SQLite bytes with scope AAD; persists only the ciphertext + public key envelope in disposable localStorage. An independently random offline recovery code is passed **ONLY from temporary DOM to the Node runner in volatile memory**, never logged or stored in browser storage. After independent Chromium-process restart, `verify_encrypted_snapshot` rejects wrong passphrase, foreign patient, tampered GCM data; requires correct passphrase and runner-held offline code to recover **exact identical SQLite bytes**, compared to a fresh original export. No real patient or production storage changes.

**Security boundary:** this proves synthetic snapshot crypto plumbing ONLY; it does NOT make ordinary live Drift SQLite encrypted at rest, and the test's separate original+clone remain plaintext. Real full-vault migration + cutover, crash atomicity and storage-backend compatibility remain open. A static passphrase is CI-only; real patients must create their own. Browser `localStorage` ciphertext is a synthetic test fixture and MUST NOT be reused as patient-vault storage. Key policy A already approved; no further human authorization for synthetic CI checks. CI on new SHA MUST be inspected before success claim. No merge or deploy.
---
