import 'dart:async';
import 'dart:io';

import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _syntheticLog = <String, dynamic>{
  'client_uuid': 'synthetic-d30',
  'blood_sugar': 120,
  'source': 'manual',
};

// Simulates a legacy/third-party token. It must not authorize IAMINA uploads.
class _NonNativeTokenAuthService extends AuthService {
  _NonNativeTokenAuthService({required super.httpClient});

  @override
  Future<String?> getIdToken() async => 'legacy-auth-token';
}

class _PausedTokenAuthService extends AuthService {
  final Completer<void> tokenCaptured = Completer<void>();
  final Completer<void> permitTokenReturn = Completer<void>();

  _PausedTokenAuthService({required super.httpClient});

  @override
  Future<String?> getIdToken() async {
    final previousToken = await super.getIdToken();
    if (!tokenCaptured.isCompleted) tokenCaptured.complete();
    await permitTokenReturn.future;
    return previousToken;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D30 API client never registers raw curl HTTP logging', () {
    final source = File('lib/services/api_client.dart').readAsStringSync();
    expect(source, isNot(contains('CurlInterceptor()')));
  });

  test('D30 local-only session cannot upload health payload by any journal path',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected authentication network request');
      }),
    );
    await auth.initialize();
    await auth.enrollLocalDevice();
    expect(auth.isAuthenticated, isTrue);
    expect(await auth.getIdToken(), isNull);

    var outgoingJournalRequests = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        outgoingJournalRequests++;
        fail('Clinical HTTP egress is forbidden for local-only patient');
      }),
    );

    expect(await api.syncLogEntry(_syntheticLog), isFalse);
    expect(await api.batchSyncLogs([_syntheticLog]), isEmpty);

    // Even a future caller bypassing ApiClient.syncLogEntry must hit the
    // interceptor's no-bearer denial before any HTTP dispatch.
    await expectLater(
      api.client.post<Object, Object>(
        Uri.parse('/api/v1/logs/batch'),
        body: [_syntheticLog],
      ),
      throwsA(isA<StateError>()),
    );
    expect(outgoingJournalRequests, 0);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();
  });

  test('D30 revoked bearer cannot upload a pending journal payload', () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
    });
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected auth HTTP');
      }),
    );
    await auth.initialize();
    expect(auth.hasRemoteApiCredential, isTrue);
    expect(await auth.refreshToken(), isNull);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.isAuthenticated, isTrue);

    var networkCalls = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        networkCalls++;
        fail('Revoked bearer must not cause journal HTTP');
      }),
    );

    expect(await api.syncLogEntry(_syntheticLog), isFalse);
    expect(await api.batchSyncLogs([_syntheticLog]), isEmpty);
    expect(networkCalls, 0);
    auth.dispose();
  });

  test('D30 session change during bearer read prevents medical HTTP egress',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
    });
    final auth = _PausedTokenAuthService(
      httpClient: MockClient((request) async => http.Response('', 204)),
    );
    await auth.initialize();

    var clinicalRequests = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        clinicalRequests++;
        fail('Epoch changed: clinical HTTP must be suppressed');
      }),
    );

    final inFlight = api.client.post<Object, Object>(
      Uri.parse('/api/v1/logs/batch'),
      body: [_syntheticLog],
    );
    await auth.tokenCaptured.future;
    await auth.signOut();
    expect(auth.isAuthenticated, isFalse);
    auth.permitTokenReturn.complete();

    await expectLater(inFlight, throwsA(isA<StateError>()));
    expect(clinicalRequests, 0);
    auth.dispose();
  });

  test('D30 non-native identity token cannot authorize clinical uploads',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final auth = _NonNativeTokenAuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected auth HTTP');
      }),
    );
    await auth.initialize();
    await auth.enrollLocalDevice();
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(await auth.getIdToken(), 'legacy-auth-token');

    var medicalRequests = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        medicalRequests++;
        fail('Non-native token must not authorize patient upload');
      }),
    );

    expect(await api.syncLogEntry(_syntheticLog), isFalse);
    expect(await api.batchSyncLogs([_syntheticLog]), isEmpty);
    await expectLater(
      api.client.post<Object, Object>(
        Uri.parse('/api/v1/logs/batch'),
        body: [_syntheticLog],
      ),
      throwsA(isA<StateError>()),
    );
    expect(medicalRequests, 0);
    auth.dispose();
  });

  test('D30 journal upload is never auto-retried after server failure',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
    });
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected auth HTTP');
      }),
    );
    await auth.initialize();

    for (final status in [401, 503]) {
      var outboundPosts = 0;
      final api = ApiClient(
        baseUrl: 'https://synthetic.example',
        authService: auth,
        httpClient: MockClient((request) async {
          outboundPosts++;
          expect(request.url.path, '/api/v1/logs/batch');
          return http.Response(
            '{"error":"synthetic"}',
            status,
            headers: {'content-type': 'application/json'},
          );
        }),
      );

      expect(await api.batchSyncLogs([_syntheticLog]), isEmpty);
      expect(outboundPosts, 1);
    }
    auth.dispose();
  });

  test('D30 valid remote bearer preserves existing authenticated log sync', () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': 'iamina.e30:1abcde:signature_123',
    });
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Unexpected auth HTTP');
      }),
    );
    await auth.initialize();
    expect(auth.hasRemoteApiCredential, isTrue);

    var journalPosts = 0;
    final api = ApiClient(
      baseUrl: 'https://synthetic.example',
      authService: auth,
      httpClient: MockClient((request) async {
        journalPosts++;
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/logs/batch');
        expect(
          request.headers['authorization'],
          'Bearer iamina.e30:1abcde:signature_123',
        );
        return http.Response(
          '{"synced_ids":["synthetic-d30"]}',
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    expect(await api.batchSyncLogs([_syntheticLog]), ['synthetic-d30']);
    expect(journalPosts, 1);
    auth.dispose();
  });
}
