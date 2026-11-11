// D1.6 experimental-only physical SQLite3MC/IndexedDB probe.
// The fake key and data below MUST NOT be used in IAMINA patient runtime.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:sqlite3/wasm.dart';

const fixture = 'D1_SQLITE3MC_FAKE_PATIENT_CANARY_8f4d7e23';
const fakeKey = 'D1_CI_ONLY_FAKE_KEY_NEVER_FOR_PATIENTS_3176';
const badKey = 'D1_WRONG_KEY_ONLY_9037';
const encryptedName = 'iamina_d1p0c_sqlite3mc_synthetic_v1';
const plaintextName = 'iamina_d1p0c_sqlite3mc_plain_control_v1';

Future<void> main() async {
  html.document.title = 'IAMINA_D1P0C_RUNNING';
  final phase = Uri.base.queryParameters['phase'];
  final isPlain = phase == 'seed_plain';
  final isCipher = {
    'seed_cipher', 'verify_cipher', 'wrong_key',
  }.contains(phase);
  if (!isPlain && !isCipher) {
    html.document.title = 'IAMINA_D1P0C_FAIL_PHASE';
    return;
  }
  IndexedDbFileSystem? storage;
  var stage = 'IDB_OPEN';
  try {
    storage = await IndexedDbFileSystem.open(
      dbName: isPlain ? plaintextName : encryptedName,
      writeAutomatically: false,
    );
    stage = 'WASM_LOAD';
    final sqlite = await WasmSqlite3.loadFromUrlString('sqlite3mc.wasm');
    stage = 'VFS_REGISTER';
    // Do not make the underlying VFS the default. SQLite3MultipleCiphers
    // requires its named encrypted VFS wrapper for PRAGMA key to work.
    sqlite.registerVirtualFileSystem(storage);
    stage = 'SQLITE_OPEN';
    final db = sqlite.open('/database',
        vfs: 'multipleciphers-${storage.name}');
    try {
      // The key must precede ALL schema reads and write statements.
      // The fake credentials exist only in this synthetic research fixture.
      if (isCipher) {
        stage = 'PRAGMA_KEY';
        db.execute("PRAGMA key = '" +
            (phase == 'wrong_key' ? badKey : fakeKey) + "'");
      }
      // SQLite ignores unknown PRAGMAs, so confirm cipher support.
      stage = 'PRAGMA_CIPHER';
      if (db.select('PRAGMA cipher').isEmpty) {
        throw StateError('FAIL_CLOSED_NO_CIPHER');
      }
      stage = 'SQLITE_TEST';
      if (phase == 'wrong_key') {
        var rejected = false;
        try {
          db.select('SELECT content FROM d1_cipher_canary');
        } catch (_) {
          rejected = true;
        }
        if (!rejected) {
          throw StateError('FAIL_CLOSED_WRONG_KEY_NOT_REJECTED');
        }
      } else if (phase == 'seed_plain' || phase == 'seed_cipher') {
        db.execute(
          'CREATE TABLE IF NOT EXISTS d1_cipher_canary (content TEXT NOT NULL)',
        );
        db.execute('DELETE FROM d1_cipher_canary');
        db.execute(
          'INSERT INTO d1_cipher_canary (content) VALUES (?)',
          [fixture],
        );
        final rows = db.select('SELECT content FROM d1_cipher_canary');
        if (rows.length != 1 || rows.single['content'] != fixture) {
          throw StateError('WRITE_READ_FAILED');
        }
      } else {
        final rows = db.select('SELECT content FROM d1_cipher_canary');
        if (rows.length != 1 || rows.single['content'] != fixture) {
          throw StateError('DECRYPT_READ_FAILED');
        }
      }
    } finally {
      db.close();
    }
    stage = 'IDB_FLUSH';
    await storage.flush();
    stage = 'IDB_CLOSE';
    await storage.close();
    storage = null;
    html.document.title = 'IAMINA_D1P0C_PASS_' + phase!.toUpperCase();
  } catch (error) {
    // WASM_LOAD is before any PRAGMA/key: safe to report transport error only.
    if (stage == 'WASM_LOAD') {
      final message = error.toString();
      html.document.documentElement?.dataset['d1WasmError'] =
          message.length > 350 ? message.substring(0, 350) : message;
    }
    // After loading, never print potentially sensitive SQL/error/key text.
    html.document.title = 'IAMINA_D1P0C_FAIL_' + stage;
    try {
      await storage?.close();
    } catch (_) {}
  }
}
