# D1.8 — Fresh Web vault Drift 2.35.4 integration

User clarified: IAMINA is development, no historical patients. Scope is fresh Web installs only, no legacy migration and no deleting other developer data.

Pinned: Flutter 3.41, Drift 2.35.4, drift_flutter 0.3.1, sqlite3_flutter_libs 0.6.0+eol. Official release drift-2.35.4 worker SHA256 48c950cd8e3bc3cddb34816c860e228be8832bef07a297c27e9907c057ff8162; sqlite3.wasm SHA256 e7451780e78c56ff864fe9317a0fbcd6aeb2e8de3beba7f5efd963202f7ec3d9.

Installer script verifies both assets offline for builds. Staging-only fetch downloads and hashes first, then copies; binaries will be committed to this integration branch. No COOP/COEP headers. Origin-wide exclusive Web Lock runs before Flutter/Drift to refuse second tab.

Generator limitation: drift_dev >=2.35 analyzer/meta incompatible with pinned Flutter 3.41 meta 1.17. Remove drift_dev from build and retain committed generated database.g.dart. No schema changes until compatible codegen has been separately proven.

Required before release: full Web build, Chrome and WebKit cold persistence, single active tab denial, A/B/A, AppLock/recovery/backup; independently verified real local encryption remains D1.6 blocker. No merge/deploy Vercel or patient use. CI browser proof is synthetic only.
