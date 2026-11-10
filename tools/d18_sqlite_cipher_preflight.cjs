#!/usr/bin/env node
/* D18 Web: fail-closed preflight for a candidate encrypted SQLite WASM.
 * This is NOT a confidentiality proof. No clinical data or production DB.
 * Usage: node tools/d18_sqlite_cipher_preflight.js path/to/candidate.wasm
 */
'use strict';
const fs = require('node:fs');
const crypto = require('node:crypto');
const candidate = process.argv[2];
if (!candidate || !fs.existsSync(candidate)) {
  console.error('BLOCKED: provide a real candidate encrypted SQLite WASM binary');
  process.exit(2);
}
const wasm = fs.readFileSync(candidate);
const hash = crypto.createHash('sha256').update(wasm).digest('hex');
if (wasm.length < 1024 || wasm.subarray(0, 4).toString('hex') !== '0061736d') {
  console.error('REJECTED: candidate is not a valid-sized WASM module');
  process.exit(1);
}
try {
  new WebAssembly.Module(wasm);
} catch (error) {
  console.error('REJECTED: WASM validation failed:', error.message);
  process.exit(1);
}
const wasmModule = new WebAssembly.Module(wasm);
const wasmExports = WebAssembly.Module.exports(wasmModule).map(item => item.name);
const sqliteExports = wasmExports.filter(name => /sqlite3_(open|prepare|exec|key|rekey)/i.test(name));
if (sqliteExports.length === 0) {
  console.error('REJECTED: valid WASM is not identifiable as a SQLite engine; no SQLite entrypoints');
  process.exit(1);
}
// Presence of SQLite exports does not establish cipher support or persistence.
console.log(JSON.stringify({
  status: 'BINARY_VALID_ONLY',
  sha256: hash,
  bytes: wasm.length,
  encryptedDatabaseVerified: false,
  sqliteEntrypointsDetected: sqliteExports,
  requiredNext: 'keyed SQLite open, persistent close/reopen, wrong-key rejection, raw storage inspection'
}, null, 2));
