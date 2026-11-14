# D1 — Web patient vault, security design and hard GO gate

Status: **PROPOSED / PATIENT NO-GO**. Scope: IAMINA Flutter Web + Drift/sqlite3 WASM, PR #1377. This is a security design contract, **not** a claim of implemented or verified cryptography.

## Decision and threat model
The current `driftDatabase(... DriftWebOptions(...))` opens SQLite through a Web worker and has no verified authenticated encryption of patient pages or WAL/journal/cache. The D1 fail-closed admission denial MUST remain until an independently reviewed replacement has passed all gates below. An app UI PIN or browser secure-storage preference is **not** disk encryption and MUST NOT be represented as such.

Protect against: at-rest extraction from IndexedDB/OPFS and offline browser profiles; A→logout→B leakage; replay/swap/malformed ciphertext; session races; old installed PWA offline writers; nonrecoverable key loss; server-side key or plaintext logging. A fully compromised running origin, XSS with active unlocked key, or malicious browser extension is **not** solved merely by at-rest encryption; separate CSP/XSS controls are required.

## Implementation contract (all gates mandatory)
1. Select an audited, browser-compatible **authenticated encryption** implementation for the *entire* clinical SQLite persistence, including database pages, schema, WAL/journals, temporary stores, export files and backups. A SQL column transformer alone is insufficient. Provide a precise plaintext boundary diagram and prove that no clinical plaintext persists outside encrypted containers. Do not claim SQLCipher works in the existing Drift WASM worker without a reproducible integration test.
2. Generate a random 256-bit data encryption key per physical owner/vault; ensure distinct owners cannot share key material. Use a reviewed envelope-key scheme with authenticated header (format/version/owner binding/key ID/KDF parameters) and strong random nonces. Never derive a vault key directly from patient ID, email, PIN, session token, IP or the global app-lock credential.
3. Bind vault unlock to authenticated owner **and** explicit key authorization. Define enrollment and rotation; disallow silent creation of a new empty vault when a previously enrolled owner's ciphertext exists but key is missing. Revoke keys and close DB/providers immediately on sign-out or auth epoch change; prevent stale async opens.
4. Recovery and backup: choose and validate a user-controlled recovery mechanism (e.g. independently generated, one-time display recovery material wrapped through reviewed KDF with realistic browser limits), with tested restore into an empty profile and wrong-key/tamper handling. Never send raw keys to backend or log them. A recovery key exposed by a screenshot, analytics or telemetry fails the gate.
5. Legacy: enumerate existing `amina`, `amina_vault_v1_native_*`, `amina_vault_v1_device_*`, and old worker storage BEFORE touching them. Existing unencrypted DBs are **quarantined read-only** until ownership can be independently proven and a verified encrypted migration is available. Import must be explicit, reversible (verified backup before mutation), atomic and idempotent. No automatic A→B attribution, overwrite or delete.
6. PWA: test already-installed service workers and Web clients *offline*. Enforce a preflight writer-version fence **before** first clinical read/write, not only in the newest JS bundle. Verify legacy offline writers cannot persist plaintext after rollout, or explicitly declare migration impossible and keep clinical Web NO-GO; an online-only feature flag does not block older offline app versions.
7. Interop: FR/EN/AR user flows (new local enrollment; returning owner; native Django auth; lock; recovery; offline; A→B→A) and Chrome + Safari/WebKit desktop/mobile. Avoid treating passing audit-only synthetic namespace as clinical encryption proof.

## Observable GO / NO-GO evidence
- Repeatable crypto integration test with physical IndexedDB/OPFS artifact inspection: no patient identifiers, sugar readings, medications, schema names or clinical strings in **any persisted unencrypted database/WAL/cache** after cold restart.
- Negative tests: wrong key, corrupted ciphertext/tag, copy A ciphertext into B namespace, replay prior header, rollback/cross-version store, lock failure, key lost, interrupted migration, two tabs, auth race, offline restart, legacy PWA regression.
- Positive tests: correct owner/key restores data after browser shutdown; backup + restore with independent browser profile; recovery and rotation; A→B→A no cross-owner observation; D5/D7/D19/D22 complete on real clinical code paths.
- Exact commit SHA, browser/build versions, scripts, unredacted aggregate test counts and redacted evidence artifacts; independent security review and human clinical GO recorded before merge or deployment.
- **Never** disable, skip, reclassify or mock the failing clinical flows to obtain a green check. Failure stays visible.

## Current verified facts (2026-11-13)
PR #1377 at `20f78d446e6cef91a6fdf25d86e79f176e7cd059`: 18 GitHub workflows successful, 4 failed (D5/D7/D19/D22), 0 running. Production safe-hold negative Chrome test passes at 390×844, 768×1024 and 1280×900; clinical encryption and recovery unimplemented, actual clinical acceptance **NO-GO**. `DESKTOP-3MAJEEH` development device was offline when this gate was authored; no reproducible local Flutter/Chrome runtime was available in the assistant's current container.

## Next permitted work
Implement a reviewed encrypted SQLite persistence adapter in a separate candidate, with key management and recovery. Preserve the existing fail-closed production path until all preceding proof gates pass. PR remains Draft. No Vercel deployment or merge without explicit authorization.
