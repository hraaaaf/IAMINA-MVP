import 'dart:convert';
import 'dart:io';

import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

const _credentialKey = 'iamina_app_lock_credential_v1';
const _requiredKey = 'iamina_app_lock_required_v1';
const _localSessionKey = 'iamina_local_session_v1';
const _localSessionValue = 'enrolled';

const _credential = AppLockCredential(
  credentialId: 'credential-id',
  publicKeySpki: 'public-key-spki',
  rpId: 'patient.example',
  origin: 'https://patient.example',
  signCount: 4,
);

class _FakeAuthenticator implements AppLockAuthenticator {
  AppLockCapability capabilityValue;
  AppLockCredential enrollmentCredential = _credential;
  AppLockAssertion assertion;
  Object? enrollError;
  Object? unlockError;
  int enrollCalls = 0;
  int unlockCalls = 0;

  _FakeAuthenticator({
    this.capabilityValue = AppLockCapability.supported,
    this.assertion = const AppLockAssertion(signCount: 5),
  });

  @override
  Future<AppLockCapability> capability() async => capabilityValue;

  @override
  Future<AppLockCredential> enroll() async {
    enrollCalls += 1;
    final error = enrollError;
    if (error != null) throw error;
    return enrollmentCredential;
  }

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) async {
    unlockCalls += 1;
    final error = unlockError;
    if (error != null) throw error;
    expect(credential.credentialId, enrollmentCredential.credentialId);
    return assertion;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  void seedStorage(Map<String, String> values) {
    FlutterSecureStorage.setMockInitialValues(values);
  }

  test('fresh installation requires setup and never starts unlocked', () async {
    seedStorage({});
    final service = AppLockService(authenticator: _FakeAuthenticator());

    await service.initialize();

    expect(service.isInitialized, isTrue);
    expect(service.needsSetup, isTrue);
    expect(service.isConfigured, isFalse);
    expect(service.isUnlocked, isFalse);
    expect(service.recoveryRequired, isFalse);
    service.dispose();
  });

  test('missing app-lock state with protected local data enters recovery', () async {
    seedStorage({});
    final service = AppLockService(
      authenticator: _FakeAuthenticator(),
      protectedLocalStateProbe: () async => true,
    );

    await service.initialize();

    expect(service.isRequired, isTrue);
    expect(service.recoveryRequired, isTrue);
    expect(service.needsSetup, isFalse);
    expect(service.isConfigured, isFalse);
    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('protected-state probe failure fails closed into recovery', () async {
    seedStorage({});
    final service = AppLockService(
      authenticator: _FakeAuthenticator(),
      protectedLocalStateProbe: () async => throw StateError('db unavailable'),
    );

    await service.initialize();

    expect(service.isRequired, isTrue);
    expect(service.recoveryRequired, isTrue);
    expect(service.needsSetup, isFalse);
    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('unsupported strong authentication fails closed', () async {
    seedStorage({});
    final authenticator = _FakeAuthenticator(
      capabilityValue: AppLockCapability.unavailable,
    );
    final service = AppLockService(authenticator: authenticator);
    await service.initialize();

    await expectLater(
      service.configure(),
      throwsA(
        isA<AppLockException>().having(
          (error) => error.code,
          'code',
          'strong_auth_unavailable',
        ),
      ),
    );

    expect(service.isConfigured, isFalse);
    expect(service.isUnlocked, isFalse);
    expect(authenticator.enrollCalls, 0);
    expect(await const FlutterSecureStorage().read(key: _credentialKey), isNull);
    expect(await const FlutterSecureStorage().read(key: _requiredKey), isNull);
    service.dispose();
  });

  test('configuration persists credential and required marker before unlock state', () async {
    seedStorage({});
    final service = AppLockService(authenticator: _FakeAuthenticator());
    await service.initialize();

    await service.configure();

    expect(service.isConfigured, isTrue);
    expect(service.isRequired, isTrue);
    expect(service.isUnlocked, isTrue);
    expect(
      await const FlutterSecureStorage().read(key: _credentialKey),
      _credential.encode(),
    );
    expect(
      await const FlutterSecureStorage().read(key: _requiredKey),
      'required',
    );
    service.dispose();
  });

  test('cold boot with a valid credential is configured but locked', () async {
    seedStorage({
      _credentialKey: _credential.encode(),
      _requiredKey: 'required',
    });
    final service = AppLockService(authenticator: _FakeAuthenticator());

    await service.initialize();

    expect(service.isConfigured, isTrue);
    expect(service.isRequired, isTrue);
    expect(service.isUnlocked, isFalse);
    expect(service.recoveryRequired, isFalse);
    service.dispose();
  });

  test('unlock verifies locally then persists new counter before opening', () async {
    seedStorage({
      _credentialKey: _credential.encode(),
      _requiredKey: 'required',
    });
    final authenticator = _FakeAuthenticator(
      assertion: const AppLockAssertion(signCount: 8),
    );
    final service = AppLockService(authenticator: authenticator);
    await service.initialize();

    await service.unlock();

    expect(authenticator.unlockCalls, 1);
    expect(service.isUnlocked, isTrue);
    final persisted = AppLockCredential.decode(
      (await const FlutterSecureStorage().read(key: _credentialKey))!,
    );
    expect(persisted.signCount, 8);
    service.dispose();
  });

  test('cancelled or failed verification never unlocks', () async {
    seedStorage({
      _credentialKey: _credential.encode(),
      _requiredKey: 'required',
    });
    final authenticator = _FakeAuthenticator()
      ..unlockError = const AppLockException('user_cancelled');
    final service = AppLockService(authenticator: authenticator);
    await service.initialize();

    await expectLater(
      service.unlock(),
      throwsA(isA<AppLockException>()),
    );

    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('required marker without credential enters recovery and never setup', () async {
    seedStorage({_requiredKey: 'required'});
    final service = AppLockService(authenticator: _FakeAuthenticator());

    await service.initialize();

    expect(service.recoveryRequired, isTrue);
    expect(service.needsSetup, isFalse);
    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('malformed stored credential enters fail-closed recovery', () async {
    seedStorage({
      _credentialKey: '{"version":1,"credentialId":"tampered"}',
      _requiredKey: 'required',
    });
    final service = AppLockService(authenticator: _FakeAuthenticator());

    await service.initialize();

    expect(service.recoveryRequired, isTrue);
    expect(service.isConfigured, isFalse);
    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('short background interval preserves unlock but timeout relocks', () async {
    seedStorage({});
    var now = DateTime.utc(2026, 9, 16, 12);
    final service = AppLockService(
      authenticator: _FakeAuthenticator(),
      now: () => now,
      gracePeriod: const Duration(seconds: 60),
    );
    await service.initialize();
    await service.configure();

    service.noteBackgrounded();
    now = now.add(const Duration(seconds: 59));
    service.noteResumed();
    expect(service.isUnlocked, isTrue);

    service.noteBackgrounded();
    now = now.add(const Duration(seconds: 60));
    service.noteResumed();
    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('detached lifecycle locks immediately', () async {
    seedStorage({});
    final service = AppLockService(authenticator: _FakeAuthenticator());
    await service.initialize();
    await service.configure();

    service.noteDetached();

    expect(service.isUnlocked, isFalse);
    service.dispose();
  });

  test('explicit local sign-out locks app-lock in the same process', () async {
    seedStorage({_localSessionKey: _localSessionValue});
    final auth = AuthService(
      httpClient: MockClient((request) async {
        fail('Local-only sign-out without bearer must not call the network');
      }),
    );
    await auth.initialize();
    expect(auth.isAuthenticated, isTrue);

    final lock = AppLockService(
      authenticator: _FakeAuthenticator(),
      authService: auth,
    );
    await lock.initialize();
    await lock.configure();
    expect(lock.isUnlocked, isTrue);

    await auth.signOut();

    expect(auth.isAuthenticated, isFalse);
    expect(lock.isUnlocked, isFalse);
    lock.dispose();
    auth.dispose();
  });

  test('credential parser rejects insecure non-loopback origins', () {
    final payload = _credential.toJson()
      ..['origin'] = 'http://patient.example';

    expect(
      () => AppLockCredential.decode(jsonEncode(payload)),
      throwsFormatException,
    );
  });

  test('secure persistence precedes public unlocked state in source', () {
    final source = File('lib/services/app_lock_service.dart').readAsStringSync();

    final configureStart = source.indexOf('Future<void> configure()');
    final configureWrite = source.indexOf(
      'await _storage.write(key: _requiredKey, value: _requiredValue);',
      configureStart,
    );
    final configureUnlock = source.indexOf('_unlocked = true;', configureStart);
    expect(configureWrite, greaterThan(configureStart));
    expect(configureUnlock, greaterThan(configureWrite));

    final unlockStart = source.indexOf('Future<void> unlock()');
    final unlockWrite = source.indexOf(
      'await _storage.write(key: _credentialKey, value: updated.encode());',
      unlockStart,
    );
    final unlockState = source.indexOf('_unlocked = true;', unlockStart);
    expect(unlockWrite, greaterThan(unlockStart));
    expect(unlockState, greaterThan(unlockWrite));
  });
}
