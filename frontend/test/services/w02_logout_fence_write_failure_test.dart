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
const _revokedToken = 'iamina_logout_revoked_token_v1';

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
  bool ignoreTokenDelete = false;
  bool failTokenTombstoneWrite = false;
  final deletedKeys = <String>[];

  Future<String?> _read(String key) async => values[key];

  Future<void> _write(String key, String value) async {
    if (key == _fenceKey && failFenceWrite) {
      throw StateError('synthetic logout fence write failure');
    }
    if (key == _tokenKey && value == _revokedToken &&
        failTokenTombstoneWrite) {
      throw StateError('synthetic bearer tombstone write failure');
    }
    values[key] = value;
  }

  Future<void> _delete(String key) async {
    deletedKeys.add(key);
    if (key == _tokenKey && failTokenDelete) {
      throw StateError('synthetic token delete failure');
    }
    if (key == _tokenKey && ignoreTokenDelete) {
      return; // Silent false-success deletion: read-back must catch it.
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
    // "Persisted bearer" is an authentic raw credential, not mere presence
    // of a deliberately non-bearer revocation sentinel in the same slot.
    'persistedBearer': storage.values[_tokenKey] == _token,
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

  test('W02 F05B-SILENT: delete returning success without removal is not safe',
      () async {
    final storage = _FailingLogoutStorage()
      ..failFenceWrite = false
      ..ignoreTokenDelete = true;
    final auth = _auth(storage);
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isTrue);
    auth.dispose();

    // An unverified delete must never be considered physical erasure.
    // The independently verified tombstone removes old bearer bytes.
    expect(storage.values.containsKey(_tokenKey), isTrue);
    expect(storage.values[_tokenKey], _revokedToken);
    final state = await _restartedState(storage);
    expect(state.values.every((value) => !value), isTrue, reason: '$state');
  });

  test('W02 F05D: pending fence survives silent deletion across two restarts',
      () async {
    final storage = _FailingLogoutStorage()
      ..failFenceWrite = false
      ..ignoreTokenDelete = true
      ..failTokenTombstoneWrite = true;
    final auth = _auth(storage);
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();

    // Both a "successful" no-op delete and tombstone overwrite refusal
    // mean RAW bearer remains. The successful original fence MUST survive.
    expect(storage.values[_tokenKey], _token);
    expect(storage.values[_fenceKey], 'revoked');
    final first = await _restartedState(storage);
    expect(first['memoryBearer'], isFalse);
    expect(first['getIdToken'], isFalse);
    expect(first['patientVaultScope'], isFalse);
    expect(storage.values[_fenceKey], 'revoked');

    // The prior initialize must not clear the fence and authorize this
    // original bearer on the next native-process cold boot.
    final second = await _restartedState(storage);
    expect(second['memoryBearer'], isFalse);
    expect(second['getIdToken'], isFalse);
    expect(second['patientVaultScope'], isFalse);
    expect(storage.values[_fenceKey], 'revoked');
  });

  test('W02 F05B-OFFLINE: verified tombstone prevents cold restart without server',
      () async {
    final storage = _FailingLogoutStorage()..failTokenDelete = true;
    final auth = AuthService(
      storage: storage,
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/auth/logout');
        throw http.ClientException('synthetic network unavailable', request.url);
      }),
    );
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isFalse);
    auth.dispose();

    expect(storage.values[_tokenKey], _revokedToken,
        reason: 'No successful network call can replace local cold-boot denial');
    final state = await _restartedState(storage);
    expect(state.values.every((value) => !value), isTrue, reason: '$state');
  });

  test('W02 F05C: if token overwrite also fails, logout reports NO-GO',
      () async {
    final storage = _FailingLogoutStorage()
      ..failTokenDelete = true
      ..failTokenTombstoneWrite = true;
    final auth = _auth(storage);
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    expect(auth.lastRemoteLogoutConfirmed, isTrue);
    auth.dispose();

    // This is a captured UNSOLVED physical-storage failure. The old
    // secret remains in hostile storage; even HTTP 204 revocation does not
    // make local erasure true. Do NOT certify this as safe offline or for
    // the native-platform persistent hydration path.
    expect(storage.values[_tokenKey], _token);
    expect(storage.values.containsKey(_bindingKey), isFalse);
    expect(storage.values.containsKey(_enrollmentKey), isFalse);
  });

  test('W02 F05B: fence write AND token delete both fail: restart must not revive A',
      () async {
    final storage = _FailingLogoutStorage()..failTokenDelete = true;
    final auth = _auth(storage);
    await auth.initialize();
    await expectLater(auth.signOut(), throwsStateError);
    expect(auth.hasRemoteApiCredential, isFalse);
    auth.dispose();

    // The injected deletion fault makes PHYSICAL key removal impossible.
    // Require instead that the old secret bytes are overwritten, read back
    // as a non-bearer, and NEVER published after process restart. Do not
    // mislabel this as physical erasure or independently confirmed server
    // revocation; those are separate gates.
    expect(storage.values.containsKey(_tokenKey), isTrue,
        reason: 'The injected token deletion fault is still active');
    expect(storage.values[_tokenKey], _revokedToken);
    final state = await _restartedState(storage);
    expect(state.values.every((value) => !value), isTrue, reason: '$state');
  });
}
