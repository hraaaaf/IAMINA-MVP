// Dedicated Web Worker, real SQLite3MC WASM+IndexedDB (synthetic only).
// THIS IS NOT A PATIENT WORKER: uses fixed public testing key, deliberately
// not reachable from AppDatabase.forPatientVault or app patient routes.
// ignore: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;

import 'package:sqlite3/wasm.dart';

const _canary = 'D1_WORKER_SYNTHETIC_CANARY_20261112';
const _correct = 'D1_FAKE_ONLY_NOT_PATIENT_KEY_20261112';
const _wrong = 'D1_WRONG_ONLY_NOT_PATIENT_KEY_20261112';
const _plain = 'd1_synthetic_real_worker_plain_20261112';
const _cipher = 'd1_synthetic_real_worker_cipher_20261112';

Future<String> _phase(String raw) async {
  String phase = '';
  try {
    final json = jsonDecode(raw);
    if (json is! Map<String, dynamic> || json['phase'] is! String) {
      return 'FAIL_BAD_REQUEST';
    }
    phase = json['phase'] as String;
  } catch (_) {
    return 'FAIL_BAD_REQUEST';
  }
  final supported = {
    'seed_plain', 'seed_cipher', 'verify_cipher', 'wrong_key', 'no_key',
  };
  if (!supported.contains(phase)) return 'FAIL_PHASE';
  IndexedDbFileSystem? storage;
  var stage = 'IDB';
  try {
    storage = await IndexedDbFileSystem.open(
      dbName: phase == 'seed_plain' ? _plain : _cipher,
      writeAutomatically: false,
    );
    stage = 'WASM';
    final sqlite = await WasmSqlite3.loadFromUrlString('sqlite3mc.wasm');
    stage = 'VFS';
    sqlite.registerVirtualFileSystem(storage);
    stage = 'OPEN';
    final db = sqlite.open('/database',
      vfs: 'multipleciphers-${storage.name}');
    try {
      stage = 'KEY';
      if (phase != 'seed_plain' && phase != 'no_key') {
        // Only a literal public canary key; not a clinical key API.
        final key = phase == 'wrong_key' ? _wrong : _correct;
        db.execute("PRAGMA key = '${key.replaceAll("'", "''")}'");
      }
      stage = 'CIPHER';
      if (db.select('PRAGMA cipher').isEmpty) {
        return 'FAIL_MISSING_CIPHER';
      }
      stage = 'SQL';
      if (phase == 'wrong_key' || phase == 'no_key') {
        var rejected = false;
        try {
          db.select('SELECT canary FROM d1_worker_canaries');
        } catch (_) {
          rejected = true;
        }
        if (!rejected) return 'FAIL_KEY_ACCEPTED';
      } else if (phase == 'seed_plain' || phase == 'seed_cipher') {
        db.execute('CREATE TABLE IF NOT EXISTS d1_worker_canaries (canary TEXT NOT NULL)');
        db.execute('DELETE FROM d1_worker_canaries');
        db.execute('INSERT INTO d1_worker_canaries(canary) VALUES (?)', [_canary]);
      } else {
        final rows = db.select('SELECT canary FROM d1_worker_canaries');
        if (rows.length != 1 || rows.single['canary'] != _canary) {
          return 'FAIL_REOPEN_MISMATCH';
        }
      }
    } finally {
      db.close();
    }
    stage = 'FLUSH';
    await storage.flush();
    stage = 'CLOSE';
    await storage.close();
    storage = null;
    return 'PASS_${phase.toUpperCase()}';
  } catch (_) {
    // No SQL, key material or cleartext errors in outbound messages.
    return 'FAIL_$stage';
  } finally {
    try { await storage?.close(); } catch (_) { /* deny on error */ }
  }
}

void main() {
  final worker = html.DedicatedWorkerGlobalScope.instance;
  var busy = false;
  worker.onMessage.listen((event) {
    if (busy) {
      worker.postMessage('FAIL_BUSY');
      return;
    }
    busy = true;
    unawaited(_phase(event.data as String).then(
      worker.postMessage,
      onError: (Object _) => worker.postMessage('FAIL_UNHANDLED'),
    ).whenComplete(() => busy = false));
  });
}
