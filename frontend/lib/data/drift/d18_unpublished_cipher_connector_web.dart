// D18 PRE-CUTOVER ONLY. The clinical AppDatabase.forPatientVault is untouched.
// ignore_for_file: experimental_member_use
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';
import 'package:drift/drift.dart' show QueryExecutor, Migrator;
import 'package:drift/remote.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:web/web.dart' as web;
import 'database.dart';
import 'patient_vault_scope.dart';
import 'd18_pre_cutover_cipher_adapter.dart';

/// Connects ONLY an unpublished D18 candidate through the guarded adapter.
/// Scope and AuthEpoch must be verified by D18KeyedOpenGuard on both sides
/// of this asynchronous operation. Never import into patient-facing providers.
Future<D18KeyedCipherWorkerLease> openD18UnpublishedCipherWorker(
  PatientVaultScope scope, D18CipherVaultOpenIntent intent,
  String destination, List<int> ephemeralKey,
) async {
  final allowed = RegExp(
      r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$');
  if (!allowed.hasMatch(scope.databaseName) ||
      destination != D18PreCutoverCipherAdapter.destinationFor(scope) ||
      ephemeralKey.length != 32) {
    throw StateError('D18 worker parameters rejected');
  }
  final worker = web.Worker('d18_unpublished_cipher_worker.js'.toJS);
  final control = web.MessageChannel(), sql = web.MessageChannel();
  QueryExecutor? executor;
  var success = false;
  try {
    final localKey = Uint8List.fromList(ephemeralKey);
    final buffer = localKey.toJS.getProperty('buffer'.toJS) as JSArrayBuffer;
    final msg = JSObject()
      ..setProperty('type'.toJS, 'D18_UNPUBLISHED_KEYED_OPEN'.toJS)
      ..setProperty('scope'.toJS, scope.databaseName.toJS)
      ..setProperty('name'.toJS, destination.toJS)
      ..setProperty('intent'.toJS,
          (intent == D18CipherVaultOpenIntent.createFresh
              ? 'createFresh' : 'reopenExisting').toJS)
      ..setProperty('key'.toJS, buffer);
    final ack = web.EventStreamProviders.messageEvent.forTarget(control.port1)
        .first.timeout(const Duration(seconds:30));
    control.port1.start();
    try {
      worker.postMessage(msg,<JSObject>[control.port2,sql.port2,buffer].toJS);
    } finally {
      localKey.fillRange(0,localKey.length,0);
    }
    final response = ((await ack).data as JSString).toDart;
    final expected = intent == D18CipherVaultOpenIntent.createFresh
        ? 'READY_FRESH' : 'READY_EXISTING_AUTHENTICATED';
    if (response != expected) throw StateError('D18 encrypted worker denied');
    executor = await connectToRemoteAndInitialize(
        sql.port1.channel(explicitClose:true));
    final db = AppDatabase.testPatientVault(executor,scope);
    final version = (await db.customSelect('PRAGMA user_version')
        .getSingle()).read<int>('user_version');
    if (intent == D18CipherVaultOpenIntent.createFresh) {
      if (version == 0 || version == 1) {
        final tables = await db.customSelect(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'").get();
        if (tables.isNotEmpty) {
          throw StateError('D18 fresh ciphertext is not empty');
        }
        await db.transaction(() async {
          await db.migration.onCreate(Migrator(db));
          await db.customStatement('PRAGMA user_version=12');
        });
      } else if (version != db.schemaVersion) {
        throw StateError('D18 unexpected encrypted schema');
      }
    } else if (version != db.schemaVersion) {
      throw StateError('D18 existing encrypted schema mismatch');
    }
    success=true;
    return D18KeyedCipherWorkerLease(
      executor:executor,
      authenticatedScopeName:scope.databaseName,
      physicalDatabaseName:destination,
      cipherEngine:'sqlite3mc',
      physicalState:intent == D18CipherVaultOpenIntent.createFresh
          ? D18CipherPhysicalState.absent
          : D18CipherPhysicalState.existingAuthenticated,
      disposeWorker:() async {
        try {await executor!.close();}
        finally {
          control.port1.close();sql.port1.close();worker.terminate();
        }
      },
    );
  } finally {
    if (!success) {
      try {await executor?.close();}
      finally {
        control.port1.close();sql.port1.close();worker.terminate();
      }
    }
  }
}
