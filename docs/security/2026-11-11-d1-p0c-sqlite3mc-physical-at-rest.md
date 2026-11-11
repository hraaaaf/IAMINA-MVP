# IAMINA D1.6 — isolated real ciphertext feasibility experiment

**GOAL:** choose a real SQLite Web at-rest encryption engine and prove that
the persisted IndexedDB bytes, not just a detached AES envelope or login
lock, are ciphertext. Development only, no historical patients.

## Verified baseline

- IAMINA is on Flutter 3.41 + Drift 2.35.4 (integration PR #1348).
- The current patient vault uses the normal sqlite3.wasm and drift_worker.js,
  so persistent SQLite database pages are not encrypted. The existing
  LocalBackup JSON export likewise is not encrypted.
- DriftWebOptions in upstream drift_flutter 0.3.1 lacks a way to pass a
  per-session setup callback/secret. The stock precompiled worker does not
  apply session-scoped PRAGMA key; replacing sqlite3.wasm by sqlite3mc.wasm
  is NOT an adequate fix, and may silently leave a plaintext database.
- Verified upstream at tag drift-2.35.4:
  drift_flutter/lib/src/connect.dart, drift_flutter/lib/src/web.dart,
  drift/lib/src/web/wasm_setup/shared.dart.
- Official sqlite3mc.wasm for drift-2.35.4, SHA256
  408a1d9bf8071bfb6e91aba005e6c8e2072c240784e1d199bbd7eb441dd5ea94.

## Independent mechanical test

1. CI fetches the SHA-locked encrypted SQLite3MC WebAssembly binary to
   an **uncommitted staging fixture path only**.
2. An isolated Dart entrypoint uses WasmSqlite3 + IndexedDbFileSystem,
   not IAMINA AppDatabase. It runs with a test-only fake key/canary.
3. A plaintext control uses exactly the same WASM and VFS without
   a PRAGMA key, writes a fake canary; the Playwright test MUST find
   those bytes in raw IndexedDB records.
4. The encrypted variant applies a fake PRAGMA key before CREATE,
   INSERT, or SELECT. The Playwright test scans the actual IDB block
   payloads and MUST NOT find the fake canary.
5. Cold browser page/SQLite close + reopen with correct key MUST
   retrieve the fake value. Reopen with wrong key MUST be rejected.
6. Tests run independently on Chromium and WebKit, no extra headers.
   Reports are retained as CI artifacts.

## Intentionally absent and blocking

This is **not a real IAMINA application encryption implementation**.
The fake key appears in fixture source solely to make the proof repeatable
and may not be used in the application. It says nothing about real
passphrase KDF design, key material management, concurrent worker
admission, app authentication, raw WAL/journal backups, hard drive
recovery, tamper detection, or the protection of exported JSON.
The full patient runtime and Vercel builds remain unchanged.

**Next engineering gate:** implement a secure, audited session key
delivery/provisioning mechanism to a custom Drift worker or a secure
single-connection adapter with no plaintext fallback. Bind keys to
verified patient identities, prevent cross-owner open, close/zeroize
secrets, handle revocation and encrypted exports, then repeat the
same physical raw-byte tests on the actual clinical database.
Safeguard against Web XSS/compromised same-origin code.

**Human gates:** no merge, no Vercel (including preview), no patient
data, no clinical approval until an independent review with evidence.
