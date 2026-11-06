import 'dart:async';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

const _localSessionKey = 'iamina_local_session_v1';
const _nativeIdentityKey = 'iamina_native_account_binding_v1';
const _tokenKey = 'iamina_native_access_token';

/// Memory-only storage that pauses the first *local enrollment marker* write.
/// This exercises the actual AuthService methods, without accounts or PHI.
class _PausedLocalEnrollmentStorage implements FlutterSecureStorage {
  final Map<String, String> values = {};
  final Completer<void> localSessionWriteStarted = Completer<void>();
  final Completer<void> _resumeLocalSessionWrite = Completer<void>();
  bool _paused = false;

  void resumeLocalSessionWrite() {
    if (!_resumeLocalSessionWrite.isCompleted) {
      _resumeLocalSessionWrite.complete();
    }
  }

  Future<void> _write(String key, String value) async {
    if (key == _localSessionKey && !_paused) {
      _paused = true;
      localSessionWriteStarted.complete();
      await _resumeLocalSessionWrite.future;
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

  test('W02 P0: suspended local enrollment cannot reactivate after sign-out',
      () async {
    final storage = _PausedLocalEnrollmentStorage();
    final auth = AuthService(storage: storage);
    await auth.initialize();
    expect(auth.isAuthenticated, isFalse);

    // Local enrollment pauses while persisting its session marker.
    final pendingEnrollment = auth.enrollLocalDevice();
    final rejectedEnrollment = expectLater(
      pendingEnrollment,
      throwsStateError,
    );
    await storage.localSessionWriteStarted.future.timeout(
      const Duration(seconds: 5),
    );

    // Logout must cancel an older enrollment before any suspension resumes.
    final pendingLogout = auth.signOut();
    expect(auth.isAuthenticated, isFalse);
    expect(auth.hasRemoteApiCredential, isFalse);

    // Under a broken implementation, the stale marker and in-memory flag
    // reappear after logout has already cleared secure storage.
    storage.resumeLocalSessionWrite();
    await pendingLogout;
    await rejectedEnrollment;

    expect(auth.isAuthenticated, isFalse);
    expect(auth.boundNativeAccountId, isNull);
    expect(await auth.getIdToken(), isNull);
    expect(await auth.resolvePatientVaultScope(), isNull);
    expect(storage.values[_localSessionKey], isNull);
    expect(storage.values[_nativeIdentityKey], isNull);
    expect(storage.values[_tokenKey], isNull);
    auth.dispose();
  });
}
