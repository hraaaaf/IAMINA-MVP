import 'dart:async';
import 'dart:convert';

import 'package:amina/services/d9_first_use_transport.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _serverConfirmed = <String, Object?>{
  'version': 1,
  'completed': true,
  'completed_at': '2026-10-14T12:00:00Z',
};

const _serverPending = <String, Object?>{
  'version': 1,
  'completed': false,
  'completed_at': null,
};

http.Response _json(Object payload, [int status = 200]) => http.Response(
  jsonEncode(payload),
  status,
  headers: const {'content-type': 'application/json'},
);

void main() {
  test('D9 proof parsing rejects contradictory, missing and untrusted status',
      () {
    final confirmed = D9FirstUseProof.parse(_serverConfirmed);
    expect(confirmed?.completed, isTrue);
    expect(confirmed?.completedAt, DateTime.utc(2026, 10, 14, 12));
    expect(D9FirstUseProof.parse(_serverPending)?.completed, isFalse);
    for (final bad in <Object?>[
      null,
      <String, Object?>{'version': 2, 'completed': true,
        'completed_at': '2026-10-14T12:00:00Z'},
      <String, Object?>{'version': 1, 'completed': true, 'completed_at': null},
      <String, Object?>{'version': 1, 'completed': false,
        'completed_at': '2026-10-14T12:00:00Z'},
      <String, Object?>{'version': 1, 'completed': 'true',
        'completed_at': '2026-10-14T12:00:00Z'},
      <String, Object?>{'version': 1, 'completed': true,
        'completed_at': 'not-a-date'},
      <String, Object?>{'version': 1, 'completed': true,
        'completed_at': '2026-10-14T12:00:00'},
    ]) {
      expect(D9FirstUseProof.parse(bad), isNull, reason: '$bad');
    }
  });

  test('D9 GET requires native bearer and returns only verified server proof',
      () async {
    var requests = 0;
    final client = MockClient((request) async {
      requests++;
      expect(request.method, 'GET');
      expect(request.url.path, '/api/v1/profile/first-use');
      expect(request.headers['Authorization'], 'Bearer iamina.synthetic');
      return _json(_serverConfirmed);
    });
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async => 'iamina.synthetic',
      hasNativeCredential: () => true,
      appLockUnlocked: () => true,
      activePatientOwner: () => 734,
      authEpoch: () => 10,
      vaultGeneration: () => 11,
    );
    expect((await transport.fetch())?.completed, isTrue);
    expect(requests, 1);
    client.close();
  });

  test('D9 POST sends only explicit first-use proof, never clinical values',
      () async {
    var requests = 0;
    final client = MockClient((request) async {
      requests++;
      expect(request.method, 'POST');
      expect(request.url.path, '/api/v1/profile/first-use');
      expect(request.headers['Authorization'], 'Bearer iamina.synthetic');
      expect(jsonDecode(request.body), <String, Object>{
        'version': 1,
        'confirmed': true,
      });
      expect(request.body, isNot(contains('diabetes')));
      expect(request.body, isNot(contains('consent')));
      return _json(_serverConfirmed);
    });
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async => 'iamina.synthetic',
      hasNativeCredential: () => true,
      appLockUnlocked: () => true,
      activePatientOwner: () => 734,
      authEpoch: () => 10,
      vaultGeneration: () => 11,
    );
    expect((await transport.confirmSavedFirstUse())?.completed, isTrue);
    expect(requests, 1);
    client.close();
  });

  test('D9 credential, owner and app-lock gates deny before token or HTTP',
      () async {
    var native = false;
    var unlocked = true;
    int? owner = 734;
    var tokenReads = 0;
    var networkCalls = 0;
    final client = MockClient((request) async {
      networkCalls++;
      fail('D9 proof must never egress from an unverified vault');
    });
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async {
        tokenReads++;
        return 'iamina.synthetic';
      },
      hasNativeCredential: () => native,
      appLockUnlocked: () => unlocked,
      activePatientOwner: () => owner,
      authEpoch: () => 1,
      vaultGeneration: () => 5,
    );
    expect(await transport.fetch(), isNull);
    native = true;
    unlocked = false;
    expect(await transport.confirmSavedFirstUse(), isNull);
    unlocked = true;
    owner = null;
    expect(await transport.fetch(), isNull);
    owner = 0;
    expect(await transport.confirmSavedFirstUse(), isNull);
    expect(tokenReads, 0);
    expect(networkCalls, 0);
    client.close();
  });

  test('D9 A-B-A switch during pending response discards stale A proof',
      () async {
    var owner = 734;
    var epoch = 8;
    var generation = 2;
    final started = Completer<void>();
    final pending = Completer<http.Response>();
    final client = MockClient((request) {
      started.complete();
      return pending.future;
    });
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async => 'iamina.synthetic',
      hasNativeCredential: () => true,
      appLockUnlocked: () => true,
      activePatientOwner: () => owner,
      authEpoch: () => epoch,
      vaultGeneration: () => generation,
    );
    final request = transport.fetch();
    await started.future;
    owner = 812;
    epoch++;
    generation++;
    owner = 734; // Same owner again, but a different auth/vault epoch.
    pending.complete(_json(_serverConfirmed));
    expect(await request, isNull);
    client.close();
  });

  test('D9 logout after bearer read denies HTTP even if old token exists',
      () async {
    var epoch = 7;
    var requests = 0;
    final gotBearer = Completer<void>();
    final releaseBearer = Completer<String?>();
    final client = MockClient((request) async {
      requests++;
      fail('Stale bearer must not reach network');
    });
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async {
        gotBearer.complete();
        return releaseBearer.future;
      },
      hasNativeCredential: () => true,
      appLockUnlocked: () => true,
      activePatientOwner: () => 734,
      authEpoch: () => epoch,
      vaultGeneration: () => 1,
    );
    final future = transport.confirmSavedFirstUse();
    await gotBearer.future;
    epoch++;
    releaseBearer.complete('iamina.synthetic');
    expect(await future, isNull);
    expect(requests, 0);
    client.close();
  });

  test('D9 bad server payloads, 401/403/404 and 5xx stay unknown',
      () async {
    final responses = <http.Response>[
      _json(_serverConfirmed, 401),
      _json(_serverConfirmed, 403),
      _json(_serverConfirmed, 404),
      _json(_serverConfirmed, 503),
      _json(<String, Object>{'version': 2, 'completed': true}),
      http.Response('<html>not JSON</html>', 200),
      _json(_serverPending),
    ];
    var called = 0;
    final client = MockClient((request) async => responses[called++]);
    final transport = D9FirstUseTransport(
      baseUri: Uri.parse('https://synthetic.example'),
      client: client,
      readBearer: () async => 'iamina.synthetic',
      hasNativeCredential: () => true,
      appLockUnlocked: () => true,
      activePatientOwner: () => 734,
      authEpoch: () => 7,
      vaultGeneration: () => 1,
    );
    for (var i = 0; i < responses.length; i++) {
      expect(await transport.confirmSavedFirstUse(), isNull);
    }
    expect(called, responses.length);
    client.close();
  });

  test('D9 remote insecure HTTP origins are refused before any token lookup',
      () async {
    for (final origin in <String>[
      'http://synthetic.example',
      'https://user:password@synthetic.example',
    ]) {
      var tokens = 0;
      var egress = 0;
      final client = MockClient((request) async {
        egress++;
        return _json(_serverConfirmed);
      });
      final transport = D9FirstUseTransport(
        baseUri: Uri.parse(origin),
        client: client,
        readBearer: () async {
          tokens++;
          return 'iamina.synthetic';
        },
        hasNativeCredential: () => true,
        appLockUnlocked: () => true,
        activePatientOwner: () => 734,
        authEpoch: () => 1,
        vaultGeneration: () => 1,
      );
      expect(await transport.fetch(), isNull);
      expect(tokens, 0);
      expect(egress, 0);
      client.close();
    }
  });
}
