import 'dart:async';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _identityKey = 'iamina_native_account_binding_v1';
const _tokenKey = 'iamina_native_access_token';
const _sessionKey = 'iamina_local_session_v1';
const _syntheticToken = 'iamina.e30:1abcde:synthetic_test_signature';

/// Deliberately suspends the *real AuthService's* first credential write.
/// In-memory only: no platform storage, network or patient information.
class _PausedBindingStorage implements FlutterSecureStorage {
  final Map<String, String> values = {};
  final Completer<void> bindingWriteStarted = Completer<void>();
  final Completer<void> _resume = Completer<void>();
  bool _pauseOnce = true;

  void resumeBindingWrite() {
    if (!_resume.isCompleted) _resume.complete();
  }

  Future<void> _write(String key, String value) async {
    if (key == _identityKey && _pauseOnce) {
      _pauseOnce = false;
      bindingWriteStarted.complete();
      await _resume.future;
    }
    values[key] = value;
  }

  Future<void> _delete(String key) async {
    values.remove(key);
  }

  @override
  dynamic noSuchMethod(Invocation invocation) {
    final key = invocation.namedArguments[#key] as String?;
    switch (invocation.memberName) {
      case #read:
        return Future<String?>.value(values[key]);
      case #write:
        return _write(key!, invocation.namedArguments[#value] as String);
      case #delete:
        return _delete(key!);
      default:
        throw UnsupportedError('Unexpected secure-storage method');
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 P0: suspended login A cannot reauthenticate after sign-out',
      () async {
    final storage = _PausedBindingStorage();
    final auth = AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/login') {
          return http.Response(
            '{"access_token":"$_syntheticToken","user":{"id":734}}',
            200,
          );
        }
        if (request.url.path == '/api/v1/auth/logout') {
          return http.Response('', 204);
        }
        fail('Unexpected network request');
      }),
    );
    await auth.initialize();

    // The HTTP login succeeded, but persistence has stopped mid-transaction.
    final pendingLogin = auth.signInWithEmail('a@example.invalid', 'test-only');
    final cancelledLogin = expectLater(pendingLogin, throwsStateError);
    await storage.bindingWriteStarted.future.timeout(
      const Duration(seconds: 5),
    );

    // The logout must retire in-memory access immediately, without waiting
    // for the pending secure-storage operation.
    final pendingLogout = auth.signOut();
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.boundNativeAccountId, isNull);

    storage.resumeBindingWrite();
    await pendingLogout;
    await cancelledLogin;

    // The A binding, token and enrollment marker must stay absent after both
    // operations settle. No account may be resurrected by a stale continuation.
    expect(auth.isAuthenticated, isFalse);
    expect(auth.boundNativeAccountId, isNull);
    expect(await auth.getIdToken(), isNull);
    expect(storage.values[_identityKey], isNull);
    expect(storage.values[_tokenKey], isNull);
    expect(storage.values[_sessionKey], isNull);
    auth.dispose();
  });
}
