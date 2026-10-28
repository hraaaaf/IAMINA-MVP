# W02 — Memory-only SQLite WASM executor candidate (2026-10-28)

## Goal / observable criterion

Create an isolated Flutter Web/Drift candidate with explicit InMemoryFileSystem instead of Drift's default OPFS/IndexedDB storage selection; allow an already-authenticated SQLite byte snapshot to be opened as an in-memory SQLite file, queried through a Drift executor, exported as bytes, and closed with memory cleared.

**Not a patient runtime integration.** The existing Web clinical patient vault deny gate in database.dart is UNCHANGED. No JS bridge, user recovery UX, key authority or automatic encrypted commit is implemented by this candidate; the preceding JavaScript AES-GCM envelope/IndexedDB ciphertext store remains independent.

## Exact pinned API evidence

Project lock: drift 2.31.0, sqlite3 2.9.4, typed_data 1.4.0. Primary source code inspected:
- https://api.github.com/repos/simolus3/drift/contents/drift/lib/wasm.dart?ref=drift-2.31.0 — WasmDatabase.opened(CommonDatabase, closeUnderlyingOnClose:false) and explicit inMemory API.
- https://api.github.com/repos/simolus3/sqlite3.dart/contents/sqlite3/lib/src/in_memory_vfs.dart?ref=sqlite3-2.9.4 — InMemoryFileSystem.fileData and virtual file bytes.
- https://pub.dev/packages/sqlite3/versions/2.9.4 ; https://drift.simonbinder.eu/platforms/web/ .

Implementation: frontend/lib/data/drift/w02_web_memory_sqlite_candidate.dart. Seeds an explicit memory VFS with a previously authenticated SQLite image (if supplied), validates header and maximum 64 MiB, rejects bad journal/temp-store mode and quick-check, exposes WasmDatabase.opened, refuses exporting during uncommitted SQLite transactions or nonempty sidecars, copies bytes, closes executor and disposes the SQLite connection and volatile file system. The NULL initial snapshot path is test-only; it cannot confer authorization to create a new real patient vault. Caller is responsible for validating AAD, patient scope, recovery key and independent rollback floor; not implemented here.

Tests authored: frontend/test/web/w02_web_memory_sqlite_candidate_test.dart (3 Flutter Web/Chrome cases: synthetic SQL insert -> memory snapshot -> reopen/SELECT, invalid image rejected, new independent memory vault empty). **NOT EXECUTED**: no Dart/Flutter SDK installed in the local runner, browser loading restricted by administrator; tests and compilation require an eligible isolated sandbox/CI on exact SHA. Do not claim browser passes or successful Flutter build.

Static Node regression contract: scripts/tests/test_w02_memory_sqlite_source_contract.mjs. Locally 4 PASS / 1 SKIP (runtime database.dart absent from standalone partial checkout). This tests only source shape, NOT runtime behavior. Existing 39/39 Node test evidence applies to previously published JavaScript ciphertext primitives and is NOT a substitute for Dart/Chrome verification.

## Release blockers / NO-GO

1. Run dart analyze + flutter test --platform chrome with pinned dependencies and WASM asset served correctly; prove actual WASM/SQLite replay and inspect physical browser IndexedDB/OPFS for plaintext. Repair any incompatibilities.
2. Build a durable authenticated JS-Dart bridge to the prior ciphertext-only IndexedDB store: no unverified account enrollment, atomic flush, stale-tab conflict prevention, quotas, offline, crash and deletion.
3. Independently trusted revision floor and account-to-slot mapping; safe key/recovery lifecycle and user-facing recovery UX. Browser raw storage must not reveal clinical data.
4. No-loss quarantine and authorized migration of legacy plaintext stores, independent security/privacy review, real browser synthetic A-to-B-to-A.
5. Close W01 before W02 merge as required by roadmap; run only one final GitHub CI once integrated; seek separate explicit Vercel Preview GO, then real hosted synthetic Web to BFF to API to Neon with independent SQL cleanup auth_user=0.

**W02 patients/Production NO-GO**. No Vercel deployment, Neon mutation, PR merge, patient data or clinical app-path activation in this subpass. No UI/UX change in the product.
