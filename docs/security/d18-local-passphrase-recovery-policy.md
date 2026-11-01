# IAMINA — D18-A Web local vault key and offline recovery policy

**Decision D18-A, 2026-11-01: APPROVED by product owner (option A).** Local patient passphrase + offline encrypted recovery. This authorizes key-policy implementation and tests, **NOT automatic clinical-vault migration, merge or Vercel deployment**.

## Goal / success / proof

- **Goal:** protect the *entire* clinical patient vault at rest on IAMINA Web, not just the exported D18 profile backup.
- **Success:** no clinical SQLite plaintext persisted after deliberate, lossless, atomic cutover; correct passphrase unlock; wrong passphrase/foreign patient cannot open; offline recovery code unlocks even if passphrase forgotten; restoration, crash and rollback validated; no silent loss/migration of historical `amina`.
- **Proof:** running production Drift adapter + browser byte/integrity tests + full schema/table/trigger inventory equality, multiple identities, fresh browser processes, recovery and CI exact SHA, independent security/clinical review. **Not yet achieved**.

## Approved A key lifecycle

1. On explicitly approved **empty** encrypted destination only: generate a random 256-bit Data Encryption Key (DEK). No deterministic key from login, Firebase account, email or device ID.
2. Wrap the DEK with AES-256-GCM under a distinct PBKDF2-HMAC-SHA256 key derived from an entered local passphrase (unique random 128-bit salt, fixed **600,000** iterations). The exposed envelope has a strict schema; it contains neither raw secret, user ID, recovery code nor data.
3. Independently wrap that same DEK under a **new cryptographically random 256-bit recovery code**. Show the code once; patient must copy/store it **outside the browser/device**. This code is different from the ordinary backup passphrase. Recovery requires the envelope plus the offline code; reset to a new passphrase and generate a new offline recovery code.
4. The two AEAD wrappers authenticate the exact selected patient vault namespace through AAD, binding decryption to that selected vault. PatientVaultScope is not by itself proof of authentication; session principal must be verified before selecting a vault.
5. Use key only while unlocked in active browser process; on explicit lock/logout/account switch destroy in-memory `SecretKeyData` references (best effort). Never write clear DEK/passphrase/code in IndexedDB, localStorage, logs, analytics, URL parameters, workers or CI. **Browser malware/XSS and runtime memory snapshots are not protected by disk encryption**.
6. Recovery without the local passphrase is possible only if the offline recovery code AND encrypted vault data/envelope still exist. **If both secrets are lost, recovery is cryptographically impossible**. A recovery code cannot resurrect data physically deleted by eviction or an erased device. An independent encrypted off-device full-vault backup is a *separate* prerequisite for disaster recovery.
7. After recovery, rotate the passphrase wrapper and recovery code. **Old copies of the envelope with the old code may still decrypt the same DEK**; true revocation after compromise requires rotating the DEK and re-encrypting the complete vault, plus retiring old encrypted copies.
8. Use no automatic sync of keys/data, no silent passphrase reset via online account, no backdoor escrow. Multi-device restoration requires explicit full-vault encrypted backup import and ownership checks, not copying an unlocked browser secret.

## Integration constraints — no-go until satisfied

- Existing `frontend/lib/data/drift/database.dart` uses **unencrypted** `sqlite3.wasm` + `drift_worker.js`. `D18VaultKeyPolicy` implements **key wrapping only**; it is not a replacement for the actual Drift storage engine. Never describe it as active at-rest protection.
- Never store a plaintext clinical copy alongside an encrypted destination. Migration from pre-existing `amina` or scoped Drift must be a deliberate, identity-bound, resumable, idempotent, non-destructive procedure with complete schema (`sqlite_master`, hidden/dynamic tables, indexes, views, triggers), integrity and row comparison. Preserve original plus independently encrypted, recoverable backup until verified cutover and review.
- A new keyset must **not** be generated when metadata is missing for an existing encrypted vault. That state is a LOCKED/RECOVERY error, not an empty vault or permission to overwrite.
- Lock UI must be accessible, FR/AR RTL tested, no persisted secret, handle browser background/timeout and multi-tab ownership/lease. Automatic timers remain design scope and require actual browser evidence.
- Session keys in Dart `SecretKeyData` can be destroyed best-effort; JS runtime, browser extensions, XSS and swapped memory are not guaranteed scrubbed.

## Verified standards basis

- NIST SP 800-132 (password-derived master keys; salt and work factor): https://csrc.nist.gov/pubs/sp/800/132/final
- OWASP Cryptographic Storage / Key Management (independent DEK vs KEK, authenticated encryption, backup and key recovery): https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html , https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- OWASP Password Storage (PBKDF2-HMAC-SHA256 600k baseline): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

## Status

**Policy A approved. Code: isolated key-wrapping helper with tests, production wiring NOT AUTHORIZED by current evidence.** Before real clinical use: full encrypted SQLite adapter proof, legacy/historical migration, atomic rollback/recovery, key-loss UX and threat review. PR #1207 remains DRAFT; no Vercel deployment.
