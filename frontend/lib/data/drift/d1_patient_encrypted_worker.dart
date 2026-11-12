// D1 secure-worker candidate. Not yet connected to live patient UI.
// No hard-coded key, no plain SQLite fallback, no legacy DB migration.
// ignore: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'package:drift/remote.dart';
import 'package:drift/web.dart';
import 'package:drift/wasm.dart';
import 'package:sqlite3/wasm.dart';
import 'package:web/web.dart' as web;

final _clinicalOwner = RegExp(
    r'^amina_vault_v1_(?:native_[1-9][0-9]*|device_[a-f0-9]{32})$');

Future<void> _open(web.DedicatedWorkerGlobalScope self, JSObject message) async {
  IndexedDbFileSystem? fs;
  var stage = 'DENIED';
  try {
    final owner = (message['owner'] as JSString?)?.toDart;
    final epoch = (message['epoch'] as JSNumber?)?.toDartInt;
    final supplied = message['key'] as JSUint8Array?;
    if (owner == null || !_clinicalOwner.hasMatch(owner) ||
        epoch == null || epoch < 0 || supplied == null) {
      self.postMessage('D1_DENIED'.toJS);
      return;
    }
    final key = supplied.toDart;
    if (key.length != 32 || key.every((byte) => byte == 0)) {
      key.fillRange(0, key.length, 0);
      self.postMessage('D1_DENIED'.toJS);
      return;
    }
    // Encode bytes for the SQLite3MC PRAGMA; never pass them to logs,
    // DOM, localStorage, URL query or persisted JS metadata.
    final keyHex = key.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    key.fillRange(0, key.length, 0);
    final port = message['port'] as web.MessagePort;
    stage = 'IDB';
    // Separate physical namespace; previous unencrypted patient data is
    // never implicitly assigned, imported, migrated, erased or opened here.
    fs = await IndexedDbFileSystem.open(
        dbName: 'd1_encrypted_v1_$owner', writeAutomatically: false);
    stage = 'WASM';
    final sqlite = await WasmSqlite3.loadFromUrlString('sqlite3mc.wasm');
    sqlite.registerVirtualFileSystem(fs);
    stage = 'SQLITE3MC';
    final db = sqlite.open('/database', vfs: 'multipleciphers-${fs.name}');
    try {
      stage = 'CIPHER';
      if (db.select('PRAGMA cipher').isEmpty) throw StateError('NO_CIPHER');
      stage = 'KEY';
      db.execute("PRAGMA key = '$keyHex'");
      stage = 'KEY_VERIFY';
      db.select('SELECT count(*) FROM sqlite_master');
      final executor = WasmDatabase.opened(db, closeUnderlyingOnClose: false);
      try {
        stage = 'DRIFT';
        final server = DriftServer(executor);
        self.postMessage('D1_CIPHER_READY'.toJS);
        await server.serve(port.channel(explicitClose: true));
      } finally {
        await executor.close();
      }
    } finally {
      db.close();
    }
    stage = 'FLUSH';
    await fs.flush();
    await fs.close();
    fs = null;
    self.postMessage('D1_CIPHER_FLUSHED'.toJS);
  } catch (_) {
    // Fail-closed with redacted stage. Never echo SQLite error messages
    // since a failed query may contain key or medical context.
    self.postMessage('D1_FAIL_$stage'.toJS);
  } finally {
    try { await fs?.close(); } catch (_) { /* fail-closed */ }
  }
}

void main() {
  final self = globalContext as web.DedicatedWorkerGlobalScope;
  var bound = false;
  web.EventStreamProviders.messageEvent.forTarget(self).listen((event) {
    if (bound) {
      self.postMessage('D1_DENIED_ALREADY_BOUND'.toJS);
      return;
    }
    bound = true;
    try {
      unawaited(_open(self, event.data as JSObject));
    } catch (_) {
      self.postMessage('D1_DENIED'.toJS);
    }
  });
}
