# W02 — Web encrypted SQLite snapshot prototype (2026-10-28)

## Goal / status

Goal: establish a correct, browser-compatible cryptographic envelope primitive for serialized patient-vault snapshots and a high-entropy recovery credential. This is a subtask of W02 (identity, vault, privacy), not an implementation of Drift Web persistent encryption.

**Status: PROTOTYPE ONLY — NOT CONNECTED TO DRIFT, NO PATIENT USE.** The separate fail-closed Web clinical vault gate remains enabled.

## Source / exact proof

- Candidate branch: feat/w02-web-bff-readonly-preflight-20261028, parent 6bd5a3fb8caf8fbc4e792da2d6945b8b10718fd4.
- frontend/web/iamina_vault_envelope.mjs — WebCrypto-only AES-256-GCM, 96-bit random nonce per snapshot, 128-bit tag, authenticated associated data (format + version + patient vault scope + revision). Canonical base64url ciphertext envelope.
- scripts/tests/test_w02_encrypted_vault_envelope.mjs — 16 synthetic Node.js v22.16.0 assertions **executed and PASS** in an isolated local container. Exact blob SHA1 before Git publication: module bc7c112c4238202a7fc74331846197e4046a8bc9, tests e23df62156b78b9435d7ae8f000b15754a5cd9bf; GitHub blobs must match before commit.
- Independent crypto interoperability oracle executed and PASS using Python cryptography v46.0.4 AESGCM: Node-encrypted synthetic bytes decrypted in Python and Python-encrypted synthetic bytes decrypted by Node, with the same authenticated metadata. Does not prove browser storage durability or safety.
- Headless Chromium direct navigation to localhost and file URLs was blocked by the runner's administrator policy before tests executed. **0 Chrome tests claimed.**
- New code is not imported by Flutter, cannot silently enable patient writes or bypass Web deny gate. No Web persistent data written or legacy data modified.

## Key design

- A fresh createRecoverySecret() emits 256 random bits encoded as 43 URL-safe chars. It must be saved by the user OUTSIDE browser storage through a future UX. It is a capability, not a memorable password; losing the only copy means loss of decryption access.
- importRecoverySecret() creates a non-exportable AES-GCM CryptoKey and zeroes its transient decoded byte buffer. Does not guarantee complete memory scrubbing (JavaScript strings and browser GC).
- Caller may supply the imported non-exportable key and a verified vault scope. Scope and revision are authenticated but excluded from the ciphertext record, limiting metadata leakage.
- rotateVaultSnapshot() decrypts and reseals at a higher revision, wiping the decrypted byte array in finally. Rotation is NOT atomic until a transactional durable adapter exists; old snapshots may remain recoverable if retained.
- minimumRevision must come from a separately trusted and durable revision authority; simply using a value read from the same mutable browser storage does NOT prevent rollback. AAD detects tampering, not deletion or replay of a previously valid snapshot without this anchor.
- WebAuthn PRF, key escrow/recovery, server authorization, secure UX and recovery after lost credentials are NOT implemented. A WebAuthn signature is not a database encryption key.

## Mandatory gaps before any clinical persistence

1. Prove an actual browser-only in-memory SQLite executor that cannot silently fall back to plaintext OPFS/IndexedDB; connect encrypted export/import without plaintext WAL, cache or backups.
2. Implement atomic encrypted commit/recovery, crash interruption tests, disk-full/quota handling and two-tab locks/version CAS (no lost updates). Full-database snapshots per write can have high latency/size; performance and recovery require measurement.
3. Provision trusted revision tracking, safe per-vault key custody, device unlock and strong recovery flow; never store recovery secret adjacent to ciphertext and assume it is protected.
4. Quarantine and assess existing plaintext amina and per-user Web stores without deleting or claiming migration performed. Perform explicitly authorized migration with rollback/restore evidence.
5. Verify Chrome mobile/tablet/desktop including refresh, offline, A→B→A, wrong key, tamper, revoked login, quota and physical IndexedDB/OPFS plaintext search; independent security/privacy review and adversarial checks. Then one final GitHub CI at exact integration HEAD.
6. W01-G1…G7 closeout/merge and postmerge success is a roadmap prerequisite. Obtain separate explicit owner GO for any W02 Vercel Preview deployment; perform real synthetic W02 Web→BFF→API→Neon and independent auth_user=0. Production and patient use remain NO-GO.

References: [IAMINA ROADMAP W02](../ROADMAP.md), [W02 at-rest fail-closed gate](2026-10-28-w02-web-vault-at-rest-gate.md), [Drift Web](https://drift.simonbinder.eu/platforms/web/), [Drift encryption](https://drift.simonbinder.eu/platforms/encryption/), [MDN WebAuthn PRF](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API/WebAuthn_extensions).
