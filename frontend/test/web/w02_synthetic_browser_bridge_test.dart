import 'dart:convert';
import 'dart:typed_data';

import 'package:amina/data/drift/w02_native_revision_client.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

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

final class _SyntheticNativeOwner implements W02NativePrincipalSource {
  int currentEpoch = 1;
  int? userId = 734;
  bool verified = true;

  @override
  int get epoch => currentEpoch;

  @override
  int? get nativeAccountId => userId;

  @override
  bool get remoteCredentialVerified => verified;

  @override
  bool get isAudit => false;

  @override
  Future<String?> readBearer() async => 'iamina.test:0:abcdefgh';

  @override
  Future<String?> readVaultNamespace() async =>
      'amina_vault_v1_native_$userId';
}

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
  test('D10 Option A: Chrome native-auth BFF mock + AES-GCM IDB + real Drift SQLite',
      () async {
    const vaultId = 'amina_vault_v1_native_734';
    final owner = _SyntheticNativeOwner();
    final bridge = await W02SyntheticBrowserBridge.load(
      _asset('iamina_w02_browser_bridge_probe.mjs'),
    );
    final storedSlot = bridge.newSyntheticSlot();
    final secret = bridge.newSyntheticSecret();
    int committed = 0;
    String currentHash = '';
    String? pendingTicket;
    int? pendingRevision;
    final apiHttp = MockClient((request) async {
      expect(request.headers.containsKey('cookie'), isFalse);
      expect(request.headers['authorization'], 'Bearer iamina.test:0:abcdefgh');
      expect(request.url.host, 'test-only.invalid');
      expect(request.url.path.startsWith('/api/v1/w02/vault-revision/'), isTrue);
      final path = request.url.path;
      if (path.endsWith('/state') && request.method == 'GET') {
        return http.Response(jsonEncode({
          'vault_id': vaultId,
          'status': pendingRevision != null
              ? 'pending' : committed == 0 ? 'uninitialized' : 'ready',
          'slot': committed == 0 && pendingRevision == null
              ? null : storedSlot,
          'committed_revision': committed,
          'committed_envelope_sha256': currentHash,
          'pending_revision': pendingRevision,
          'pending_ticket': pendingTicket,
        }), 200, headers: {'content-type':'application/json'});
      }
      final data = jsonDecode(request.body) as Map<String, dynamic>;
      if (path.endsWith('/reserve') && request.method == 'POST') {
        expect(data['slot'], storedSlot);
        expect(data['expected_revision'], committed);
        expect(pendingRevision, null);
        pendingRevision = committed + 1;
        pendingTicket = List.filled(43, 'T').join();
        return http.Response(jsonEncode({
          'vault_id': vaultId, 'revision': pendingRevision,
          'ticket': pendingTicket,
        }), 200, headers: {'content-type':'application/json'});
      }
      if (path.endsWith('/finalize') && request.method == 'POST') {
        expect(data['slot'], storedSlot);
        expect(data['revision'], pendingRevision);
        expect(data['ticket'], pendingTicket);
        expect(data['envelope_sha256'], isA<String>());
        expect((data['envelope_sha256'] as String).length, 64);
        committed = pendingRevision!;
        currentHash = data['envelope_sha256'] as String;
        pendingRevision = null;
        pendingTicket = null;
        return http.Response(jsonEncode({
          'vault_id': vaultId, 'status': 'ready',
          'committed_revision': committed,
          'committed_envelope_sha256': currentHash,
        }), 200, headers: {'content-type':'application/json'});
      }
      return http.Response('', 404);
    });
    final identityApi = await W02NativeRevisionClient.capture(
      identity: owner, client: apiHttp,
      origin: Uri.parse('https://test-only.invalid'), syntheticTestOnly: true,
    );
    expect((await identityApi.state())['status'], 'uninitialized');
    final browser = await bridge.open(
      vaultId: identityApi.vaultId, slot: storedSlot,
      secret: secret, revisionFloor: 0, allowSyntheticEmpty: true,
    );
    W02WebMemorySqliteCandidate? volatile;
    Uint8List? bytes;
    try {
      volatile = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: browser.takeAuthenticatedSnapshot(),
        sqlite3Wasm: _asset('sqlite3.wasm'),
      );
      expect(await volatile.executor.ensureOpen(_W02SyntheticSchema()), isTrue);
      await volatile.executor.runCustom(
        'CREATE TABLE synthetic_anchor (note TEXT NOT NULL)', [],
      );
      await volatile.executor.runInsert(
        'INSERT INTO synthetic_anchor(note) VALUES (?)',
        ['D10_OPTION_A_NATIVE_WEB_734'],
      );
      bytes = volatile.exportSnapshot();
      final ticket = await identityApi.reserve(
        slot: storedSlot, expectedRevision: 0,
      );
      expect(ticket['revision'], 1);
      expect(await browser.commit(bytes), 1);
      final digest = await browser.envelopeSha256();
      expect(digest.length, 64);
      final finalized = await identityApi.finalize(
        slot: storedSlot, revision: 1, ticket: ticket['ticket'] as String,
        envelopeSha256: digest,
      );
      expect(finalized['committed_envelope_sha256'], digest);
      final authoritative = await identityApi.state();
      expect(authoritative['status'], 'ready');
      expect(authoritative['slot'], storedSlot);
      expect(authoritative['committed_envelope_sha256'], digest);
    } finally {
      bytes?.fillRange(0, bytes.length, 0);
      await volatile?.close();
      browser.close();
    }
    final reopened = await bridge.open(
      vaultId: vaultId, slot: storedSlot, secret: secret,
      revisionFloor: 1, allowSyntheticEmpty: false,
    );
    W02WebMemorySqliteCandidate? recovered;
    Uint8List? restored;
    try {
      // Server-committed checksum must match the exact ciphertext recovered
      // from IndexedDB before allowing any synthetic SQL SELECT.
      expect(await reopened.envelopeSha256(), currentHash);
      restored = reopened.takeAuthenticatedSnapshot();
      recovered = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: restored,
        sqlite3Wasm: _asset('sqlite3.wasm'),
      );
      expect(await recovered.executor.ensureOpen(_W02SyntheticSchema()), isTrue);
      final result = await recovered.executor.runSelect(
        'SELECT note FROM synthetic_anchor', [],
      );
      expect(result.single['note'], 'D10_OPTION_A_NATIVE_WEB_734');
    } finally {
      restored?.fillRange(0, restored.length, 0);
      await recovered?.close();
      reopened.close();
    }
    owner.currentEpoch++;
    owner.userId = 812;
    await expectLater(identityApi.state(),
        throwsA(isA<W02RevisionClientException>()));
    apiHttp.close();
  });

}
