import 'dart:async';
import 'dart:io';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
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
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(
      await const FlutterSecureStorage().read(key: _localSessionKey),
      _localSessionValue,
    );
    service.dispose();
  });

  test('explicit sign-out clears local enrollment and device id even if remote logout fails', () async {
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
    expect(await const FlutterSecureStorage().read(key: _localDeviceIdKey), isNull);
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
    expect(await const FlutterSecureStorage().read(key: _localDeviceIdKey), isNull);

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
}
