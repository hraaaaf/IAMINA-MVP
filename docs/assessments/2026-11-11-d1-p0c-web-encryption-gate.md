# D1 P0-C — Web patient vault encrypted-at-rest gate (11 Nov 2026)

**Status:** RESEARCH SPIKE ONLY; **patient NO-GO**. No silent cutover of the historic `amina` IndexedDB.

## Confirmed architecture
- `frontend/lib/data/drift/database.dart` uses `driftDatabase(name: scope.databaseName, sqlite3Wasm: Uri.parse('sqlite3.wasm'))` on Web.
- There is **no verified encryption layer** in the actual SQLite storage path. The App Lock and browser storage encryption policies do **not** prove protection against a browser-profile/IndexedDB file read.
- `LocalBackup.exportVaultJson` produces unencrypted JSON; it MUST NOT be presented as a safe encrypted recovery file.

## Isolated synthetic cryptographic experiment
- `tools/d1_p0c_webcrypto_envelope.mjs`: WebCrypto PBKDF2-SHA256 (310,000 iterations), AES-256-GCM with 96-bit random IV, 128-bit tag, 128-bit random salt.
- Authenticated AAD binds envelope format, owner namespace and schema version; tests reject tampered ciphertext/owner metadata, wrong secret, weak secrets, extra fields; confirm random nonces.
- **No production imports of this experiment**. No secret, key, raw patient data, or external requests. Do not confuse AEAD envelope with encrypted SQLite; this encrypts only an explicitly supplied synthetic string.

## Required engineering before clinical readiness
1. Select and review an encrypted SQLite/WASM VFS (or audited SQLCipher-compatible Web distribution) so the actual Drift database pages, WAL, journals, indices, metadata, and browser persistence are never readable as plaintext.
2. Decide a viable per-vault secret lifecycle across Chrome/Safari PWA, private browsing, offline reload, cleared storage, lost devices, expired WebAuthn credentials, and absent device access. WebAuthn is an authenticator, not automatically a raw AES key. Never derive keys from server bearer tokens.
3. Integrate into `AppDatabase.forPatientVault` **for brand-new vaults only**, behind an explicit opt-in proof gate. Preserve old SQLite untouched and never silently convert legacy bytes.
4. Prove positive reload & restore, wrong-owner rejection, tampering fail-closed, crash recovery, no plaintext residue in IndexedDB/OPFS, no rogue multi-tab writer, Safari/WebKit and Chrome; conduct independent crypto/privacy review.
5. Until those proofs exist, **do not enable cutover**, do not relax `canOptOutOfAppLock`, never merge to clinical use or deploy.

This document records testable evidence and exclusions, not a green security certificate.
