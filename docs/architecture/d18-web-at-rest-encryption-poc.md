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
