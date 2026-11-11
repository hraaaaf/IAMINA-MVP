#!/usr/bin/env bash
# IAMINA D1.8 — matching official Drift 2.35.4 Web assets only.
# Default VERIFY (offline, for normal builds). FETCH only for staging.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/web"
WORKER_SHA="48c950cd8e3bc3cddb34816c860e228be8832bef07a297c27e9907c057ff8162"
WASM_SHA="e7451780e78c56ff864fe9317a0fbcd6aeb2e8de3beba7f5efd963202f7ec3d9"
verify() {
  printf '%s  %s\n' "$WORKER_SHA" "$WEB/drift_worker.js" \
    "$WASM_SHA" "$WEB/sqlite3.wasm" | sha256sum --check --status || {
      echo "D1.8 ERROR: mismatched Drift Web worker/WASM, refusing build" >&2
      return 70
    }
  echo "D1.8 pinned Drift 2.35.4 assets SHA256 OK"
}
mode=verify
if [ "$#" -ge 1 ]; then mode="$1"; fi
case "$mode" in
 verify) verify ;;
 fetch)
   tmp="$(mktemp -d)"
   trap 'rm -rf "$tmp"' EXIT
   for asset in drift_worker.js sqlite3.wasm; do
     curl --fail --location --retry 3 --silent --show-error \
       "https://github.com/simolus3/drift/releases/download/drift-2.35.4/$asset" \
       --output "$tmp/$asset"
   done
   printf '%s  %s\n' "$WORKER_SHA" "$tmp/drift_worker.js" \
     "$WASM_SHA" "$tmp/sqlite3.wasm" | sha256sum --check --status || {
       echo "D1.8 ERROR: official asset hash mismatch; no install" >&2
       exit 70
     }
   cp "$tmp/drift_worker.js" "$WEB/drift_worker.js"
   cp "$tmp/sqlite3.wasm" "$WEB/sqlite3.wasm"
   verify ;;
 *) echo "Usage: $0 [verify|fetch]" >&2; exit 64 ;;
esac
