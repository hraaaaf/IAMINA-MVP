# IAMINA — W02/D10 Option A : Dart Native-auth epoch gated API adapter (2026-10-28)

Goal: prove a real Flutter/Dart transport adapter only for HTTPS IAMINA Web Preview, capturing AuthService native Django account, epoch and remote credential verification, refreshing cross-tab stored bearer and vault namespace **before and after every BFF request**. No patient routes or AppDatabase imports this file. Preview build-time flag is required for real adapter; tests inject a synthetic source, `MockClient`, and an HTTPS test origin.

Files: `frontend/lib/data/drift/w02_native_revision_client.dart`, `frontend/test/web/w02_native_revision_client_test.dart`. Actions workflow `w02-sqlite-wasm-stage-diagnostics.yml` executes the new Dart Chrome tests. Fail closed: Firebase, audit device, unverified native, cross-tab revoke, A→logout→B, wrong verified scope, forged BFF result, wrong revision receipt, network timeout, non-HTTPS URL or non-preview runtime. No credential logging or persistent browser token.

Unchanged: Flutter `AppDatabase.forPatientVault` fail-closed `encrypted_web_patient_vault_unavailable`; JS synthetic fixture remains test-only outside shipped web bundle; no Neon/Vercel/merge/medical patient account write. A Dart adapter test does not constitute end-to-end hosted BFF→API→Postgres nor a data-recovery guarantee.

Success: exact HEAD Chrome + Flutter --fatal-infos and static code-contract logs. Additional independent security-review and human Vercel Preview gate remain mandatory. Next: integrate this Dart transport with injected Option A JS fixture and memory SQLite in an isolated Chrome end-to-end test (no patient runtime), then adjudicate crash recovery and key lifecycle.

## Cross-layer Chrome integration (synthetic, no hosted API)

A real Chrome 3rd-path test now exercises `W02NativeRevisionClient` (account verified + bearer + auth epoch, `MockClient` matching server Option A receipts) → `W02SyntheticBrowserBridge` (WebCrypto AES-GCM + IndexedDB CAS) → real in-memory Flutter Drift SQLite WASM → ciphertext restore and SQL SELECT. The JS fixture returns a canonical digest of its encrypted envelope. The mocked revision authority has **no PostgreSQL**; the separate #40725428391 run validates real PG row lock and bearer backend. The cross-layer test is not an end-to-end cloud Preview certification. Wrong account epoch denies reused A lease. No app routes changed.


## 2026-10-28 — Flutter Web isolated native session/anchor bridge (post Option A server)

**Goal:** verify actual `AuthService.authEpoch`, `isRemoteCredentialVerified`, persisted/native Django ID, browser token and exact physical vault namespace before **and after** every HTTPS Preview BFF metadata operation; then demonstrate a combined synthetic Chrome transaction through encrypted IndexedDB and volatile SQLite WASM. The new adapter is `frontend/lib/data/drift/w02_native_revision_client.dart`, used only by tests and **never** imported by patient routes or AppDatabase.

**Proof stage 1 (complete):** code [30c84fb1](https://github.com/hraaaaf/IAMINA-MVP/commit/30c84fb1c275a2a0a9c3a88f5d90ae7667ceb0bb), [CI #40728794787](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40728794787) **SUCCESS**: 63/63 Node; 14/14 Flutter Chrome; 0 analyzer issue. Chrome tested A→logout→B, stale response after logout, Firebase refused, audit/refreshed scope denied, network and invalid Preview host refused. The "syntheticTestOnly" fixture is locked to `https://test-only.invalid`; the real adapter requires the compile-time Preview flag and exact IAMINA Web Preview host.

**Stage 2 (awaiting exact-SHA CI):** code [e1b338a8](https://github.com/hraaaaf/IAMINA-MVP/commit/e1b338a88baa87db20828be3fa7fe345260f6807), [CI #40729430613](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40729430613) queued at initial observation. New synthetic Chrome test does **not** contact deployed BFF/API/Neon: a `MockClient` models Django state/reserve/finalize while real Flutter Drift SQLite WASM bytes are AES-GCM sealed into real browser IndexedDB by JS, then reopened and compared with the **committed ciphertext envelope SHA-256** before SELECT. The result must not be called PASS until its GitHub run completes.

**Traceable boundaries:** GitHub comparison from W02 baseline `5a705712` to `e1b338a8`: seven files in the isolated fixture and test code, **no change** to `frontend/lib/data/drift/database.dart`, `frontend/web/index.html`, `frontend/api/preview-proxy.js` or backend production code. No Vercel Preview deployed, no Neon mutation and no patient data accessed.

**External blockers, not quietly solved:** (a) no full hosted Vercel Preview BFF→API→isolated Neon E2E without explicit deployment authorization; (b) cloud API feature flag remains OFF by default, W01 GO needed before W02 merge; (c) enrollment/recovery key lifecycle, backup and no-loss data migration of historical `amina` DB require separate user/security decision; (d) AppLock optional policy and real clinical vault opening are not authorized; (e) offline **read-only** is an unimplemented product goal, not a certified behavior: the prototype contacts the authority on each opening and rejects missing network. Option A **forbids offline writes**.

**Next exact:** complete and inspect CI #40729430613; if red, patch and rerun exact SHA; then final evidence/doc consistency, HEAD/CI/branch/Vercel recheck. Next gated step is deployment to isolated Preview and real cross-service E2E only after explicit GO; independent security/privacy review and W01 closeout remain necessary before patient D10 GO.
