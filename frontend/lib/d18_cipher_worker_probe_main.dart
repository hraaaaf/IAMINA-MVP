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

Future<void> executePhase(String phase) async {
  final scope = PatientVaultScope.deviceLocal(
    phase == 'isolation_b' ? patientB : patientA,
  );
  final stock = phase == 'stock_reject';
  final wrong = phase == 'wrong_key';
  final wasm = Uri.parse(stock ? 'sqlite3.wasm' : 'd18_sqlite3mc.wasm');
  final worker = Uri.parse(
    wrong ? 'd18_cipher_worker_wrong.js' : 'd18_cipher_worker_correct.js',
  );
  if (phase == 'raw_bytes') {
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
      localSetup: (raw) => d18Configure(raw, wrong ? d18Wrong : d18Right),
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
    } else if (phase == 'read') {
      final row = await db.customSelect(
        'SELECT marker FROM "$table" WHERE id = 1',
      ).getSingle();
      verify(row.read<String>('marker') == marker, 'D18_POC_RESTART_LOST');
    } else if (phase == 'isolation_b') {
      final rows = await db.customSelect(
        "SELECT name FROM sqlite_master WHERE name = 'd18_mc_synthetic_probe'",
      ).get();
      verify(rows.isEmpty, 'D18_POC_CROSS_PATIENT_LEAK');
    } else if (stock || wrong) {
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
    if (wrong && isSqliteNotADatabase) return;
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
      'read', 'isolation_b', 'raw_bytes',
    }.contains(phase), 'D18_POC_BAD_PHASE');
    await executePhase(phase);
    html.document.title = 'D18_CIPHER_PASS:$phase';
  } catch (e) {
    // Never expose keys, patient content, decrypted bytes or stack traces.
    html.document.documentElement?.dataset['d18CipherError'] =
        e.runtimeType.toString();
    html.document.title = 'D18_CIPHER_FAIL:$phase';
  }
  runApp(const SizedBox.shrink());
}
