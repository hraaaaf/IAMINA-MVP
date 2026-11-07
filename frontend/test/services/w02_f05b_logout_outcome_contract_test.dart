import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _token = 'iamina.e30:1abcde:w02_f05b_status_synthetic';
const _tokenKey = 'iamina_native_access_token';
const _enrollmentKey = 'iamina_local_session_v1';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  AuthService createService({
    required Future<http.Response> Function(http.Request) onRequest,
    required List<String> failures,
  }) {
    FlutterSecureStorage.setMockInitialValues({
      _tokenKey: _token,
      _enrollmentKey: 'enrolled',
    });
    return AuthService(
      httpClient: MockClient(onRequest),
      failureLogger: (operation, errorType, _) {
        failures.add('$operation:$errorType');
      },
    );
  }

  test('W02 F05B status: offline logout is locally complete but not server-confirmed',
      () async {
    final failures = <String>[];
    final auth = createService(
      failures: failures,
      onRequest: (request) async {
        expect(request.url.path, '/api/v1/auth/logout');
        expect(request.headers['Authorization'], 'Bearer $_token');
        throw http.ClientException('offline', request.url);
      },
    );
    await auth.initialize();
    expect(auth.hasRemoteApiCredential, isTrue);

    // Offline transport errors cannot make the already revoked LOCAL session
    // appear active or prevent the local-first logout from completing.
    await auth.signOut();
    expect(auth.isAuthenticated, isFalse);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isFalse);
    expect(failures, <String>['logout:ClientException']);
    expect(await const FlutterSecureStorage().read(key: _tokenKey), isNull);
    auth.dispose();
  });

  test('W02 F05B status: HTTP 503 is an explicit failed server revocation',
      () async {
    final failures = <String>[];
    final auth = createService(
      failures: failures,
      onRequest: (request) async {
        expect(request.url.path, '/api/v1/auth/logout');
        return http.Response('{"detail":"unavailable"}', 503);
      },
    );
    await auth.initialize();

    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.isAuthenticated, isFalse);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isFalse);
    expect(failures, <String>['logout:StateError']);
    auth.dispose();
  });

  test('W02 F05B status: HTTP 200 confirms server revocation for this request',
      () async {
    final failures = <String>[];
    final auth = createService(
      failures: failures,
      onRequest: (request) async {
        expect(request.url.path, '/api/v1/auth/logout');
        return http.Response('{"detail":"Signed out"}', 200);
      },
    );
    await auth.initialize();

    await auth.signOut();
    expect(auth.isAuthenticated, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isTrue);
    expect(failures, isEmpty);
    auth.dispose();
  });
}
