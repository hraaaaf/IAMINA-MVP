import 'dart:async';
import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/cal12_server_session_liveness.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const tokenA = 'iamina.syntheticA:123abc:fixture_A';
const tokenB = 'iamina.syntheticB:123abd:fixture_B';
const headers = <String, String>{
  'cache-control': 'no-store, private, max-age=0',
  'content-type': 'application/json',
};

class _FakeLock implements AppLockAuthenticator {
  @override
  Future<AppLockCapability> capability() async => AppLockCapability.supported;

  @override
  Future<AppLockCredential> enroll() async => const AppLockCredential(
        credentialId: 'fixture-cal12',
        publicKeySpki: 'fixture-key',
        rpId: 'localhost',
        origin: 'http://localhost',
        signCount: 1,
      );

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) async =>
      const AppLockAssertion(signCount: 2);
}

http.Response verified(int id) => http.Response(
      jsonEncode({'active': true, 'account_id': id}),
      200,
      headers: headers,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthService auth;
  late AppLockService lock;
  late PatientVaultSessionController vault;
  late http.Client transport;
  late http.Response Function(http.Request) livenessResult;
  Completer<http.Response>? pending;
  var verifyCalls = 0;

  setUp(() async {
    FlutterSecureStorage.setMockInitialValues({});
    verifyCalls = 0;
    pending = null;
    livenessResult = (_) => verified(734);
    transport = MockClient((request) async {
      if (request.url.path == '/api/v1/auth/login') {
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        final a = data['email'] == 'a@example.invalid';
        if (!a && data['email'] != 'b@example.invalid') {
          fail('Unexpected non-fixture account');
        }
        return http.Response(jsonEncode({
          'access_token': a ? tokenA : tokenB,
          'user': {'id': a ? 734 : 812},
        }), 200);
      }
      if (request.url.path == '/api/v1/auth/logout') {
        return http.Response('', 204);
      }
      if (request.url.path == '/api/v1/auth/session/verify') {
        verifyCalls++;
        expect(request.method, 'GET');
        expect(request.url.host, anyOf('localhost', '127.0.0.1'));
        expect(request.followRedirects, isFalse);
        expect(request.headers['Authorization'], startsWith('Bearer iamina.'));
        expect(request.headers['Cache-Control'], 'no-store');
        return pending?.future ?? livenessResult(request);
      }
      fail('Unexpected CAL-12 HTTP path: ' + request.url.path);
    });
    auth = AuthService(httpClient: transport);
    await auth.initialize();
    lock = AppLockService(
      authService: auth,
      authenticator: _FakeLock(),
      protectedLocalStateProbe: () async => false,
    );
    await lock.initialize();
    vault = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: auth.resolvePatientVaultScope,
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
    );
    await vault.reconcile();
  });

  tearDown(() {
    vault.dispose();
    lock.dispose();
    auth.dispose();
    transport.close();
  });

  Future<void> login(String email) async {
    await auth.signInWithEmail(email, 'fictional-only');
    await vault.reconcile();
  }

  Future<void> setupA() async {
    await login('a@example.invalid');
    await lock.configure();
    expect(auth.isRemoteCredentialVerified, isTrue);
  }

  Future<bool> probe() => Cal12ServerSessionLiveness.verifyOnce(
        auth: auth, vault: vault, appLock: lock, client: transport,
      );

  test('CAL12 no login, local-only or audit cannot reach server', () async {
    expect(Cal12ServerSessionLiveness.realPatientExportEnabled, isFalse);
    expect(await probe(), isFalse);
    await auth.enrollLocalDevice();
    await vault.reconcile();
    expect(await probe(), isFalse);
    await auth.signOut();
    auth.enterAuditSession();
    await vault.reconcile();
    expect(await probe(), isFalse);
    expect(verifyCalls, 0);
  });

  test('CAL12 current session has exact owner and noncacheable proof', () async {
    await setupA();
    expect(await probe(), isTrue);
    expect(verifyCalls, 1);
    expect(auth.boundNativeAccountId, 734);
  });

  test('CAL12 deny 401, 503, wrong owner, cache, redirect, forged body',
      () async {
    await setupA();
    final failures = <http.Response>[
      http.Response('{"detail":"revoked"}', 401, headers: headers),
      http.Response('unavailable', 503, headers: headers),
      http.Response('{"active":true,"account_id":812}', 200,
          headers: headers),
      http.Response('{"active":false,"account_id":734}', 200,
          headers: headers),
      http.Response('{"active":true,"account_id":734}', 200,
          headers: {'content-type': 'application/json'}),
      http.Response('{"active":true,"account_id":734}', 302,
          headers: {...headers, 'location': 'https://different.invalid'}),
      http.Response('{broken-json}', 200, headers: headers),
      http.Response('{"active":true,"account_id":"734"}', 200,
          headers: headers),
    ];
    for (final failure in failures) {
      livenessResult = (_) => failure;
      expect(await probe(), isFalse,
          reason: 'Denied HTTP ' + failure.statusCode.toString());
    }
    expect(verifyCalls, failures.length);
  });

  test('CAL12 lock during request denies stale result, unlock can retry',
      () async {
    await setupA();
    pending = Completer<http.Response>();
    final started = probe();
    await Future<void>.delayed(Duration.zero);
    expect(verifyCalls, 1);
    lock.lock();
    pending!.complete(verified(734));
    expect(await started, isFalse);
    pending = null;
    await lock.unlock();
    expect(await probe(), isTrue);
  });

  test('CAL12 A-B-A during network wait does not revive old evidence',
      () async {
    await setupA();
    pending = Completer<http.Response>();
    final started = probe();
    await Future<void>.delayed(Duration.zero);
    expect(verifyCalls, 1);
    await auth.signOut();
    await login('b@example.invalid');
    await lock.unlock();
    await auth.signOut();
    await login('a@example.invalid');
    await lock.unlock();
    pending!.complete(verified(734));
    expect(await started, isFalse);
    pending = null;
    expect(await probe(), isTrue);
  });

  test('CAL12 reply for patient B never validates active patient A',
      () async {
    await setupA();
    livenessResult = (_) => verified(812);
    expect(await probe(), isFalse);
    await auth.signOut();
    await login('b@example.invalid');
    await lock.unlock();
    expect(await probe(), isTrue);
  });

  test('CAL12 offline cached bearer cannot trigger remote liveness',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': tokenA,
      'iamina_native_account_binding_v1':
          jsonEncode({'token': tokenA, 'user_id': 734}),
    });
    final restored = AuthService(httpClient: transport);
    await restored.initialize();
    final rVault = PatientVaultSessionController(
      authChanges: restored,
      resolveScope: restored.resolvePatientVaultScope,
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
    );
    final rLock = AppLockService(
      authService: restored,
      authenticator: _FakeLock(),
      protectedLocalStateProbe: () async => false,
    );
    await rLock.initialize();
    await rLock.configure();
    await rVault.reconcile();
    expect(restored.boundNativeAccountId, 734);
    expect(restored.isRemoteCredentialVerified, isFalse);
    expect(await Cal12ServerSessionLiveness.verifyOnce(
      auth: restored, vault: rVault, appLock: rLock, client: transport,
    ), isFalse);
    expect(verifyCalls, 0);
    rVault.dispose();
    rLock.dispose();
    restored.dispose();
  });
}
