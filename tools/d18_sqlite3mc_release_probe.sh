#!/usr/bin/env bash
# D18 isolated CI proof: inspect pinned upstream WASM release; no production integration.
set -euo pipefail
VERSION="sqlite3mc-2.6.1-sqlite-3.54.0-wasm.zip"
EXPECTED_SHA256="aba121490fd6123bcbef8404ee26df9b26c0301063781e2aa31f05aed6f48384"
URL="https://github.com/utelle/SQLite3MultipleCiphers/releases/download/v2.6.1/$VERSION"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
curl --fail --location --retry 2 --proto '=https' --tlsv1.2 "$URL" --output "$WORK/$VERSION"
echo "$EXPECTED_SHA256  $WORK/$VERSION" | sha256sum -c -
unzip -l "$WORK/$VERSION"
unzip -q "$WORK/$VERSION" -d "$WORK/extracted"
find "$WORK/extracted" -type f -print | sort
WASM="$(find "$WORK/extracted" -type f -name '*.wasm' -print -quit)"
test -n "$WASM" || { echo 'NO_WASM_IN_RELEASE'; exit 1; }
node tools/d18_sqlite_cipher_preflight.cjs "$WASM"
ROOT="$(dirname "$(dirname "$WASM")")"
printf '%s\\n' '<!doctype html><meta charset="utf-8"><script src="/jswasm/sqlite3.js"></script>' > "$ROOT/d18-probe.html"
python3 -m http.server 7398 --bind 127.0.0.1 --directory "$ROOT" > "$WORK/http.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; rm -rf "$WORK"' EXIT
node tools/d18_sqlite3mc_browser_api_probe.cjs
echo 'D18 browser key API discovery complete; encrypted persistence NOT verified'
