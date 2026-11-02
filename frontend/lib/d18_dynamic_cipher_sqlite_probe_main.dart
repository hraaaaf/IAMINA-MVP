// D18 synthetic only: dynamic per-vault secret and SQLite in a dedicated worker.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use, experimental_member_use
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';
import 'package:drift/remote.dart';
import 'package:drift/wasm.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';

const _patientA = 'e2dbe28f-3eea-4410-86a7-274150a00018';
const _patientB = 'e2dbe28f-3eea-4410-86a7-274150b00018';
const _table = 'd18_ci_real_keyed_worker';
const _marker = 'D18_CI_DYNAMIC_REAL_SQLITE_WORKER_20261102';

void verify(bool ok, String code) {
  if (!ok) throw StateError(code);
}

Future<void> runPhase(String name) async {
  final scope = PatientVaultScope.deviceLocal(
    name == 'isolate_b' ? _patientB : _patientA,
  );
  final dbName = scope.databaseName + '_d18_ci_dynamic';
  final jsKey = globalContext.getProperty('__D18_DYNAMIC_CI_KEY'.toJS);
  verify(jsKey is JSUint8Array, 'D18_DYNAMIC_MISSING_SYNTHETIC_KEY');
  final ephemeral = Uint8List.fromList((jsKey as JSUint8Array).toDart);
  verify(ephemeral.length == 32, 'D18_DYNAMIC_BAD_KEY_SIZE');

  if (name == 'physical_bytes') {
    final probe = await WasmDatabase.probe(
      sqlite3Uri: Uri.parse('d18_sqlite3mc.wasm'),
      driftWorkerUri: Uri.parse('d18_cipher_worker_correct.js'),
      databaseName: dbName,
    );
    final entries = probe.existingDatabases.where((e) => e.$2 == dbName).toList();
    verify(entries.length == 1, 'D18_DYNAMIC_MISSING_DB');
    final bytes = await probe.exportDatabase(entries.single);
    verify(bytes != null && bytes.length > 100, 'D18_DYNAMIC_NO_BYTES');
    final raw = bytes!;
    verify(String.fromCharCodes(raw.take(16)) != 'SQLite format 3\u0000',
        'D18_DYNAMIC_PLAINTEXT_HEADER');
    final needle = _marker.codeUnits;
    for (var i = 0; i <= raw.length - needle.length; i++) {
      var found = true;
      for (var j = 0; j < needle.length; j++) {
        if (raw[i + j] != needle[j]) {
          found = false;
          break;
        }
      }
      verify(!found, 'D18_DYNAMIC_PLAINTEXT_SENTINEL');
    }
    return;
  }

  final worker = web.Worker('d18_dynamic_cipher_sqlite_worker.js'.toJS);
  final control = web.MessageChannel();
  final sql = web.MessageChannel();
  AppDatabase? database;
  try {
    final keyArrayBuffer = ephemeral.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final message = JSObject()
      ..setProperty('type'.toJS, 'D18_CI_DYNAMIC_SQL_OPEN'.toJS)
      ..setProperty('name'.toJS, dbName.toJS)
      ..setProperty('key'.toJS, keyArrayBuffer);
    worker.postMessage(message,
        <JSObject>[control.port2, sql.port2, keyArrayBuffer].toJS);
    ephemeral.fillRange(0, ephemeral.length, 0);
    final statusEvent = await web.EventStreamProviders.messageEvent
        .forTarget(control.port1)
        .first.timeout(const Duration(seconds: 25));
    final status = (statusEvent.data as JSString).toDart;
    control.port1.close();
    if (name == 'wrong_key') {
      verify(status == 'KEY_REJECTED', 'D18_DYNAMIC_BAD_KEY_ACCEPTED');
      return;
    }
    verify(status == 'READY', 'D18_DYNAMIC_OPEN_REJECTED');
    final connection = await connectToRemoteAndInitialize(
      sql.port1.channel(explicitClose: true),
    );
    database = AppDatabase.testPatientVault(connection, scope);
    await database.customSelect('SELECT count(*) FROM sqlite_master').getSingle();
    if (name == 'create') {
      await database.customStatement(
          'CREATE TABLE "$_table" (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)');
      await database.customStatement(
          'INSERT INTO "$_table" (id, marker) VALUES (?, ?)', [1, _marker]);
    } else if (name == 'read') {
      final row = await database.customSelect(
          'SELECT marker FROM "$_table" WHERE id = 1').getSingle();
      verify(row.read<String>('marker') == _marker, 'D18_DYNAMIC_RESTART_LOST');
    } else if (name == 'isolate_b') {
      final rows = await database.customSelect(
          "SELECT name FROM sqlite_master WHERE name = '$_table'").get();
      verify(rows.isEmpty, 'D18_DYNAMIC_PATIENT_CROSSOVER');
    } else {
      throw StateError('D18_DYNAMIC_UNKNOWN_PHASE');
    }
  } finally {
    if (database != null) await database.close();
    control.port1.close();
    sql.port1.close();
    worker.terminate();
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final name = Uri.base.queryParameters['phase'] ?? '';
  try {
    verify(const {'create', 'read', 'wrong_key', 'isolate_b', 'physical_bytes'}
        .contains(name), 'D18_DYNAMIC_INVALID_PHASE');
    await runPhase(name);
    html.document.title = 'D18_DYNAMIC_SQL_PASS:$name';
  } catch (e) {
    html.document.documentElement?.dataset['d18DynamicError'] =
        e.runtimeType.toString();
    html.document.title = 'D18_DYNAMIC_SQL_FAIL:$name';
  }
  runApp(const SizedBox.shrink());
}
