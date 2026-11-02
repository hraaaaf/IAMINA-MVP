// D18 synthetic only: dynamic per-vault secret and SQLite in a dedicated worker.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use, experimental_member_use
import 'dart:html' as html;
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';
import 'package:drift/drift.dart' show Migrator;
import 'package:drift/remote.dart';
import 'package:drift/wasm.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';
import 'data/drift/d18_keyed_open_guard.dart';
import 'data/drift/d18_vault_key_policy.dart';

const _patientA = 'e2dbe28f-3eea-4410-86a7-274150a00018';
const _patientB = 'e2dbe28f-3eea-4410-86a7-274150b00018';
const _table = 'd18_ci_real_keyed_worker';
const _marker = 'D18_CI_DYNAMIC_REAL_SQLITE_WORKER_20261102';
const _tableB = 'd18_ci_second_vault';
const _markerB = 'D18_CI_SYNTHETIC_SECOND_VAULT_20261102';

void stage(String value) =>
    html.document.documentElement?.dataset['d18DynamicStage'] = value;

void verify(bool ok, String code) {
  if (!ok) throw StateError(code);
}

// LOT 2/3 PRE-CUTOVER: real sqlite3mc worker + real D18VaultKeyPolicy
// + scope/epoch guard + real AppDatabase v12 schema; disposable C ONLY.
// This is not a clinical connector, never switch forPatientVault to this POC.
const _guardedC = 'e2dbe28f-3eea-4410-86a7-274150c00018';

final class _GuardedSqlCandidate {
  final web.Worker worker;
  final web.MessagePort control, sql;
  final AppDatabase database;
  const _GuardedSqlCandidate(this.worker,this.control,this.sql,this.database);
  Future<void> close() async {
    try {await database.close();}
    finally {
      control.close();
      sql.close();
      worker.terminate();
    }
  }
}

Future<void> verifyGuardedWebOpen() async {
  stage('guarded_policy_enroll');
  final scope=PatientVaultScope.deviceLocal(_guardedC);
  final enrolled=await D18VaultKeyPolicy.createForEmptyVault(
    scope:scope,passphrase:'D18-CI-only-synthetic-2026-verified-policy');
  try {
    final guard=D18KeyedOpenGuard(
      resolveAuthenticatedScope:() async => scope,
      readAuthEpoch:()=>1);
    stage('guarded_cross_patient_reject');
    final wrong=PatientVaultScope.deviceLocal(_patientB);
    var invoked=false;
    try {
      await guard.openUnpublished<_GuardedSqlCandidate>(
        requestedScope:wrong,
        keySession:enrolled.session,
        createUnpublished:(key) async {
          invoked=true;
          throw StateError('MUST_NOT_ENTER_WORKER');
        },
        discardUnpublished:(v)=>v.close());
      throw StateError('D18_GUARD_CROSS_SCOPE_ACCEPTED');
    } catch(e) {
      verify(!invoked && e is StateError,
        'D18_GUARD_OPENED_WRONG_PATIENT');
    }
    stage('guarded_real_worker_open');
    final candidate=await guard.openUnpublished<_GuardedSqlCandidate>(
      requestedScope:scope,
      keySession:enrolled.session,
      createUnpublished:(bytes) async {
        final worker=web.Worker('d18_dynamic_cipher_sqlite_worker.js'.toJS);
        final control=web.MessageChannel(),sql=web.MessageChannel();
        var transferred=false;
        try {
          final own=Uint8List.fromList(bytes);
          final buffer=own.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
          final packet=JSObject()
            ..setProperty('type'.toJS,'D18_CI_DYNAMIC_SQL_OPEN'.toJS)
            ..setProperty('name'.toJS,(scope.databaseName+'_d18_ci_dynamic').toJS)
            ..setProperty('key'.toJS,buffer);
          final response=web.EventStreamProviders.messageEvent
            .forTarget(control.port1).first.timeout(const Duration(seconds:25));
          control.port1.start();
          worker.postMessage(packet,<JSObject>[control.port2,sql.port2,buffer].toJS);
          transferred=true;
          own.fillRange(0,own.length,0);
          final status=((await response).data as JSString).toDart;
          verify(status=='READY','D18_GUARDED_WORKER_NOT_READY');
          final conn=await connectToRemoteAndInitialize(
            sql.port1.channel(explicitClose:true));
          final database=AppDatabase.testPatientVault(conn,scope);
          try {
            // Drift may have already bootstrapped the real v12 schema when
            // AppDatabase opened the remote connection. Never re-run onCreate
            // or overwrite an existing encrypted database in that case.
            // If the pre-opened CI worker instead left an EMPTY v1 store,
            // create the real schema inside a transaction and verify it.
            stage('guarded_v12_read_initial_version');
            final initialRows=await database.customSelect('PRAGMA user_version').get();
            if (initialRows.length!=1) {
              stage('guarded_v12_initial_version_no_row');
              throw StateError('D18_GUARDED_INITIAL_VERSION_UNAVAILABLE');
            }
            final rawVersion=initialRows.single.data['user_version'];
            if (rawVersion is! int) {
              stage('guarded_v12_initial_version_invalid_type');
              throw StateError('D18_GUARDED_INITIAL_VERSION_INVALID');
            }
            // enableMigrations:false on the CI worker leaves a brand-new
            // sqlite3mc database at PRAGMA user_version=0, not necessarily 1.
            // Both 0 and 1 are allowed ONLY with no user tables; v12 must
            // already have the complete real Drift schema. Never overwrite.
            stage(rawVersion==12 ? 'guarded_v12_auto_initialized' :
              rawVersion==0 ? 'guarded_v12_fresh_version_zero' :
              rawVersion==1 ? 'guarded_v12_worker_version_one' :
              'guarded_v12_unexpected_initial_version');
            verify(rawVersion==0||rawVersion==1||rawVersion==12,
                'D18_GUARDED_UNEXPECTED_INITIAL_VERSION');
            final existing=await database.customSelect(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'").get();
            if (rawVersion==0||rawVersion==1) {
              stage('guarded_v12_check_empty');
              verify(existing.isEmpty,'D18_GUARDED_NONEMPTY_CIPHER_DB');
              stage('guarded_v12_begin_transaction');
              await database.transaction(() async {
                stage('guarded_v12_create_all');
                await database.migration.onCreate(Migrator(database));
                stage('guarded_v12_set_user_version');
                await database.customStatement('PRAGMA user_version=12');
                stage('guarded_v12_integrity_check');
                final check=await database.customSelect(
                    'PRAGMA integrity_check').getSingle();
                verify(check.data.values.single=='ok',
                    'D18_GUARDED_MIGRATION_INTEGRITY_FAILED');
                stage('guarded_v12_foreign_key_check');
                final fks=await database.customSelect(
                    'PRAGMA foreign_key_check').get();
                verify(fks.isEmpty,'D18_GUARDED_MIGRATION_FK_FAILED');
              });
              stage('guarded_v12_migration_committed');
            } else {
              stage('guarded_v12_verify_existing_schema');
              final tableNames=existing.map((r)=>r.read<String>('name')).toSet();
              verify(tableNames.containsAll(const {
                'patient_profiles','log_entries','chat_messages',
                'medication_events','reminders',
                'patient_treatment_declarations_v1',
              }), 'D18_GUARDED_V12_TABLES_MISSING');
            }
          } catch(_) {
            await database.close();
            rethrow;
          }
          return _GuardedSqlCandidate(worker,control.port1,sql.port1,database);
        } catch(_) {
          control.port1.close();
          sql.port1.close();
          worker.terminate();
          rethrow;
        } finally {
          verify(transferred,'D18_GUARDED_WORKER_KEY_NOT_TRANSFERRED');
        }
      },
      discardUnpublished:(c)=>c.close());
    try {
      stage('guarded_schema_version');
      final version=await candidate.database.customSelect('PRAGMA user_version')
        .getSingle();
      verify(version.read<int>('user_version')==12,
        'D18_GUARDED_REAL_DRIFT_SCHEMA_NOT_V12');
      final rows=await candidate.database.customSelect(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='patient_profiles'").get();
      verify(rows.length==1,'D18_GUARDED_PATIENT_TABLE_MISSING');
      final declaration=await candidate.database.customSelect(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='patient_treatment_declarations_v1'").get();
      verify(declaration.length==1,'D18_GUARDED_DECLARATION_TABLE_MISSING');
      stage('guarded_session_key_preserved');
      verify(!enrolled.session.isLocked,'D18_GUARDED_SESSION_KEY_LOST');
    } finally {await candidate.close();}
  } finally {enrolled.session.lock();}
}

Future<void> runPhase(String name) async {
  if(name=='guarded_open') {await verifyGuardedWebOpen();return;}
  stage('resolve_scope');
  final scope = PatientVaultScope.deviceLocal(
    const {'isolate_b', 'create_b', 'read_b'}.contains(name)
        ? _patientB : _patientA,
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

  stage('create_worker');
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
    // The control port uses addEventListener via EventStreamProviders.
    // It will NOT dispatch messages until MessagePort.start() is called.
    // Subscribe before posting to avoid losing an immediate worker response.
    final readyEvent = web.EventStreamProviders.messageEvent
        .forTarget(control.port1)
        .first.timeout(const Duration(seconds: 25));
    control.port1.start();
    stage('send_worker_open');
    worker.postMessage(message,
        <JSObject>[control.port2, sql.port2, keyArrayBuffer].toJS);
    ephemeral.fillRange(0, ephemeral.length, 0);
    stage('await_worker_ready');
    final statusEvent = await readyEvent;
    final status = (statusEvent.data as JSString).toDart;
    control.port1.close();
    if (name == 'wrong_key') {
      verify(status == 'KEY_REJECTED', 'D18_DYNAMIC_BAD_KEY_ACCEPTED');
      return;
    }
    if (name == 'lock_denied') {
      verify(status == 'LOCK_UNAVAILABLE', 'D18_DYNAMIC_SAME_VAULT_LOCK_BYPASS');
      return;
    }
    stage('worker_ack_' + status);
    verify(status == 'READY', 'D18_DYNAMIC_OPEN_REJECTED');
    final connection = await connectToRemoteAndInitialize(
      sql.port1.channel(explicitClose: true),
    );
    stage('remote_connected');
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
    } else if (name == 'create_b') {
      await database.customStatement(
          'CREATE TABLE "$_tableB" (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)');
      await database.customStatement(
          'INSERT INTO "$_tableB" (id, marker) VALUES (?, ?)', [1, _markerB]);
    } else if (name == 'read_b') {
      final row = await database.customSelect(
          'SELECT marker FROM "$_tableB" WHERE id = 1').getSingle();
      verify(row.read<String>('marker') == _markerB,
          'D18_DYNAMIC_B_RESTART_LOST');
      final rows = await database.customSelect(
          "SELECT name FROM sqlite_master WHERE name = '$_table'").get();
      verify(rows.isEmpty, 'D18_DYNAMIC_B_SAW_A');
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
  stage('main_entered');
  WidgetsFlutterBinding.ensureInitialized();
  final name = Uri.base.queryParameters['phase'] ?? '';
  try {
    verify(const {
      'create', 'read', 'wrong_key', 'isolate_b', 'physical_bytes',
      'lock_denied', 'create_b', 'read_b', 'guarded_open',
    }.contains(name), 'D18_DYNAMIC_INVALID_PHASE');
    stage('run_phase');
    await runPhase(name);
    html.document.title = 'D18_DYNAMIC_SQL_PASS:$name';
  } catch (e) {
    html.document.documentElement?.dataset['d18DynamicError'] =
        e.runtimeType.toString();
    html.document.title = 'D18_DYNAMIC_SQL_FAIL:$name';
  }
  runApp(const SizedBox.shrink());
}
