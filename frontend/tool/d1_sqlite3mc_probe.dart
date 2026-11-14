// D1 feasibility ONLY: isolated synthetic SQLite3MultipleCiphers Web exercise.
// No patient data, no integration with IAMINA clinical AppDatabase, no stored key.
// A green result does not authorize Web patient vault admission.
import 'dart:convert';
import 'dart:html' as html;
import 'package:drift/drift.dart';
import 'package:drift/wasm.dart';
import 'package:sqlite3/wasm.dart';

// Zero-table synthetic Drift wrapper: tests the actual project's executor API.
class _SyntheticEncryptedDriftDb extends GeneratedDatabase {
  _SyntheticEncryptedDriftDb(QueryExecutor executor) : super(executor);
  @override
  int get schemaVersion => 1;
  @override
  Iterable<TableInfo<Table, dynamic>> get allTables => const [];
  @override
  Iterable<DatabaseSchemaEntity> get allSchemaEntities => const [];
}

const _dbName = 'iamina_d1_crypto_probe_20261113';
const _fileName = '/d1_cipher_probe.db';
const _syntheticPatient = 'D1_SYNTHETIC_GLUCOSE_ONLY_777_XY';
const _correctKey = 'D1_SYNTHETIC_TEST_KEY_GOOD_NOT_A_SECRET';
const _wrongKey = 'D1_SYNTHETIC_TEST_KEY_WRONG_NOT_A_SECRET';

void _publish(Map<String, Object?> result) {
  html.document.body?.text = jsonEncode(result);
}

Future<void> main() async {
  final proof = <String, Object?>{
    'scope': 'synthetic-only wasm/IndexedDB feasibility, NOT IAMINA clinical DB',
    'sqlite3mcWasm': 'sqlite3mc.wasm',
    'correctKeyRead': false,
    'wrongKeyRejected': false,
    'cipherAvailable': false,
    'persistentAfterReopen': false,
    'driftRead': false,
    'clinicalGo': false,
  };
  try {
    final sqlite3 = await WasmSqlite3.loadFromUrl(Uri.parse('sqlite3mc.wasm'));
    final fileSystem = await IndexedDbFileSystem.open(dbName: _dbName);
    sqlite3.registerVirtualFileSystem(fileSystem, makeDefault: true);

    final db = sqlite3.open(_fileName);
    try {
      final cipher = db.select('PRAGMA cipher');
      proof['cipherAvailable'] = cipher.isNotEmpty;
      if (cipher.isEmpty) throw StateError('Encryption not available');
      db.execute("PRAGMA key = '$_correctKey';");
      db.execute('CREATE TABLE IF NOT EXISTS readings (value TEXT NOT NULL)');
      db.execute('DELETE FROM readings');
      db.execute('INSERT INTO readings(value) VALUES (?)', [_syntheticPatient]);
      proof['correctKeyRead'] =
          db.select('SELECT value FROM readings').single['value'] == _syntheticPatient;
    } finally {
      db.dispose();
    }
    await fileSystem.flush();

    final wrong = sqlite3.open(_fileName);
    try {
      wrong.execute("PRAGMA key = '$_wrongKey';");
      try {
        wrong.select('SELECT value FROM readings');
      } on Exception {
        proof['wrongKeyRejected'] = true;
      }
    } finally {
      wrong.dispose();
    }
    final reopened = sqlite3.open(_fileName);
    try {
      reopened.execute("PRAGMA key = '$_correctKey';");
      proof['persistentAfterReopen'] =
          reopened.select('SELECT value FROM readings').single['value'] ==
              _syntheticPatient;
      final drift = _SyntheticEncryptedDriftDb(
        WasmDatabase.opened(reopened, closeUnderlyingOnClose: false),
      );
      try {
        final row = await drift.customSelect('SELECT value FROM readings').getSingle();
        proof['driftRead'] = row.read<String>('value') == _syntheticPatient;
      } finally {
        await drift.close();
      }
    } finally {
      reopened.dispose();
    }
    await fileSystem.flush();
    proof['ok'] = proof['cipherAvailable'] == true &&
        proof['correctKeyRead'] == true &&
        proof['wrongKeyRejected'] == true &&
        proof['persistentAfterReopen'] == true &&
        proof['driftRead'] == true;
  } catch (e, stack) {
    proof['ok'] = false;
    proof['error'] = '$e';
    proof['stack'] = stack.toString().split('\n').take(5).join('\n');
  }
  _publish(proof);
}
