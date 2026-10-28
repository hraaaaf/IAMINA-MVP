import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';

const candidate = readFileSync('frontend/lib/data/drift/w02_web_memory_sqlite_candidate.dart', 'utf8');
const dbPath = 'frontend/lib/data/drift/database.dart';
const web = readFileSync('frontend/test/web/w02_web_memory_sqlite_candidate_test.dart', 'utf8');

test('explicit in-memory VFS is the only registered sqlite WASM filesystem', () => {
  assert.match(candidate, /final memory = InMemoryFileSystem\(\)/);
  assert.match(candidate, /registerVirtualFileSystem\(memory, makeDefault: true\)/);
  assert.doesNotMatch(candidate, /IndexedDbFileSystem|OpfsFileSystem|DriftWebStorage|driftDatabase\(/);
});
test('only opened in-memory executor is returned, no automatic storage chooser', () => {
  assert.match(candidate, /WasmDatabase\.opened\(/);
  assert.doesNotMatch(candidate, /WasmDatabase\.open\(|WebDatabase\(|WasmDatabase\.probe\(/);
});
test('snapshot is checked before constructing sqlite and no partial transaction is exported', () => {
  const initialCheck = candidate.indexOf('if (initial != null) _assertSnapshot(initial);');
  const load = candidate.indexOf('WasmSqlite3.loadFromUrl');
  assert.ok(initialCheck >= 0 && initialCheck < load);
  assert.match(candidate, /!_sqlite\.autocommit/);
  assert.match(candidate, /w02_unexpected_sqlite_sidecar/);
  assert.match(candidate, /_memory\.fileData\.clear\(\)/);
});
test('runtime patient guard remains fail-closed; candidate is unreferenced', { skip: !existsSync(dbPath) }, () => {
  const db = readFileSync(dbPath, 'utf8');
  assert.match(db, /encrypted_web_patient_vault_unavailable/);
  assert.doesNotMatch(db, /W02WebMemorySqliteCandidate|w02_web_memory_sqlite_candidate/);
});
test('browser-only acceptance tests cover real SQLite round trip and no silent reuse', () => {
  assert.match(web, /W02_SYNTHETIC_734/);
  assert.match(web, /authenticatedSnapshot: encryptedInput/);
  assert.match(web, /new volatile connection cannot see prior synthetic records/);
});

test('W02 Chrome WASM diagnostic uses an explicit Flutter asset and real byte-loader', () => {
  const pubspec = readFileSync('frontend/pubspec.yaml', 'utf8');
  assert.match(candidate, /WasmSqlite3\.load\(sqlite3WasmBytes\)/);
  assert.match(candidate, /w02_wasm_load_timeout/);
  assert.match(web, /TestWidgetsFlutterBinding\.ensureInitialized\(\)/);
  assert.match(web, /rootBundle\s*\.load\('web\/sqlite3\.wasm'\)/);
  assert.match(pubspec, /- web\/sqlite3\.wasm/);
  assert.match(pubspec, /sqlite3: 2\.9\.4/);
});
