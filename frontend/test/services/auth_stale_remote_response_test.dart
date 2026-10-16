import 'dart:async';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _identityKey = 'iamina_native_account_binding_v1';
const _tokenA = 'iamina.eyJhIjoxfQ:1abcde:sig_a';
const _tokenB = 'iamina.eyJiIjoyfQ:1abcdf:sig_b';

http.Response _response(String token, int userId) => http.Response(
  '{"access_token":"$token","user":{"id":$userId}}',
  200,
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 late login response after local sign-out cannot resurrect A',
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
    expect(service.isAuthenticated, isFalse);
    expect(service.boundNativeAccountId, isNull);

    oldLogin.complete(_response(_tokenA, 734));
    await expectLater(pending, throwsStateError);
    expect(service.isAuthenticated, isFalse);
    expect(service.hasRemoteApiCredential, isFalse);
    expect(service.boundNativeAccountId, isNull);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _identityKey), isNull);
  });

  test('W02 out-of-order A and B login responses never rebind B to A',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final oldLogin = Completer<http.Response>();
    final newLogin = Completer<http.Response>();
    final service = AuthService(
      httpClient: MockClient((request) {
        if (request.body.contains('a@example.invalid')) return oldLogin.future;
        if (request.body.contains('b@example.invalid')) return newLogin.future;
        fail('Unexpected HTTP request in synthetic test');
      }),
    );
    addTearDown(service.dispose);
    await service.initialize();

    final fromA = service.signInWithEmail('a@example.invalid', 'synthetic');
    final fromB = service.signInWithEmail('b@example.invalid', 'synthetic');
    newLogin.complete(_response(_tokenB, 812));
    await fromB;
    expect(service.boundNativeAccountId, 812);

    oldLogin.complete(_response(_tokenA, 734));
    await expectLater(fromA, throwsStateError);
    expect(service.boundNativeAccountId, 812);
    expect(await service.getIdToken(), _tokenB);
    expect(
      await const FlutterSecureStorage().read(key: _tokenKey),
      _tokenB,
    );
  });
}
