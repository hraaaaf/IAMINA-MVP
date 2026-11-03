// D18 PRE-CUTOVER encrypted Web worker candidate. No clinical runtime activation.
// No patient runtime use, no production namespace, no release artifacts.
// ignore_for_file: experimental_member_use
// Requires pinned Drift and sqlite3mc WASM; custom transport uses pinned Drift
// implementation adapter and MUST be reviewed before clinical integration.
import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'package:drift/drift.dart';
import 'package:drift/remote.dart';
import 'package:drift/wasm.dart';
import 'package:drift/src/web/channel_new.dart';
import 'package:sqlite3/wasm.dart';
import 'package:web/web.dart' as web;

const _namespace = r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})_d18_cipher_v1$';
const _scope = r'^amina_vault_v1_(native_[1-9][0-9]*|device_[0-9a-f]{32})$';
bool _used = false;

// Open the raw Drift QueryExecutor before querying it. Never invoke direct
// runSelect on an unopened executor. This POC intentionally runs no schema
// migrations and has no clinical tables or automatic patient cutover.
final class _SyntheticNoMigrations implements QueryExecutorUser {
  const _SyntheticNoMigrations();

  @override
  int get schemaVersion => 1;

  @override
  Future<void> beforeOpen(QueryExecutor executor, OpeningDetails details) async {}
}

String _hex(List<int> bytes) =>
    bytes.map((value) => value.toRadixString(16).padLeft(2, '0')).join();

Future<void> _serve(web.MessageEvent event) async {
  final ports = event.ports.toDart;
  if (ports.length != 2) return;
  final control = ports[0], databasePort = ports[1];
  void reject() {
    control.postMessage('REJECTED'.toJS);
    control.close();
    databasePort.close();
  }
  if (_used) { reject(); return; }
  _used = true;

  IndexedDbFileSystem? storage;
  WasmDatabase? database;
  DriftServer? server;
  JSObject? lockLease;
  var acknowledged = false;
  var stage = 'validate_input';
  try {
    final payload = event.data as JSObject;
    final kind = (payload.getProperty('type'.toJS) as JSString).toDart;
    final name = (payload.getProperty('name'.toJS) as JSString).toDart;
    final scope = (payload.getProperty('scope'.toJS) as JSString).toDart;
    // Mandatory intent and physical inspection under Web Lock. Historically tested phases still
    // use D18_CI_DYNAMIC_SQL_OPEN without intent (same behavior). The new
    // INTENT variant is scoped to disposable synthetic namespaces and MUST
    // inspect the VFS under the Web Lock before sqlite3 opens a DB file.
    final intentMode = kind == 'D18_UNPUBLISHED_KEYED_OPEN';
    if (!intentMode || !RegExp(_namespace).hasMatch(name) ||
        !RegExp(_scope).hasMatch(scope) ||
        name != scope + '_d18_cipher_v1') {
      reject(); return;
    }
    String? intent;
    if (intentMode) {
      final rawIntent = payload.getProperty('intent'.toJS);
      if (rawIntent is! JSString) { reject(); return; }
      intent = rawIntent.toDart;
      if (intent != 'createFresh' && intent != 'reopenExisting') {
        reject(); return;
      }
    }
    final keyBuffer = payload.getProperty('key'.toJS) as JSArrayBuffer;
    final bytes = keyBuffer.toDart.asUint8List();
    if (bytes.length != 32) { reject(); return; }

    // Hex encodes the per-opening random 32-byte test secret for sqlite3mc
    // PRAGMA key's password interface. This is NOT direct raw-DEK mode.
    final secret = _hex(bytes);
    bytes.fillRange(0, bytes.length, 0);

    // Acquire an exclusive origin-wide lease BEFORE opening the physical DB.
    // Missing Web Locks, an occupied namespace, or missing CI helper fail closed.
    stage = 'load_lock_gate';
    globalContext.callMethod('importScripts'.toJS,
        'd18_unpublished_worker_lock_gate.js'.toJS);
    stage = 'acquire_lock';
    final acquired = await globalContext
        .callMethod<JSPromise<JSObject>>('__d18AcquireUnpublishedLock'.toJS,
            name.toJS)
        .toDart;
    if (!(acquired.getProperty('ok'.toJS) as JSBoolean).toDart) {
      control.postMessage('LOCK_UNAVAILABLE'.toJS);
      control.close();
      databasePort.close();
      return;
    }
    lockLease = acquired;

    stage = 'open_indexeddb';
    storage = await IndexedDbFileSystem.open(dbName: name);
    if (intentMode) {
      // xAccess checks the physical SQLite FILE, not merely the IndexedDB
      // namespace (which IndexedDbFileSystem.open may create on first use).
      // 1 means file exists; 0 means absent. Never call sqlite3.open before
      // rejecting an inconsistent intent, or a missing ciphertext can be
      // silently replaced with an empty database.
      stage = 'inspect_ciphertext_before_open';
      final physicalExists = storage.xAccess('/database', 0) != 0;
      if (intent == 'reopenExisting' && !physicalExists) {
        control.postMessage('MISSING_CIPHERTEXT'.toJS);
        control.close();
        databasePort.close();
        return;
      }
      if (intent == 'createFresh' && physicalExists) {
        control.postMessage('CIPHERTEXT_ALREADY_EXISTS'.toJS);
        control.close();
        databasePort.close();
        return;
      }
    }
    stage = 'load_sqlite3mc';
    final sqlite3 = await WasmSqlite3.loadFromUrl(
      Uri.parse('d18_sqlite3mc.wasm'),
    );
    stage = 'register_vfs';
    sqlite3.registerVirtualFileSystem(storage, makeDefault: true);
    stage = 'construct_wasm_database';
    final db = WasmDatabase(
      sqlite3: sqlite3,
      path: '/database',
      fileSystem: storage,
      enableMigrations: false,
      setup: (raw) {
        final cipher = raw.select('PRAGMA cipher');
        if (cipher.length != 1 ||
            cipher.first.values.first is! String) {
          throw StateError('D18_CI_DYNAMIC_CIPHER_MISSING');
        }
        raw.execute("PRAGMA key = '$secret'");
        // This query distinguishes a wrong key from a successful lazy open.
        raw.select('SELECT count(*) FROM sqlite_master');
      },
    );
    database = db;
    // Must authenticate the keyed database BEFORE exporting SQL port.
    stage = 'ensure_open';
    await db.ensureOpen(const _SyntheticNoMigrations());
    stage = 'validate_encrypted_schema';
    await db.runSelect('SELECT count(*) FROM sqlite_master', const []);
    if (intent == 'reopenExisting') {
      final version = await db.runSelect('PRAGMA user_version', const []);
      if (version.length != 1 || version.single['user_version'] != 12) {
        throw StateError('D18_CIPHERTEXT_SCHEMA_VERSION_REJECTED');
      }
    }
    stage = 'create_drift_server';
    final liveServer = DriftServer(db, closeConnectionAfterShutdown: true);
    server = liveServer;
    control.postMessage((intent == 'createFresh'
        ? 'READY_FRESH' : 'READY_EXISTING_AUTHENTICATED').toJS);
    acknowledged = true;
    control.close();
    await liveServer.serve(databasePort.channel(explicitClose: true));
  } catch (error) {
    // Only a SQLite encrypted-page rejection can count as wrong key.
    // All other failures must remain generic; no secrets in responses.
    final reason = error.toString();
    final notADatabase = reason.contains('SQLITE_NOTADB') ||
        reason.contains('sqlite3 result code 26') ||
        reason.contains('file is not a database');
    // A finite test-only stage and exception type, never error.toString or keys.
    final response = notADatabase
        ? 'KEY_REJECTED'
        : 'REJECTED_${stage}_${error.runtimeType}';
    if (!acknowledged) {
      control.postMessage(response.toJS);
      control.close();
      databasePort.close();
    }
  } finally {
    // Keep the exclusive Web Lock until Drift and IndexedDB are fully closed.
    // Nested finally guarantees lease release even when a close fails.
    try {
      if (server != null) {
        await server.shutdown();
      } else if (database != null) {
        await database.close();
      }
    } finally {
      try {
        await storage?.close();
      } finally {
        if (lockLease != null) {
          await lockLease
              .callMethod<JSPromise<JSAny?>>('release'.toJS)
              .toDart;
        }
      }
    }
  }
}

void main() {
  final self = globalContext as web.DedicatedWorkerGlobalScope;
  web.EventStreamProviders.messageEvent.forTarget(self).listen((event) {
    unawaited(_serve(event));
  });
}
