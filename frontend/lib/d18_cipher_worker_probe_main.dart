// D18 isolated, synthetic Web encryption proof: NEVER run on clinical data.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;

import 'package:drift/wasm.dart';
import 'package:flutter/widgets.dart';

import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';
import 'd18_cipher_worker_setup.dart';

const table = 'd18_mc_synthetic_probe';
const marker = 'D18_SYNTHETIC_ENCRYPTED_SENTINEL_20261102';
const patientA = 'e2dbe28f-3eea-4410-86a7-274150a00018';
const patientB = 'e2dbe28f-3eea-4410-86a7-274150b00018';

void stage(String name) =>
    html.document.documentElement?.dataset['d18CipherStage'] = name;

void verify(bool ok, String reason) {
  if (!ok) throw StateError(reason);
}


// Disposable synthetic logical migration only: NOT a full clinical schema copy.
const migrationSource = 'd18_ci_plain_source_20261102';
const migrationDestination = 'd18_ci_cipher_destination_20261102';
const migrationTable = 'd18_ci_migration_marker';
const migrationMarker = 'D18_SYNTHETIC_MIGRATION_NEVER_CLINICAL_20261102';

Future<void> migrationPhase(String phase) async {
  final scope = PatientVaultScope.deviceLocal(patientA);
  final sourcePhase = phase == 'migration_seed_plain' ||
      phase == 'migration_check_source' || phase == 'migration_copy_cipher';
  if (phase == 'migration_raw_cipher') {
    final probe = await WasmDatabase.probe(
      sqlite3Uri: Uri.parse('d18_sqlite3mc.wasm'),
      driftWorkerUri: Uri.parse('d18_cipher_worker_correct.js'),
      databaseName: migrationDestination,
    );
    final found = probe.existingDatabases.where(
      (v) => v.$2 == migrationDestination,
    ).toList();
    verify(found.length == 1, 'D18_MIG_TARGET_NOT_UNIQUE');
    final bytes = await probe.exportDatabase(found.single);
    verify(bytes != null && bytes.length >= 100, 'D18_MIG_NO_CIPHER_BYTES');
    final file = bytes!;
    verify(String.fromCharCodes(file.take(16)) != 'SQLite format 3\u0000',
        'D18_MIG_PLAINTEXT_HEADER');
    final needle = migrationMarker.codeUnits;
    for (var i = 0; i <= file.length - needle.length; i++) {
      var equal = true;
      for (var j = 0; j < needle.length; j++) {
        if (file[i + j] != needle[j]) {
          equal = false;
          break;
        }
      }
      verify(!equal, 'D18_MIG_PLAINTEXT_MARKER');
    }
    return;
  }
  final isWrongKey = phase == 'migration_wrong_key';
  final name = sourcePhase ? migrationSource : migrationDestination;
  final wasm = Uri.parse(sourcePhase ? 'sqlite3.wasm' : 'd18_sqlite3mc.wasm');
  final worker = Uri.parse(sourcePhase ? 'drift_worker.js' :
      (isWrongKey ? 'd18_cipher_worker_wrong.js' :
                    'd18_cipher_worker_correct.js'));
  if (phase == 'migration_copy_cipher') {
    final probe = await WasmDatabase.probe(
      sqlite3Uri: Uri.parse('d18_sqlite3mc.wasm'),
      driftWorkerUri: Uri.parse('d18_cipher_worker_correct.js'),
      databaseName: migrationDestination,
    );
    verify(!probe.existingDatabases.any((v) => v.$2 == migrationDestination),
        'D18_MIG_DEST_ALREADY_EXISTS');
  }
  AppDatabase? db;
  try {
    final opened = await WasmDatabase.open(
      databaseName: name, sqlite3Uri: wasm, driftWorkerUri: worker,
      moveExistingIndexedDbToOpfs: false,
      localSetup: sourcePhase ? null : (raw) =>
          d18Configure(raw, isWrongKey ? d18Wrong : d18Right),
    );
    verify(const {'sharedIndexedDb', 'opfsShared', 'opfsLocks'}
        .contains(opened.chosenImplementation.name), 'D18_MIG_UNSAFE_STORAGE');
    html.document.documentElement?.dataset['d18CipherBackend'] =
        opened.chosenImplementation.name;
    db = AppDatabase.testPatientVault(opened.resolvedExecutor, scope);
    await db.customSelect('SELECT count(*) FROM sqlite_master').getSingle();
    if (isWrongKey) throw StateError('D18_MIG_BAD_KEY_ACCEPTED');
    if (phase == 'migration_seed_plain') {
      await db.customStatement(
        'CREATE TABLE "$migrationTable" (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)',
      );
      await db.customStatement(
        'INSERT INTO "$migrationTable" (id, marker) VALUES (?, ?)',
        [1, migrationMarker],
      );
    } else if (phase == 'migration_copy_cipher') {
      final integrity = await db.customSelect('PRAGMA integrity_check').getSingle();
      verify(integrity.data.values.single == 'ok', 'D18_MIG_SOURCE_CORRUPT');
      final fks = await db.customSelect('PRAGMA foreign_key_check').get();
      verify(fks.isEmpty, 'D18_MIG_SOURCE_FK_ERROR');
      final source = await db.customSelect(
        'SELECT marker FROM "$migrationTable" WHERE id = 1',
      ).getSingle();
      verify(source.read<String>('marker') == migrationMarker,
          'D18_MIG_SOURCE_MISSING');
      await db.close(); db = null;
      final cipher = await WasmDatabase.open(
        databaseName: migrationDestination,
        sqlite3Uri: Uri.parse('d18_sqlite3mc.wasm'),
        driftWorkerUri: Uri.parse('d18_cipher_worker_correct.js'),
        moveExistingIndexedDbToOpfs: false,
        localSetup: (raw) => d18Configure(raw, d18Right),
      );
      verify(const {'sharedIndexedDb', 'opfsShared', 'opfsLocks'}
          .contains(cipher.chosenImplementation.name), 'D18_MIG_UNSAFE_TARGET');
      db = AppDatabase.testPatientVault(cipher.resolvedExecutor, scope);
      await db.transaction(() async {
        await db.customStatement(
          'CREATE TABLE "$migrationTable" (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)',
        );
        await db.customStatement(
          'INSERT INTO "$migrationTable" (id, marker) VALUES (?, ?)',
          [1, migrationMarker],
        );
      });
      final copied = await db.customSelect(
        'SELECT marker FROM "$migrationTable" WHERE id = 1',
      ).getSingle();
      verify(copied.read<String>('marker') == migrationMarker,
          'D18_MIG_TARGET_MISMATCH');
    } else if (phase == 'migration_verify_cipher' ||
               phase == 'migration_check_source') {
      final row = await db.customSelect(
        'SELECT marker FROM "$migrationTable" WHERE id = 1',
      ).getSingle();
      verify(row.read<String>('marker') == migrationMarker,
          'D18_MIG_RESTART_LOST');
    } else {
      throw StateError('D18_MIG_UNKNOWN_PHASE');
    }
  } catch (e) {
    if (db != null) { await db.close(); db = null; }
    final error = e.toString();
    if (isWrongKey && (error.contains('SQLITE_NOTADB') ||
        error.contains('sqlite3 result code 26') ||
        error.contains('file is not a database'))) return;
    rethrow;
  } finally {
    if (db != null) await db.close();
  }
}

Future<void> executePhase(String phase) async {
  final scope = PatientVaultScope.deviceLocal(
    phase == 'isolation_b' ? patientB : patientA,
  );
  final stock = phase == 'stock_reject';
  final wrong = phase == 'wrong_key';
  final oldKeyReject = phase == 'old_key_reject';
  final rotated = phase == 'read_rotated';
  final useRotatedKey = wrong || rotated;
  final wasm = Uri.parse(stock ? 'sqlite3.wasm' : 'd18_sqlite3mc.wasm');
  final worker = Uri.parse(
    useRotatedKey ? 'd18_cipher_worker_wrong.js' : 'd18_cipher_worker_correct.js',
  );
  if (phase == 'raw_bytes' || phase == 'raw_bytes_after_rotate') {
    stage('inspect_physical_encrypted_bytes');
    final probe = await WasmDatabase.probe(
      sqlite3Uri: wasm,
      driftWorkerUri: worker,
      databaseName: scope.databaseName,
    );
    final matches = probe.existingDatabases
        .where((entry) => entry.$2 == scope.databaseName).toList();
    verify(matches.length == 1, 'D18_POC_SOURCE_NOT_UNIQUE');
    final bytes = await probe.exportDatabase(matches.single);
    verify(bytes != null && bytes.length >= 100, 'D18_POC_NO_RAW_EXPORT');
    final file = bytes!;
    verify(
      String.fromCharCodes(file.take(16)) != 'SQLite format 3\u0000',
      'D18_POC_PLAINTEXT_SQLITE_HEADER',
    );
    final needle = marker.codeUnits;
    for (var i = 0; i <= file.length - needle.length; i++) {
      var found = true;
      for (var j = 0; j < needle.length; j++) {
        if (file[i + j] != needle[j]) { found = false; break; }
      }
      verify(!found, 'D18_POC_PLAINTEXT_MARKER');
    }
    return;
  }

  AppDatabase? db;
  try {
    stage('open_custom_worker_and_local_setup');
    final result = await WasmDatabase.open(
      databaseName: scope.databaseName,
      sqlite3Uri: wasm,
      driftWorkerUri: worker,
      localSetup: (raw) =>
          d18Configure(raw, useRotatedKey ? d18Wrong : d18Right),
      moveExistingIndexedDbToOpfs: false,
    );
    final backend = result.chosenImplementation.name;
    html.document.documentElement?.dataset['d18CipherBackend'] = backend;
    verify(
      const {'sharedIndexedDb', 'opfsShared', 'opfsLocks'}.contains(backend),
      'D18_POC_UNSAFE_STORAGE',
    );
    db = AppDatabase.testPatientVault(result.resolvedExecutor, scope);
    stage('query_schema_after_key');
    // Force a real SQLite schema read. A constructor/open alone can be lazy.
    await db.customSelect('SELECT count(*) AS n FROM sqlite_master').getSingle();
    if (phase == 'write') {
      await db.customStatement(
        'CREATE TABLE "$table" (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)',
      );
      await db.customStatement(
        'INSERT INTO "$table" (id, marker) VALUES (?, ?)',
        [1, marker],
      );
      final row = await db.customSelect(
        'SELECT marker FROM "$table" WHERE id = 1',
      ).getSingle();
      verify(row.read<String>('marker') == marker, 'D18_POC_WRITE_LOST');
    } else if (phase == 'read' || rotated) {
      final row = await db.customSelect(
        'SELECT marker FROM "$table" WHERE id = 1',
      ).getSingle();
      verify(row.read<String>('marker') == marker, 'D18_POC_RESTART_LOST');
    } else if (phase == 'rotate') {
      // Synthetic-only in-place SQLite encryption-key rotation.
      // The original physical ciphertext must remain unreadable by old key.
      await db.customStatement("PRAGMA rekey = '$d18Wrong'");
      final row = await db.customSelect(
        'SELECT marker FROM "$table" WHERE id = 1',
      ).getSingle();
      verify(row.read<String>('marker') == marker, 'D18_POC_REKEY_LOST');
    } else if (phase == 'isolation_b') {
      final rows = await db.customSelect(
        "SELECT name FROM sqlite_master WHERE name = 'd18_mc_synthetic_probe'",
      ).get();
      verify(rows.isEmpty, 'D18_POC_CROSS_PATIENT_LEAK');
    } else if (stock || wrong || oldKeyReject) {
      throw StateError('D18_POC_UNSAFE_OPEN_ACCEPTED');
    } else {
      throw StateError('D18_POC_UNKNOWN_PHASE');
    }
  } catch (e) {
    if (db != null) { await db.close(); db = null; }
    final error = e.toString();
    if (stock && error.contains('D18_POC_CIPHER_UNAVAILABLE')) return;
    // Do not treat arbitrary worker, network, or SQL failures as wrong-key proof.
    // Only an actual SQLite encrypted-page read rejection is acceptable.
    final isSqliteNotADatabase = error.contains('SQLITE_NOTADB') ||
        error.contains('sqlite3 result code 26') ||
        error.contains('file is not a database');
    if ((wrong || oldKeyReject) && isSqliteNotADatabase) return;
    rethrow;
  } finally {
    if (db != null) await db.close();
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final phase = Uri.base.queryParameters['phase'] ?? '';
  try {
    verify(const {
      'stock_reject', 'write', 'wrong_key',
      'read', 'isolation_b', 'raw_bytes', 'rotate',
      'old_key_reject', 'read_rotated', 'raw_bytes_after_rotate',
      'migration_seed_plain', 'migration_copy_cipher',
      'migration_wrong_key', 'migration_verify_cipher',
      'migration_check_source', 'migration_raw_cipher',
    }.contains(phase), 'D18_POC_BAD_PHASE');
    if (phase.startsWith('migration_')) {
      await migrationPhase(phase);
    } else {
      await executePhase(phase);
    }
    html.document.title = 'D18_CIPHER_PASS:$phase';
  } catch (e) {
    // Never expose keys, patient content, decrypted bytes or stack traces.
    html.document.documentElement?.dataset['d18CipherError'] =
        e.runtimeType.toString();
    html.document.title = 'D18_CIPHER_FAIL:$phase';
  }
  runApp(const SizedBox.shrink());
}
