// Diagnostic only: bare Dart 3.11 JS runner using SQLite3MC in-memory.
// No Flutter, no Drift worker, no persistent data, no user information.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:sqlite3/wasm.dart';

Future<void> main() async {
  html.document.title = 'D1_BARE_DART_RUNNING';
  var step = 'WASM_LOAD';
  try {
    final sqlite = await WasmSqlite3.loadFromUrlString('/sqlite3mc.wasm');
    step = 'INMEMORY_VFS';
    sqlite.registerVirtualFileSystem(InMemoryFileSystem(), makeDefault: true);
    step = 'OPEN_DB';
    final db = sqlite.open('/test_database');
    try {
      step = 'CIPHER_CHECK';
      if (db.select('PRAGMA cipher').isEmpty) {
        throw StateError('NO_CIPHER');
      }
      step = 'KEY_SETUP';
      db.execute("PRAGMA key = 'FAKE_CI_ONLY_NO_USER_DATA'");
      step = 'CREATE_SELECT';
      db.execute('CREATE TABLE d1_ci_fake_canary (sample TEXT NOT NULL)');
      db.execute("INSERT INTO d1_ci_fake_canary VALUES ('CI_FAKE')");
      final rows = db.select('SELECT sample FROM d1_ci_fake_canary');
      if (rows.length != 1 || rows.single['sample'] != 'CI_FAKE') {
        throw StateError('TEST_VALUE_NOT_READABLE');
      }
    } finally {
      db.close();
    }
    html.document.title = 'D1_BARE_DART_PASS';
  } catch (error, stack) {
    // This diagnostic has no real secrets or patients, but never log a key or
    // full query. Expose only a step / exception runtime type.
    html.document.title = 'D1_BARE_DART_FAIL_' +
        step + '_' + error.runtimeType.toString().replaceAll(' ', '_');
    html.document.documentElement?.dataset['d1Stack'] =
        stack.toString().substring(0, 450);
  }
}
