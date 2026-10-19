import 'dart:async';
import 'dart:io';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _identityKey = 'iamina_native_account_binding_v1';
const _localSessionKey = 'iamina_local_session_v1';
const _localSessionValue = 'enrolled';
const _localDeviceIdKey = 'iamina_local_device_id_v1';
const _token = 'iamina.e30:1abcde:signature_123';
const _freshToken = 'iamina.eyJ1aWQiOjEsInYiOjB9:1abcdf:signature_456';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  void seedStorage(Map<String, String> values) {
    FlutterSecureStorage.setMockInitialValues(values);
  }

  MockClient noBootNetworkClient() => MockClient((request) async {
        fail('Local-first operation must perform zero network requests');
      });

  test('first enrollment is device-local with zero network', () async {
    seedStorage({});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    await service.enrollLocalDevice();

    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(service.hasRemoteApiCredential, isFalse);
    expect(await service.getIdToken(), isNull);
    expect(
      await const FlutterSecureStorage().read(key: _localSessionKey),
      _localSessionValue,
    );
    final deviceId =
        await const FlutterSecureStorage().read(key: _localDeviceIdKey);
    expect(deviceId, isNotNull);
    expect(deviceId, isNotEmpty);
    service.dispose();
  });

  test('local enrollment cannot run before auth initialization', () async {
    seedStorage({});
    final service = AuthService(httpClient: noBootNetworkClient());

    expect(service.enrollLocalDevice(), throwsStateError);
    expect(service.isAuthenticated, isFalse);
    service.dispose();
  });


  test('hosted demo uses local audit session without remote auth', () {
    expect(
      demoUsesLocalAuditSession(
        offlineDemo: false,
        remoteAccountEnrollmentEnabled: true,
      ),
      isTrue,
    );
  });

  test('offline demo uses local audit session', () {
    expect(
      demoUsesLocalAuditSession(
        offlineDemo: true,
        remoteAccountEnrollmentEnabled: false,
      ),
      isTrue,
    );
  });

  test('non-demo local build keeps legacy auth path', () {
    expect(
      demoUsesLocalAuditSession(
        offlineDemo: false,
        remoteAccountEnrollmentEnabled: false,
      ),
      isFalse,
    );
  });

  test('remote account enrollment fails closed by default', () async {
    seedStorage({});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    await expectLater(
      service.registerWithEmail('patient@example.com', 'not-used-locally'),
      throwsStateError,
    );

    expect(service.isAuthenticated, isFalse);
    expect(await const FlutterSecureStorage().read(key: _localSessionKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localDeviceIdKey), isNull);
    service.dispose();
  });

  test('registration status 400 maps to weak password', () {
    final failure = registrationFailureForStatus(400);
    expect(failure.code, RegistrationFailureCode.weakPassword);
    expect(failure.statusCode, 400);
  });

  test('registration status 409 maps to account exists', () {
    final failure = registrationFailureForStatus(409);
    expect(failure.code, RegistrationFailureCode.accountExists);
    expect(failure.statusCode, 409);
  });

  test('unexpected registration status maps to rejected', () {
    final failure = registrationFailureForStatus(503);
    expect(failure.code, RegistrationFailureCode.rejected);
    expect(failure.statusCode, 503);
  });

  test('local enrollment is exposed only after secure marker persistence', () {
    final source = File('lib/services/auth_service.dart').readAsStringSync();
    final methodStart = source.indexOf('Future<void> _ensureLocalEnrollment()');
    final writeIndex = source.indexOf(
      'await _storage.write(key: _localSessionKey, value: _localSessionValue);',
      methodStart,
    );
    final stateIndex = source.indexOf(
      '_localSessionEnrolled = true;',
      methodStart,
    );

    expect(methodStart, greaterThanOrEqualTo(0));
    expect(writeIndex, greaterThan(methodStart));
    expect(stateIndex, greaterThan(writeIndex));
  });

  test('legacy native bearer migrates locally with zero boot network', () async {
    seedStorage({_tokenKey: _token});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(service.hasRemoteApiCredential, isTrue);
    expect(service.boundNativeAccountId, isNull); // No legacy identity binding.
    expect(await service.getIdToken(), _token);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), _token);
    expect(
      await const FlutterSecureStorage().read(key: _localSessionKey),
      _localSessionValue,
    );
    service.dispose();
  });

  test('established local enrollment reopens with bearer and zero boot network', () async {
    seedStorage({_tokenKey: _token, _localSessionKey: _localSessionValue});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(await service.getIdToken(), _token);
    service.dispose();
  });

  test('marker-only local enrollment reopens with zero boot network', () async {
    seedStorage({_localSessionKey: _localSessionValue});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(await service.getIdToken(), isNull);
    service.dispose();
  });

  test('successful remote login creates local enrollment and verified bearer', () async {
    seedStorage({});
    final service = AuthService(
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/auth/login');
        return http.Response(
          '{"access_token":"$_freshToken","user":{"id":1}}',
          200,
        );
      }),
    );
    await service.initialize();
    await service.signInWithEmail('patient@example.com', 'correct-password');

    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isTrue);
    expect(service.hasRemoteApiCredential, isTrue);
    expect(service.boundNativeAccountId, 1);
    expect(await service.getIdToken(), _freshToken);
    expect(
      await const FlutterSecureStorage().read(key: _localSessionKey),
      _localSessionValue,
    );
    service.dispose();
  });

  test('remote 401 retry path drops bearer but preserves local enrollment', () async {
    seedStorage({_tokenKey: _token, _localSessionKey: _localSessionValue});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    final refreshed = await service.refreshToken();

    expect(refreshed, isNull);
    expect(service.isAuthenticated, isTrue);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(service.hasRemoteApiCredential, isFalse);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(
      await const FlutterSecureStorage().read(key: _localSessionKey),
      _localSessionValue,
    );
    service.dispose();
  });

  test('D7 sign-out invalidates the epoch before any storage await', () async {
    seedStorage({_tokenKey: _token, _localSessionKey: _localSessionValue});
    final service = AuthService(httpClient: MockClient((request) async =>
        http.Response('', 204)));
    await service.initialize();
    final before = AuthService.authEpoch;
    final loggingOut = service.signOut();
    expect(AuthService.authEpoch, greaterThan(before));
    expect(service.isAuthenticated, isFalse);
    await loggingOut;
    service.dispose();
  });

  test('explicit sign-out revokes session but preserves dormant device vault locator', () async {
    seedStorage({
      _tokenKey: _token,
      _localSessionKey: _localSessionValue,
      _localDeviceIdKey: 'device-id',
    });
    final service = AuthService(
      httpClient: MockClient((request) async {
        throw http.ClientException('offline', request.url);
      }),
    );
    await service.initialize();
    await service.signOut();

    expect(service.isAuthenticated, isFalse);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localSessionKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localDeviceIdKey), 'device-id');
    expect(await service.resolvePatientVaultScope(), isNull);
    service.dispose();
  });

  test('D7 offline local vault stays dormant until explicitly re-enrolled',
      () async {
    seedStorage({});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();
    await service.enrollLocalDevice();
    final original = (await service.resolvePatientVaultScope())!.databaseName;
    await service.signOut();
    expect(service.isAuthenticated, isFalse);
    expect(await service.resolvePatientVaultScope(), isNull);
    expect(
      (await service.dormantDeviceVaultForProtectedStateProbe())?.databaseName,
      original,
    );
    await service.enrollLocalDevice();
    expect((await service.resolvePatientVaultScope())?.databaseName, original);
    service.dispose();
  });

  test('stalled remote logout cannot delay local sign-out', () async {
    seedStorage({
      _tokenKey: _token,
      _localSessionKey: _localSessionValue,
      _localDeviceIdKey: 'device-id',
    });
    final remoteLogout = Completer<http.Response>();
    final service = AuthService(
      httpClient: MockClient((request) => remoteLogout.future),
    );
    await service.initialize();

    final signOut = service.signOut();
    await Future<void>.delayed(Duration.zero);

    expect(service.isAuthenticated, isFalse);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localSessionKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localDeviceIdKey), 'device-id');

    remoteLogout.complete(http.Response('', 204));
    await signOut;
    service.dispose();
  });

  test('malformed secure-storage text cannot bootstrap local enrollment', () async {
    seedStorage({_tokenKey: 'not-an-iamina-token'});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    expect(service.isAuthenticated, isFalse);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localSessionKey), isNull);
    service.dispose();
  });

  test('prefixed malformed bearer cannot bootstrap local enrollment', () async {
    seedStorage({_tokenKey: 'iamina.previously-enrolled-token'});
    final service = AuthService(httpClient: noBootNetworkClient());
    await service.initialize();

    expect(service.isAuthenticated, isFalse);
    expect(service.isRemoteCredentialVerified, isFalse);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _localSessionKey), isNull);
    service.dispose();
  });
  test('W01 stale A login never replaces B in either HTTP response order', () async {
    for (final bFirst in <bool>[true, false]) {
      seedStorage({});
      final patientA = Completer<http.Response>();
      final patientB = Completer<http.Response>();
      final service = AuthService(httpClient: MockClient((request) {
        if (request.body.contains('a@example.com')) return patientA.future;
        if (request.body.contains('b@example.com')) return patientB.future;
        fail('Unexpected endpoint in synthetic login race');
      }));
      await service.initialize();
      final aLogin = service.signInWithEmail('a@example.com', 'synthetic');
      final aRejected = expectLater(aLogin, throwsStateError);
      final bLogin = service.signInWithEmail('b@example.com', 'synthetic');

      final aResponse = http.Response(
        '{"access_token":"$_token","user":{"id":734}}', 200);
      final bResponse = http.Response(
        '{"access_token":"$_freshToken","user":{"id":812}}', 200);
      if (bFirst) {
        patientB.complete(bResponse);
        await bLogin;
        patientA.complete(aResponse);
        await aRejected;
      } else {
        patientA.complete(aResponse);
        await aRejected;
        patientB.complete(bResponse);
        await bLogin;
      }

      expect(service.boundNativeAccountId, 812);
      expect(await service.getIdToken(), _freshToken);
      expect(await const FlutterSecureStorage().read(key: _tokenKey), _freshToken);
      expect(await const FlutterSecureStorage().read(key: _identityKey),
          contains('"user_id":812'));
      service.dispose();
    }
  });

  test('W01 logout cancels a pending login before its HTTP completion', () async {
    seedStorage({});
    final pending = Completer<http.Response>();
    final service = AuthService(httpClient: MockClient((request) => pending.future));
    await service.initialize();

    final oldLogin = service.signInWithEmail('a@example.com', 'synthetic');
    final rejected = expectLater(oldLogin, throwsStateError);
    await service.signOut();
    pending.complete(http.Response(
        '{"access_token":"$_token","user":{"id":734}}', 200));
    await rejected;

    expect(service.isAuthenticated, isFalse);
    expect(service.hasRemoteApiCredential, isFalse);
    expect(service.boundNativeAccountId, isNull);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _identityKey), isNull);
    service.dispose();
  });

  test('D7 native binding persists offline only with the exact bearer', () async {
    seedStorage({});
    final service = AuthService(httpClient: MockClient((request) async =>
        http.Response('{"access_token":"' + _freshToken + '","user":{"id":734}}', 200)));
    await service.initialize();
    await service.signInWithEmail('a@example.com', 'secret');
    expect(service.boundNativeAccountId, 734);
    expect(await const FlutterSecureStorage().read(key: _identityKey),
        contains('"user_id":734'));
    service.dispose();
    final reopened = AuthService(httpClient: noBootNetworkClient());
    await reopened.initialize();
    expect(reopened.boundNativeAccountId, 734);
    expect(reopened.isRemoteCredentialVerified, isFalse);
    reopened.dispose();
  });

  test('D7 mismatched or invalid cached binding fails closed', () async {
    seedStorage({
      _tokenKey: _token,
      _identityKey: '{"token":"' + _freshToken + '","user_id":734}',
    });
    final mismatch = AuthService(httpClient: noBootNetworkClient());
    await mismatch.initialize();
    expect(mismatch.boundNativeAccountId, isNull);
    mismatch.dispose();
    seedStorage({
      _tokenKey: _token,
      _identityKey: '{"token":"' + _token + '","user_id":-1}',
    });
    final invalid = AuthService(httpClient: noBootNetworkClient());
    await invalid.initialize();
    expect(invalid.boundNativeAccountId, isNull);
    invalid.dispose();
  });

  test('D7 A logout B native binding switches without stale patient ID', () async {
    seedStorage({});
    final service = AuthService(httpClient: MockClient((request) async {
      if (request.url.path == '/api/v1/auth/logout') {
        return http.Response('', 204);
      }
      final b = request.body.contains('b@example.com');
      return http.Response(
          '{"access_token":"' + (b ? _freshToken : _token) +
          '","user":{"id":' + (b ? '812' : '734') + '}}', 200);
    }));
    await service.initialize();
    await service.signInWithEmail('a@example.com', 'secret');
    expect(service.boundNativeAccountId, 734);
    await service.signOut();
    expect(service.boundNativeAccountId, isNull);
    expect(await const FlutterSecureStorage().read(key: _identityKey), isNull);
    await service.signInWithEmail('b@example.com', 'secret');
    expect(service.boundNativeAccountId, 812);
    service.dispose();
  });

  test('D7 malformed native user ID never persists an account binding', () async {
    seedStorage({});
    final service = AuthService(httpClient: MockClient((request) async =>
        http.Response('{"access_token":"' + _freshToken +
            '","user":{"id":"812"}}', 200)));
    await service.initialize();
    await expectLater(
        service.signInWithEmail('b@example.com', 'secret'), throwsStateError);
    expect(service.boundNativeAccountId, isNull);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _identityKey), isNull);
    service.dispose();
  });

  test('D7 vault resolution only accepts typed bound principals', () async {
    seedStorage({_tokenKey: _token});
    final old = AuthService(httpClient: noBootNetworkClient());
    await old.initialize();
    expect(await old.resolvePatientVaultScope(), isNull);
    old.dispose();

    seedStorage({_localSessionKey: _localSessionValue});
    final legacy = AuthService(httpClient: noBootNetworkClient());
    await legacy.initialize();
    expect(await legacy.resolvePatientVaultScope(), isNull);
    await legacy.enrollLocalDevice();
    expect(
      (await legacy.resolvePatientVaultScope())?.databaseName,
      startsWith('amina_vault_v1_device_'),
    );
    legacy.dispose();

    seedStorage({});
    final remote = AuthService(httpClient: MockClient((request) async =>
        http.Response('{"access_token":"' + _freshToken +
            '","user":{"id":734}}', 200)));
    await remote.initialize();
    await remote.signInWithEmail('a@example.com', 'secret');
    expect(
      (await remote.resolvePatientVaultScope())?.databaseName,
      'amina_vault_v1_native_734',
    );
    await remote.signOut();
    expect(await remote.resolvePatientVaultScope(), isNull);
    remote.dispose();
  });

}
