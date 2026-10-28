# IAMINA W02 — Encrypted ciphertext-only IndexedDB adapter (2026-10-28)

## Goal / observable success / evidence

Goal: prepare a Web-only ciphertext persistence primitive for already serialized SQLite snapshots with no plaintext persistent SQLite write, no cross-patient ciphertext disclosure, concurrent update compare-and-swap and strict IndexedDB transaction durability where supported.

Observable interim success: new dedicated database name, random opaque 256-bit slot, values containing only AES-GCM envelope, no legacy stores inspected, incompatible browsers refuse writes, and synthetic transaction failures do not overwrite older ciphertext. The module is a standalone prototype; it is NOT the clinical SQLite/Drift Web executor and must never be presented as full end-to-end at-rest protection.

Evidence: new files:
- frontend/web/iamina_vault_ciphertext_store.mjs (Git blob SHA1 fe5fa7633952a01da84fada3b674b8439a2cb9aa).
- scripts/tests/test_w02_ciphertext_store.mjs (Git blob SHA1 7bcfefc3abee12f87068f341d9747a180a0890f3).
- Existing prior cryptographic envelope frontend/web/iamina_vault_envelope.mjs (SHA1 bc7c112c4238202a7fc74331846197e4046a8bc9).

A local isolated shell executed Node v22.16.0 with Python 3.13.5 / SQLite 3.46.1:
    node --test scripts/tests/test_w02_ciphertext_store.mjs scripts/tests/test_w02_encrypted_vault_envelope.mjs

39/39 PASS; zero fail, including a genuine Python SQLite database serialized in memory, encrypted to an in-memory IndexedDB transaction test double, decrypted, deserialized in SQLite and SELECT-verified. 23 persistence tests and 16 cryptographic tests. The tests exercise wrong key, wrong patient A/B, corrupted envelope, missing known snapshot, tampered expected ciphertext, concurrent writers, abort after staged write, quota failure, strict-durability unavailable, restore, and revision-floor failure. No real IndexedDB or Flutter browser runtime was executed for this new code; Chromium direct navigation remained administrator-blocked in the prior attempt. Do not confuse simulated transaction atomicity with OS-level crash consistency.

## Design and boundaries

- Dedicated IDB database iamina_w02_ciphertext_only_v1, store sealed_snapshots. Only records with slot and envelope fields with a randomly generated opaque 256-bit slot, not clinical plaintext, medical record, account ID or recovery secret. Slot-to-verified-account mapping is intentionally NOT implemented and must be secured separately.
- Existing AES-256-GCM envelope provides authenticated data (version, namespace, revision) and random 96-bit nonce. Encryption occurs before IDB readwrite transaction; get(slot) and put({slot,envelope}) execute without awaits in the SAME transaction. CAS prevents two writers from silently clobbering a stale revision.
- On update, expected prior ciphertext must decrypt under the same supplied key and owner scope before committing; integrity failures are refused. Recovery key must remain outside browser persistence. No user account is authorized by the IDB layer.
- Browser write requests durability strict AND verifies transaction.durability === strict, otherwise fails closed. Per MDN this is only a browser durability hint, not proof against OS power loss. Strict mode support and behavior require a REAL browser test.
- Caller must provide minimumRevision from an INDEPENDENT trusted source. A revision stored alongside its own ciphertext cannot defeat rollback. Adapter does not create this authority.
- Restore with a known nonzero trusted revision and missing ciphertext fails with missing_known_snapshot rather than creating a new empty vault.
- No deletion, reencryption, automatic migration or remote call touches previously written unencrypted Web vaults. Native clients and patient clinical guard remain unchanged.

## NOT DONE / blocking gates

1. Replace current Drift Web persistent executor with a proven SQLite WASM RAM-only executor; connect serialized imports/exports to this ciphertext adapter, with no plaintext OPFS, IndexedDB, WAL, backups, browser caches or service-worker leakage. Current AppDatabase.forPatientVault Web clinical deny gate stays ON.
2. Prove real browser transaction and disk behavior (Chromium, Safari, Firefox), cold restart, crash/power-loss, quota, offline and A→B→A two-tab isolation. Inspect actual physical browser IndexedDB/OPFS content for plaintext; resolve strict durability compatibility. Implement safe backup/restore without false claims of hardware-durable commit.
3. Implement strong recovery/enrollment UX and key lifecycle (WebAuthn PRF if reliably supported, or audited recovery flow), trusted antirollback floor, secure account↔slot mapping, scope-bound authorization, deletion/rotation and non-destructive plaintext legacy migration.
4. Review independent privacy/security and clinical data policies, repeat exact-HEAD Flutter/Chrome tests, then one final CI run per roadmap. W01 closure is a prerequisite to W02 merge. Obtain owner explicit Vercel Preview GO before hosted A→B→A / BFF / Neon and independent SQL zero.

W02 status: DRAFT / clinical & production NO-GO. Safety gate does not permit real patient use. No Vercel deploy, database mutation or merge authorized.

Primary sources: https://developer.mozilla.org/en-US/docs/Web/API/IDBDatabase/transaction and https://developer.mozilla.org/en-US/docs/Web/API/IDBTransaction/durability and https://drift.simonbinder.eu/platforms/web/.
