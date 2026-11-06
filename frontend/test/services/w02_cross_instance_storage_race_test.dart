import 'dart:async';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _identityKey = 'iamina_native_account_binding_v1';
const _tokenKey = 'iamina_native_access_token';
const _sessionKey = 'iamina_local_session_v1';
const _syntheticToken = 'iamina.e30:1abcde:cross_instance_test_signature';

/// Two independent AuthService objects share exactly one in-memory storage
/// backend. The first A credential write pauses until a different service
/// has already issued sign-out. No real browser, platform keys or PHI.
class _SharedPausedBindingStorage implements FlutterSecureStorage {
  final values = <String, String>{};
  final bindingWriteStarted = Completer<void>();
  final _resumeBindingWrite = Completer<void>();
  bool _pauseOnce = true;

  void resumeBindingWrite() {
    if (!_resumeBindingWrite.isCompleted) _resumeBindingWrite.complete();
  }

  Future<void> _write(String key, String value) async {
    if (key == _identityKey && _pauseOnce) {
      _pauseOnce = false;
      bindingWriteStarted.complete();
      await _resumeBindingWrite.future;
    }
    values[key] = value;
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
        values.remove(key);
        return Future<void>.value();
      default:
        throw UnsupportedError('Unexpected secure-storage method');
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 P0: second AuthService logout cancels suspended first instance login',
      () async {
    final storage = _SharedPausedBindingStorage();
    final first = AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/login') {
          return http.Response(
            '{"access_token":"$_syntheticToken","user":{"id":734}}',
            200,
          );
        }
        fail('Unexpected synthetic network request: ${request.url.path}');
      }),
    );
    final second = AuthService(storage: storage);
    await first.initialize();
    await second.initialize();

    // A successful HTTP login in instance 1 pauses before its very first
    // secure-storage binding write is allowed to finish.
    final pendingLogin = first.signInWithEmail('a@example.invalid', 'test-only');
    final rejectedLogin = expectLater(pendingLogin, throwsStateError);
    await storage.bindingWriteStarted.future.timeout(const Duration(seconds: 5));

    // Different AuthService instance, same persistence, later logout intent.
    // Instance-scoped queues/intent counters cannot order these operations.
    final pendingLogout = second.signOut();
    expect(second.isAuthenticated, isFalse);
    expect(second.hasRemoteApiCredential, isFalse);

    storage.resumeBindingWrite();
    await pendingLogout;
    await rejectedLogin;

    // No stale A identity, token or local enrollment may be published by
    // either instance, nor remain cached after the newer logout has settled.
    expect(first.isAuthenticated, isFalse);
    expect(first.hasRemoteApiCredential, isFalse);
    expect(first.boundNativeAccountId, isNull);
    expect(await first.getIdToken(), isNull);
    expect(second.isAuthenticated, isFalse);
    expect(await second.resolvePatientVaultScope(), isNull);
    expect(storage.values[_identityKey], isNull);
    expect(storage.values[_tokenKey], isNull);
    expect(storage.values[_sessionKey], isNull);

    first.dispose();
    second.dispose();
  });
}
