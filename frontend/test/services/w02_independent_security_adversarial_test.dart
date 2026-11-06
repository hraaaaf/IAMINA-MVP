import 'dart:async';
import 'dart:convert';

import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _tokenKey = 'iamina_native_access_token';
const _bindingKey = 'iamina_native_account_binding_v1';
const _localKey = 'iamina_local_session_v1';
const _deviceKey = 'iamina_local_device_id_v1';
const _tokenA = 'iamina.e30:1abcde:audit_synthetic_signature';
const _deviceId = '123e4567-e89b-42d3-a456-426614174000';

class _AuditStorage implements FlutterSecureStorage {
  final values = <String, String>{};
  bool pauseDeviceRead = false;
  bool pauseBindingRead = false;
  bool failNextTokenDelete = false;
  final deviceReadStarted = Completer<void>();
  final bindingReadStarted = Completer<void>();
  final _releaseDeviceRead = Completer<void>();
  final _releaseBindingRead = Completer<void>();
  bool _devicePausedOnce = false;
  bool _bindingPausedOnce = false;

  void releaseDeviceRead() {
    if (!_releaseDeviceRead.isCompleted) _releaseDeviceRead.complete();
  }

  void releaseBindingRead() {
    if (!_releaseBindingRead.isCompleted) _releaseBindingRead.complete();
  }

  Future<String?> _read(String key) async {
    // Snapshot before waiting, as a secure-storage plugin call can return
    // a value read before another instance changes persistent state.
    final snapshot = values[key];
    if (key == _deviceKey && pauseDeviceRead && !_devicePausedOnce) {
      _devicePausedOnce = true;
      deviceReadStarted.complete();
      await _releaseDeviceRead.future;
    }
    if (key == _bindingKey && pauseBindingRead && !_bindingPausedOnce) {
      _bindingPausedOnce = true;
      bindingReadStarted.complete();
      await _releaseBindingRead.future;
    }
    return snapshot;
  }

  Future<void> _write(String key, String value) async {
    values[key] = value;
  }

  Future<void> _delete(String key) async {
    if (key == _tokenKey && failNextTokenDelete) {
      failNextTokenDelete = false;
      throw StateError('synthetic secure storage deletion failure');
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

AuthService _service(_AuditStorage storage) => AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/auth/logout') {
          return http.Response('', 204);
        }
        fail('Unexpected external request: ${request.url.path}');
      }),
    );

void _seedAuthenticatedA(_AuditStorage storage) {
  storage.values[_tokenKey] = _tokenA;
  storage.values[_bindingKey] = jsonEncode({
    'token': _tokenA,
    'user_id': 734,
  });
  storage.values[_localKey] = 'enrolled';
  storage.values[_deviceKey] = _deviceId;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AUDIT RED 1: sibling signOut revokes an already-authenticated instance',
      () async {
    final storage = _AuditStorage();
    _seedAuthenticatedA(storage);
    final first = _service(storage);
    final second = _service(storage);
    await first.initialize();
    await second.initialize();
    expect(first.boundNativeAccountId, 734);
    expect(await first.getIdToken(), _tokenA);

    await second.signOut();

    // A logout is a global revocation, not just cancellation of pending writes.
    expect(first.hasRemoteApiCredential, isFalse);
    expect(first.boundNativeAccountId, isNull);
    expect(await first.getIdToken(), isNull);
    expect(await first.resolvePatientVaultScope(), isNull);
    expect(storage.values[_tokenKey], isNull);
    expect(storage.values[_bindingKey], isNull);
    first.dispose();
    second.dispose();
  });

  test('AUDIT RED 2: vault lookup started pre-logout cannot publish post-logout',
      () async {
    final storage = _AuditStorage();
    final auth = _service(storage);
    await auth.initialize();
    await auth.enrollLocalDevice();
    storage.pauseDeviceRead = true;

    final pendingScope = auth.resolvePatientVaultScope();
    await storage.deviceReadStarted.future.timeout(const Duration(seconds: 5));
    await auth.signOut();
    expect(auth.isAuthenticated, isFalse);

    storage.releaseDeviceRead();
    final resolved = await pendingScope;
    expect(resolved, isNull,
        reason: 'A pre-logout device read must not grant a revoked vault');
    auth.dispose();
  });

  test('AUDIT RED 3: initialize suspended on stale binding cannot undo logout',
      () async {
    final storage = _AuditStorage()..pauseBindingRead = true;
    _seedAuthenticatedA(storage);
    // Force re-enrollment path after initialize() resumes.
    storage.values.remove(_localKey);
    final auth = _service(storage);

    final pendingInit = auth.initialize();
    await storage.bindingReadStarted.future.timeout(const Duration(seconds: 5));
    await auth.signOut();
    expect(auth.hasRemoteApiCredential, isFalse);

    storage.releaseBindingRead();
    await pendingInit;
    expect(auth.isAuthenticated, isFalse,
        reason: 'Old initialize continuation must not re-enroll after logout');
    expect(await auth.resolvePatientVaultScope(), isNull);
    expect(storage.values[_localKey], isNull);
    auth.dispose();
  });

  test('AUDIT RED 4: secure-storage deletion failure cannot revive A at restart',
      () async {
    final storage = _AuditStorage();
    _seedAuthenticatedA(storage);
    final current = _service(storage);
    await current.initialize();
    storage.failNextTokenDelete = true;

    await expectLater(current.signOut(), throwsStateError);
    expect(current.hasRemoteApiCredential, isFalse);
    current.dispose();

    final reopened = _service(storage);
    await reopened.initialize();
    expect(reopened.boundNativeAccountId, isNull,
        reason: 'Failed logout must leave a durable revocation fence');
    expect(await reopened.getIdToken(), isNull);
    expect(await reopened.resolvePatientVaultScope(), isNull);
    reopened.dispose();
  });
}
