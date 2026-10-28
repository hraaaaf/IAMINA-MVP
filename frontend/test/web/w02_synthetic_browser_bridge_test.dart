import 'dart:typed_data';

import 'package:amina/data/drift/w02_web_memory_sqlite_candidate.dart';
import 'package:amina/data/drift/w02_synthetic_browser_bridge.dart';
import 'package:drift/drift.dart'
    show OpeningDetails, QueryExecutor, QueryExecutorUser;
import 'package:flutter_test/flutter_test.dart';

final class _W02SyntheticSchema extends QueryExecutorUser {
  @override
  int get schemaVersion => 1;

  @override
  Future<void> beforeOpen(QueryExecutor executor, OpeningDetails details) async {}
}

Uri _asset(String name) => Uri.parse('http://127.0.0.1:7399/$name');

void main() {
  test('Chrome Dart -> JS AES-GCM IndexedDB CAS -> Dart SQLite WASM round trip', () async {
    final bridge = await W02SyntheticBrowserBridge.load(
      _asset('iamina_w02_browser_bridge_probe.mjs'),
    );
    final slot = bridge.newSyntheticSlot();
    final secret = bridge.newSyntheticSecret();
    const vaultId = 'amina_vault_v1_native_734';
    final original = await bridge.open(
      vaultId: vaultId,
      slot: slot,
      secret: secret,
      revisionFloor: 0,
      allowSyntheticEmpty: true,
    );
    W02WebMemorySqliteCandidate? memory;
    Uint8List? exported;
    try {
      expect(original.revision, 0);
      memory = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: original.takeAuthenticatedSnapshot(),
        sqlite3Wasm: _asset('sqlite3.wasm'),
      );
      expect(await memory.executor.ensureOpen(_W02SyntheticSchema()), isTrue);
      await memory.executor.runCustom(
        'CREATE TABLE test_bridge (note TEXT NOT NULL)', [],
      );
      await memory.executor.runInsert(
        'INSERT INTO test_bridge(note) VALUES (?)',
        ['W02_BROWSER_DART_JS_REAL_SQLITE_734'],
      );
      exported = memory.exportSnapshot();
      expect(await original.commit(exported), 1);
    } finally {
      exported?.fillRange(0, exported.length, 0);
      await memory?.close();
      original.close();
    }

    final restored = await bridge.open(
      vaultId: vaultId,
      slot: slot,
      secret: secret,
      revisionFloor: 1,
      allowSyntheticEmpty: false,
    );
    W02WebMemorySqliteCandidate? reopened;
    Uint8List? snapshot;
    try {
      expect(restored.revision, 1);
      snapshot = restored.takeAuthenticatedSnapshot();
      expect(snapshot, isNotNull);
      reopened = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: snapshot,
        sqlite3Wasm: _asset('sqlite3.wasm'),
      );
      expect(await reopened.executor.ensureOpen(_W02SyntheticSchema()), isTrue);
      final rows = await reopened.executor.runSelect(
        'SELECT note FROM test_bridge', [],
      );
      expect(rows.single['note'], 'W02_BROWSER_DART_JS_REAL_SQLITE_734');
    } finally {
      snapshot?.fillRange(0, snapshot.length, 0);
      await reopened?.close();
      restored.close();
    }

    await expectLater(
      bridge.open(
        vaultId: vaultId,
        slot: slot,
        secret: bridge.newSyntheticSecret(),
        revisionFloor: 1,
        allowSyntheticEmpty: false,
      ),
      throwsA(isA<Object>()),
    );
    await expectLater(
      bridge.open(
        vaultId: 'amina_vault_v1_native_812',
        slot: slot,
        secret: secret,
        revisionFloor: 1,
        allowSyntheticEmpty: false,
      ),
      throwsA(isA<Object>()),
    );
    await expectLater(
      bridge.open(
        vaultId: vaultId,
        slot: slot,
        secret: secret,
        revisionFloor: 2,
        allowSyntheticEmpty: false,
      ),
      throwsA(isA<Object>()),
    );
  });
  test('test-only browser module refuses non-loopback JS sources', () async {
    await expectLater(
      W02SyntheticBrowserBridge.load(
        Uri.parse('https://example.com/iamina_w02_browser_bridge_probe.mjs'),
      ),
      throwsStateError,
    );
  });
}
