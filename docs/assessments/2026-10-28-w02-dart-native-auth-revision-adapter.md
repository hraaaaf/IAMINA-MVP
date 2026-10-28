# IAMINA — W02/D10 Option A : Dart Native-auth epoch gated API adapter (2026-10-28)

Goal: prove a real Flutter/Dart transport adapter only for HTTPS IAMINA Web Preview, capturing AuthService native Django account, epoch and remote credential verification, refreshing cross-tab stored bearer and vault namespace **before and after every BFF request**. No patient routes or AppDatabase imports this file. Preview build-time flag is required for real adapter; tests inject a synthetic source, `MockClient`, and an HTTPS test origin.

Files: `frontend/lib/data/drift/w02_native_revision_client.dart`, `frontend/test/web/w02_native_revision_client_test.dart`. Actions workflow `w02-sqlite-wasm-stage-diagnostics.yml` executes the new Dart Chrome tests. Fail closed: Firebase, audit device, unverified native, cross-tab revoke, A→logout→B, wrong verified scope, forged BFF result, wrong revision receipt, network timeout, non-HTTPS URL or non-preview runtime. No credential logging or persistent browser token.

Unchanged: Flutter `AppDatabase.forPatientVault` fail-closed `encrypted_web_patient_vault_unavailable`; JS synthetic fixture remains test-only outside shipped web bundle; no Neon/Vercel/merge/medical patient account write. A Dart adapter test does not constitute end-to-end hosted BFF→API→Postgres nor a data-recovery guarantee.

Success: exact HEAD Chrome + Flutter --fatal-infos and static code-contract logs. Additional independent security-review and human Vercel Preview gate remain mandatory. Next: integrate this Dart transport with injected Option A JS fixture and memory SQLite in an isolated Chrome end-to-end test (no patient runtime), then adjudicate crash recovery and key lifecycle.

## Cross-layer Chrome integration (synthetic, no hosted API)

A real Chrome 3rd-path test now exercises `W02NativeRevisionClient` (account verified + bearer + auth epoch, `MockClient` matching server Option A receipts) → `W02SyntheticBrowserBridge` (WebCrypto AES-GCM + IndexedDB CAS) → real in-memory Flutter Drift SQLite WASM → ciphertext restore and SQL SELECT. The JS fixture returns a canonical digest of its encrypted envelope. The mocked revision authority has **no PostgreSQL**; the separate #40725428391 run validates real PG row lock and bearer backend. The cross-layer test is not an end-to-end cloud Preview certification. Wrong account epoch denies reused A lease. No app routes changed.
