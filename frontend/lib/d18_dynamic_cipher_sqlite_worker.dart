// D18 CI-ONLY: per-opening dynamic sqlite3mc password through a dedicated worker.
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

const _namespace = r'^amina_vault_v1_device_[0-9a-f]{32}_d18_ci_dynamic$';
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
  var stage = 'validate_input';
  try {
    final payload = event.data as JSObject;
    final kind = (payload.getProperty('type'.toJS) as JSString).toDart;
    final name = (payload.getProperty('name'.toJS) as JSString).toDart;
    if (kind != 'D18_CI_DYNAMIC_SQL_OPEN' ||
        !RegExp(_namespace).hasMatch(name)) {
      reject(); return;
    }
    final keyBuffer = payload.getProperty('key'.toJS) as JSArrayBuffer;
    final bytes = keyBuffer.toDart.asUint8List();
    if (bytes.length != 32) { reject(); return; }

    // Hex encodes the per-opening random 32-byte test secret for sqlite3mc
    // PRAGMA key's password interface. This is NOT direct raw-DEK mode.
    final secret = _hex(bytes);
    bytes.fillRange(0, bytes.length, 0);

    stage = 'open_indexeddb';
    storage = await IndexedDbFileSystem.open(dbName: name);
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
    // Must authenticate the keyed database BEFORE exporting SQL port.
    stage = 'ensure_open';
    await db.ensureOpen(const _SyntheticNoMigrations());
    stage = 'validate_encrypted_schema';
    await db.runSelect('SELECT count(*) FROM sqlite_master', const []);
    stage = 'create_drift_server';
    final server = DriftServer(db, closeConnectionAfterShutdown: true);
    control.postMessage('READY'.toJS);
    control.close();
    await server.serve(databasePort.channel(explicitClose: true));
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
    control.postMessage(response.toJS);
    control.close();
    databasePort.close();
    await storage?.close();
  }
}

void main() {
  final self = globalContext as web.DedicatedWorkerGlobalScope;
  web.EventStreamProviders.messageEvent.forTarget(self).listen((event) {
    unawaited(_serve(event));
  });
}
