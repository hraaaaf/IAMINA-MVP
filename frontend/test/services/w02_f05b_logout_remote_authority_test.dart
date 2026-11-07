import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _bearer = 'iamina.e30:1abcde:f05b_synthetic_signature';
const _tokenKey = 'iamina_native_access_token';
const _bindingKey = 'iamina_native_account_binding_v1';
const _localKey = 'iamina_local_session_v1';
const _fenceKey = 'iamina_auth_logout_pending_v1';

class _BrokenLocalStorage implements FlutterSecureStorage {
  final bool refuseFence;
  final bool refuseBearerDelete;
  final values = <String, String>{
    _tokenKey: _bearer,
    _bindingKey: jsonEncode({'token': _bearer, 'user_id': 734}),
    _localKey: 'enrolled',
  };

  _BrokenLocalStorage({
    this.refuseFence = false,
    this.refuseBearerDelete = false,
  });

  Future<String?> _read(String key) async => values[key];
  Future<void> _write(String key, String value) async {
    if (key == _fenceKey && refuseFence) {
      throw StateError('synthetic fence persistence unavailable');
    }
    values[key] = value;
  }
  Future<void> _delete(String key) async {
    if (key == _tokenKey && refuseBearerDelete) {
      throw StateError('synthetic bearer erasure unavailable');
    }
    values.remove(key);
  }

  @override
  dynamic noSuchMethod(Invocation invocation) {
    final key = invocation.namedArguments[#key] as String?;
    switch (invocation.memberName) {
      case #read:
        return _read(key!);
      case #write:
        return _write(key!, invocation.namedArguments[#value] as String);
      case #delete:
        return _delete(key!);
      default:
        throw UnsupportedError('Unexpected secure storage operation');
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 F05B-HTTP1: local storage failure cannot skip server-side logout',
      () async {
    final storage = _BrokenLocalStorage(
      refuseFence: true,
      refuseBearerDelete: true,
    );
    var remoteCalls = 0;
    final auth = AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/logout') {
          remoteCalls++;
          expect(request.headers['Authorization'], 'Bearer $_bearer');
          return http.Response('{"detail":"Signed out"}', 200);
        }
        fail('Unexpected synthetic endpoint: ${request.url.path}');
      }),
    );
    await auth.initialize();
    expect(await auth.getIdToken(), _bearer);
    await expectLater(auth.signOut(), throwsStateError);
    // Local erasure fails, but server is still available: always attempt
    // revocation of the old bearer, even if secure storage reports failure.
    expect(remoteCalls, 1);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();
  });

  test('W02 F05B-HTTP2: server rejecting logout must not be reported as success',
      () async {
    final storage = _BrokenLocalStorage();
    var remoteCalls = 0;
    final auth = AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/logout') {
          remoteCalls++;
          return http.Response('{"detail":"Unavailable"}', 503);
        }
        fail('Unexpected synthetic endpoint: ${request.url.path}');
      }),
    );
    await auth.initialize();
    // Even when local keys are erased, a remote 503 is NOT proof that the
    // Django auth_token_version has advanced.
    await expectLater(auth.signOut(), throwsStateError);
    expect(remoteCalls, 1);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(storage.values.containsKey(_tokenKey), isFalse);
    auth.dispose();
  });
}
