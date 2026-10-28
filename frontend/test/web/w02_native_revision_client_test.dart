import 'dart:convert';

import 'package:amina/data/drift/w02_native_revision_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

final class FakePrincipal implements W02NativePrincipalSource {
  int currentEpoch = 7;
  int? account = 734;
  bool verified = true;
  bool audit = false;
  String? bearer = 'iamina.test:0:abcdefgh';
  String? scope = 'amina_vault_v1_native_734';
  Future<void> Function()? duringBearerRead;
  Future<void> Function()? duringScopeRead;

  @override
  int get epoch => currentEpoch;
  @override
  int? get nativeAccountId => account;
  @override
  bool get remoteCredentialVerified => verified;
  @override
  bool get isAudit => audit;
  @override
  Future<String?> readBearer() async {
    await duringBearerRead?.call();
    return bearer;
  }
  @override
  Future<String?> readVaultNamespace() async {
    await duringScopeRead?.call();
    return scope;
  }

  void switchToB() {
    currentEpoch++;
    account = 812;
    scope = 'amina_vault_v1_native_812';
    bearer = 'iamina.test:0:BRAVO';
  }
}

Uri get preview => Uri.parse('https://test-only.invalid');

Map<String, dynamic> answer({String vaultId = 'amina_vault_v1_native_734'}) =>
    {'vault_id': vaultId, 'status': 'uninitialized', 'slot': null,
     'committed_revision': 0, 'committed_envelope_sha256': '',
     'pending_revision': null, 'pending_ticket': null};

http.Response jsonResponse(Map<String, dynamic> body, {int status = 200}) =>
    http.Response(jsonEncode(body), status,
                  headers: {'content-type': 'application/json'});

Future<W02NativeRevisionClient> capture(
  FakePrincipal principal,
  http.Client client,
) => W02NativeRevisionClient.capture(
  identity: principal, client: client, origin: preview, syntheticTestOnly: true,
);

void main() {
  test('fresh account A accepts only BFF same-origin native bearer GET', () async {
    final owner = FakePrincipal();
    var calls = 0;
    final client = MockClient((request) async {
      calls++;
      expect(request.url.toString(),
          'https://test-only.invalid/api/v1/w02/vault-revision/state');
      expect(request.headers['authorization'], 'Bearer ${owner.bearer}');
      expect(request.headers.containsKey('cookie'), false);
      expect(request.method, 'GET');
      return jsonResponse(answer());
    });
    final binding = await capture(owner, client);
    expect(binding.vaultId, 'amina_vault_v1_native_734');
    expect((await binding.state())['status'], 'uninitialized');
    expect(calls, 1);
    client.close();
  });

  test('Flutter auth epoch switch A -> logout -> B denies stale request', () async {
    final owner = FakePrincipal();
    var requests = 0;
    final client = MockClient((request) async {
      requests++;
      return jsonResponse(answer());
    });
    final leaseA = await capture(owner, client);
    owner.switchToB();
    await expectLater(leaseA.state(),
        throwsA(isA<W02RevisionClientException>()));
    expect(requests, 0);
    final leaseB = await capture(owner, client);
    expect(leaseB.vaultId, 'amina_vault_v1_native_812');
    client.close();
  });

  test('network response after logout cannot become authorized A snapshot', () async {
    final owner = FakePrincipal();
    final client = MockClient((request) async {
      owner.switchToB();
      return jsonResponse(answer());
    });
    final lease = await capture(owner, client);
    await expectLater(lease.state(),
        throwsA(isA<W02RevisionClientException>()));
    client.close();
  });

  test('cross-tab revocation during secure-storage re-read denies capture', () async {
    final owner = FakePrincipal();
    owner.duringScopeRead = () async { owner.currentEpoch++; };
    await expectLater(capture(owner, MockClient((_) async => jsonResponse(answer()))),
        throwsA(isA<W02RevisionClientException>()));
  });

  test('revoked native identity cannot enter, even with cached token', () async {
    final owner = FakePrincipal()..verified = false;
    await expectLater(capture(owner, MockClient((_) async => jsonResponse(answer()))),
        throwsA(isA<W02RevisionClientException>()));
    owner.verified = true;
    owner.audit = true;
    await expectLater(capture(owner, MockClient((_) async => jsonResponse(answer()))),
        throwsA(isA<W02RevisionClientException>()));
  });

  test('Firebase bearer and mismatched verified vault scope fail closed', () async {
    final owner = FakePrincipal()..bearer = 'firebase.token';
    await expectLater(capture(owner, MockClient((_) async => jsonResponse(answer()))),
        throwsA(isA<W02RevisionClientException>()));
    owner.bearer = 'iamina.test:0:abcdefgh';
    owner.scope = 'amina_vault_v1_native_812';
    await expectLater(capture(owner, MockClient((_) async => jsonResponse(answer()))),
        throwsA(isA<W02RevisionClientException>()));
  });

  test('BFF forged owner field and pending transaction refuse readiness', () async {
    final owner = FakePrincipal();
    final forged = MockClient((_) async =>
        jsonResponse(answer(vaultId: 'amina_vault_v1_native_812')));
    final first = await capture(owner, forged);
    await expectLater(first.state(), throwsA(isA<W02RevisionClientException>()));
    final pending = MockClient((_) async =>
        jsonResponse({...answer(), 'status': 'pending',
            'slot': List.filled(43, 'S').join(), 'pending_revision': 1,
            'pending_ticket': List.filled(43, 'T').join()}));
    final second = await capture(owner, pending);
    final state = await second.state();
    expect(state['status'], 'pending');
    // The caller MUST block SQLite opening when pending; no ready abstraction.
  });

  test('reserve and finalize use bounded JSON with owner still current', () async {
    final owner = FakePrincipal();
    final seen = <String>[];
    final client = MockClient((request) async {
      seen.add('${request.method} ${request.url.path}');
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      if (request.url.path.endsWith('/reserve')) {
        expect(payload['expected_revision'], 0);
        return jsonResponse({
          'vault_id': 'amina_vault_v1_native_734',
          'revision': 1, 'ticket': List.filled(43, 'T').join(),
        });
      }
      expect(payload['envelope_sha256'], List.filled(64, 'a').join());
      return jsonResponse({
        'vault_id': 'amina_vault_v1_native_734',
        'status': 'ready', 'committed_revision': 1,
        'committed_envelope_sha256': List.filled(64, 'a').join(),
      });
    });
    final lease = await capture(owner, client);
    final ticket = await lease.reserve(slot: List.filled(43, 'S').join(), expectedRevision: 0);
    expect(ticket['revision'], 1);
    final ok = await lease.finalize(
        slot: List.filled(43, 'S').join(), revision: 1,
        ticket: ticket['ticket'], envelopeSha256: List.filled(64, 'a').join());
    expect(ok['status'], 'ready');
    expect(seen.length, 2);
  });

  test('production-mode HTTP or unpinned origin is rejected before any call', () async {
    final owner = FakePrincipal();
    final client = MockClient((_) async => throw StateError('should not run'));
    await expectLater(
      W02NativeRevisionClient.capture(identity: owner, client: client,
          origin: Uri.parse('http://test-only.invalid'),
          syntheticTestOnly: true),
      throwsA(isA<W02RevisionClientException>()),
    );
    await expectLater(
      W02NativeRevisionClient.capture(identity: owner, client: client,
          origin: Uri.parse('https://test-only.invalid')),
      throwsA(isA<W02RevisionClientException>()),
    );
  });
}

  // Further replay/host scope checks are covered by the source contract.
