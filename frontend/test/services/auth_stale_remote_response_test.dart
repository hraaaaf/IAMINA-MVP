// W02 synthetic-only regression candidate for frontend/test/services/.
// Must be run with Flutter on the exact patched checkout; not yet CI certified.
import 'dart:async';
import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _identityKey = 'iamina_native_account_binding_v1';
const _tokenA = 'iamina.eyJhIjoxfQ:1abcde:sig_a';
const _tokenB = 'iamina.eyJiIjoyfQ:1abcdf:sig_b';

http.Response _response(String token, int userId) =>
    http.Response('{"access_token":"$token","user":{"id":$userId}}', 200);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'W02 logout rejects late A HTTP reply and leaves no bearer in storage',
    () async {
      FlutterSecureStorage.setMockInitialValues({});
      final oldLogin = Completer<http.Response>();
      final service = AuthService(
        httpClient: MockClient((request) {
          expect(request.url.path, '/api/v1/auth/login');
          return oldLogin.future;
        }),
      );
      addTearDown(service.dispose);
      await service.initialize();
      final pending = service.signInWithEmail('a@example.invalid', 'synthetic');
      await service.signOut();
      oldLogin.complete(_response(_tokenA, 734));
      await expectLater(pending, throwsStateError);
      expect(service.isAuthenticated, isFalse);
      expect(service.hasRemoteApiCredential, isFalse);
      expect(service.boundNativeAccountId, isNull);
      expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
      expect(
        await const FlutterSecureStorage().read(key: _identityKey),
        isNull,
      );
    },
  );

  test(
    'W02 out-of-order A/B HTTP replies must keep B identity and storage',
    () async {
      FlutterSecureStorage.setMockInitialValues({});
      final fromOld = Completer<http.Response>();
      final fromNew = Completer<http.Response>();
      final service = AuthService(
        httpClient: MockClient((request) {
          if (request.body.contains('a@example.invalid')) return fromOld.future;
          if (request.body.contains('b@example.invalid')) return fromNew.future;
          fail('Unexpected synthetic HTTP operation');
        }),
      );
      addTearDown(service.dispose);
      await service.initialize();
      final pendingA = service.signInWithEmail(
        'a@example.invalid',
        'synthetic',
      );
      final pendingB = service.signInWithEmail(
        'b@example.invalid',
        'synthetic',
      );
      fromNew.complete(_response(_tokenB, 812));
      await pendingB;
      fromOld.complete(_response(_tokenA, 734));
      await expectLater(pendingA, throwsStateError);
      expect(service.boundNativeAccountId, 812);
      expect(await service.getIdToken(), _tokenB);
      expect(await const FlutterSecureStorage().read(key: _tokenKey), _tokenB);
    },
  );

  test('W02 switching into audit session rejects late remote login', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final late = Completer<http.Response>();
    final service = AuthService(httpClient: MockClient((_) => late.future));
    addTearDown(service.dispose);
    await service.initialize();
    final pending = service.signInWithEmail('a@example.invalid', 'synthetic');
    service.enterAuditSession();
    late.complete(_response(_tokenA, 734));
    await expectLater(pending, throwsStateError);
    expect(service.isAuditSession, isTrue);
    expect(await service.getIdToken(), isNull);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
  });

  test(
    'W02 new local enrollment invalidates older pending remote login',
    () async {
      FlutterSecureStorage.setMockInitialValues({});
      final late = Completer<http.Response>();
      final service = AuthService(httpClient: MockClient((_) => late.future));
      addTearDown(service.dispose);
      await service.initialize();
      final pending = service.signInWithEmail('a@example.invalid', 'synthetic');
      await service.enrollLocalDevice();
      late.complete(_response(_tokenA, 734));
      await expectLater(pending, throwsStateError);
      expect(service.boundNativeAccountId, isNull);
      expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    },
  );

  test(
    'W02 retained A bearer plus revocation tombstone must not restore A',
    () async {
      // Models a browser restart after a real secure-storage token DELETE failure:
      // old token bytes survived, but the earlier durable tombstone was written.
      FlutterSecureStorage.setMockInitialValues({
        _tokenKey: _tokenA,
        _identityKey: jsonEncode({'token': _tokenA, 'user_id': 734}),
        'iamina_local_session_v1': 'enrolled',
        'iamina_web_session_revoked_v1': 'revoked',
      });
      final service = AuthService();
      addTearDown(service.dispose);
      await service.initialize();
      expect(service.hasRemoteApiCredential, isFalse);
      expect(service.boundNativeAccountId, isNull);
      expect(service.isAuthenticated, isFalse);
      expect(await service.resolvePatientVaultScope(), isNull);
      // No silent deletion is assumed: this intentionally remains on disk.
      expect(await const FlutterSecureStorage().read(key: _tokenKey), _tokenA);
    },
  );

  test(
    'W02 a newly verified B can replace the revoked A storage atomically',
    () async {
      FlutterSecureStorage.setMockInitialValues({
        _tokenKey: _tokenA,
        _identityKey: jsonEncode({'token': _tokenA, 'user_id': 734}),
        'iamina_web_session_revoked_v1': 'revoked',
      });
      final service = AuthService(
        httpClient: MockClient((request) async {
          expect(request.url.path, '/api/v1/auth/login');
          return _response(_tokenB, 812);
        }),
      );
      addTearDown(service.dispose);
      await service.initialize();
      expect(service.boundNativeAccountId, isNull);
      await service.signInWithEmail('b@example.invalid', 'synthetic');
      expect(service.boundNativeAccountId, 812);
      expect(await service.getIdToken(), _tokenB);
      const store = FlutterSecureStorage();
      expect(await store.read(key: 'iamina_web_session_revoked_v1'), isNull);
      expect(await store.read(key: _tokenKey), _tokenB);
      final restored = AuthService();
      addTearDown(restored.dispose);
      await restored.initialize();
      if (kIsWeb) {
        expect(restored.boundNativeAccountId, isNull);
        expect(restored.isAuthenticated, isFalse);
        expect(await restored.getIdToken(), isNull);
      } else {
        expect(restored.boundNativeAccountId, 812);
      }
    },
  );

  test(
    'W02 local enrollment wipes prior remote A before clearing tombstone',
    () async {
      FlutterSecureStorage.setMockInitialValues({
        _tokenKey: _tokenA,
        _identityKey: jsonEncode({'token': _tokenA, 'user_id': 734}),
        'iamina_web_session_revoked_v1': 'revoked',
      });
      final service = AuthService();
      addTearDown(service.dispose);
      await service.initialize();
      await service.enrollLocalDevice();
      const store = FlutterSecureStorage();
      expect(await store.read(key: _tokenKey), isNull);
      expect(await store.read(key: _identityKey), isNull);
      expect(await store.read(key: 'iamina_web_session_revoked_v1'), isNull);
      expect(service.boundNativeAccountId, isNull);
      final restarted = AuthService();
      addTearDown(restarted.dispose);
      await restarted.initialize();
      expect(restarted.boundNativeAccountId, isNull);
      expect(restarted.isAuthenticated, isTrue);
    },
  );
  test(
    'W02 A Web cached A without tombstone NEVER restores after refresh',
    () async {
      if (!kIsWeb) return;
      FlutterSecureStorage.setMockInitialValues({
        _tokenKey: _tokenA,
        _identityKey: jsonEncode({'token': _tokenA, 'user_id': 734}),
        'iamina_local_session_v1': 'enrolled',
      });
      final service = AuthService();
      addTearDown(service.dispose);
      await service.initialize();
      expect(service.hasRemoteApiCredential, isFalse);
      expect(service.isAuthenticated, isFalse);
      expect(service.boundNativeAccountId, isNull);
      expect(await service.getIdToken(), isNull);
      expect(await service.resolvePatientVaultScope(), isNull);
    },
  );

  test('W02 A Web B must login online again after browser refresh', () async {
    if (!kIsWeb) return;
    FlutterSecureStorage.setMockInitialValues({
      _tokenKey: _tokenB,
      _identityKey: jsonEncode({'token': _tokenB, 'user_id': 812}),
      'iamina_local_session_v1': 'enrolled',
    });
    final service = AuthService(
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/auth/login');
        return _response(_tokenB, 812);
      }),
    );
    addTearDown(service.dispose);
    await service.initialize();
    expect(service.boundNativeAccountId, isNull);
    expect(service.isAuthenticated, isFalse);
    await service.signInWithEmail('b@example.invalid', 'synthetic');
    expect(service.boundNativeAccountId, 812);
    expect(await service.getIdToken(), _tokenB);
    final refreshed = AuthService();
    addTearDown(refreshed.dispose);
    await refreshed.initialize();
    expect(refreshed.boundNativeAccountId, isNull);
    expect(refreshed.isAuthenticated, isFalse);
    expect(await refreshed.getIdToken(), isNull);
  });
}
