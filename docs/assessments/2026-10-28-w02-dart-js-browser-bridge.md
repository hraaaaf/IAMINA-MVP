# IAMINA W02/D10 — Web Dart ↔ JS AES-GCM IndexedDB Browser Proof (28/10/2026)

## Goal
In real Chrome test only, pass actual Drift SQLite WASM bytes Dart→JS Uint8Array, encrypt with AES-256-GCM, persist ciphertext-only in IndexedDB through atomic CAS, reopen via WebCrypto, and rehydrate a second volatile Drift executor. Deny wrong secret, wrong synthetic owner and stale revision. Never touch patient runtime/legacy data.

## Strict perimeter
- `iamina_w02_browser_bridge_probe.mjs` permits only synthetic `amina_vault_v1_native_734`/`812` fixtures. The user-held secret, slot and trusted revision supplied by tests are NOT a clinically sound recovery/authorization mechanism. No external trusted monotonic floor.
- `w02_synthetic_browser_bridge.dart` uses typed-array JS interop from an imported ES module, pinning the URL to `http://127.0.0.1:7399/iamina_w02_browser_bridge_probe.mjs`; no arbitrary source, no production path import. Buffer clearing is best effort.
- Fixture HTTP server serves the bridge fixture from scripts/fixtures, never from frontend/web packaged application assets, and exposes only WASM plus the audited dependency modules; no patient secrets, data, or arbitrary directories.
- Garde `database.dart` remains `encrypted_web_patient_vault_unavailable`; no Vercel/Neon/Production/merge.
- A green JS test and a green Chrome SQLite test do not substitute for **this** actual Dart↔JS round-trip. Only exact-SHA CI is proof.

## Remaining gates
Authenticated owner and auth-epoch contract with verified principal, reliable monotonic revision authority OUTSIDE browser/local storage, recovery UX following crash/quota, permanent key/backup lifecycle, migration legacy with verified owner and no-loss, E2E A→B→A hosted, independent security/privacy audit, W01 closeout, then user-approved Preview and UI BEFORE/AFTER. No D10-B Web patient enablement.
