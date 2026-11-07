import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _bindingKey = 'iamina_native_account_binding_v1';
const _enrollmentKey = 'iamina_local_session_v1';
const _fenceKey = 'iamina_auth_logout_pending_v1';
const _token = 'iamina.e30:1abcde:f05_synthetic_signature';

/// Deliberate non-atomic secure-storage faults; no PHI, device keys or remote
/// identity provider. The fake returns stored values across AuthService restarts.
class _FailingLogoutStorage implements FlutterSecureStorage {
  final values = <String, String>{
    _tokenKey: _token,
    _bindingKey: jsonEncode({'token': _token, 'user_id': 734}),
    _enrollmentKey: 'enrolled',
  };
  bool failFenceWrite = true;
  bool failTokenDelete = false;
  final deletedKeys = <String>[];

  Future<String?> _read(String key) async => values[key];

  Future<void> _write(String key, String value) async {
    if (key == _fenceKey && failFenceWrite) {
      throw StateError('synthetic logout fence write failure');
    }
    values[key] = value;
  }

  Future<void> _delete(String key) async {
    deletedKeys.add(key);
    if (key == _tokenKey && failTokenDelete) {
      throw StateError('synthetic token delete failure');
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
        throw UnsupportedError('Unexpected secure-storage invocation');
    }
  }
}

AuthService _auth(_FailingLogoutStorage storage) => AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/logout') {
          return http.Response('', 204);
        }
        fail('Unexpected synthetic HTTP request: ${request.url.path}');
      }),
    );

Future<Map<String, bool>> _restartedState(_FailingLogoutStorage storage) async {
  final reopened = _auth(storage);
  await reopened.initialize();
  final token = await reopened.getIdToken();
  final scope = await reopened.resolvePatientVaultScope();
  final state = {
    'memoryBearer': reopened.hasRemoteApiCredential,
    'boundAccount': reopened.boundNativeAccountId != null,
    'getIdToken': token != null,
    'patientVaultScope': scope != null,
    'persistedBearer': storage.values.containsKey(_tokenKey),
    'persistedBinding': storage.values.containsKey(_bindingKey),
    'persistedEnrollment': storage.values.containsKey(_enrollmentKey),
  };
  reopened.dispose();
  return state;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 F05A: fence write fails but available deletes still prevent restart',
      () async {
    final storage = _FailingLogoutStorage();
    final auth = _auth(storage);
    await auth.initialize();
    expect(auth.boundNativeAccountId, 734);

    // Local revocation must be immediate even if persistence later fails.
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();

    // A failing marker write is not a reason to skip working key deletions.
    expect(storage.deletedKeys, containsAll(
      [_tokenKey, _bindingKey, _enrollmentKey],
    ));
    final state = await _restartedState(storage);
    expect(state.values.every((value) => !value), isTrue, reason: '$state');
  });

  test('W02 F05B: fence write AND token delete both fail: restart must not revive A',
      () async {
    final storage = _FailingLogoutStorage()..failTokenDelete = true;
    final auth = _auth(storage);
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();

    // This is deliberately a stronger adversarial oracle. If both durable
    // writes and token deletion fail, a client-only approach may be unable
    // to prove crash-safe revocation; keep it RED until a viable mechanism
    // is demonstrated (e.g. independent server-side credential invalidation).
    final state = await _restartedState(storage);
    expect(state.values.every((value) => !value), isTrue, reason: '$state');
  });
}
