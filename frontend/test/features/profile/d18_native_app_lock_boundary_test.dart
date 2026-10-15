import 'dart:async';

import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

const _credential = AppLockCredential(
  credentialId: 'native-bio-v1-123e4567-e89b-42d3-a456-426614174000',
  publicKeySpki: 'synthetic-test-spki',
  rpId: 'ma.iamina.app',
  origin: 'https://native.iamina.invalid',
  signCount: 0,
);

class _DelayedAuthenticator implements AppLockAuthenticator {
  final Completer<AppLockAssertion> unlockCompleter =
      Completer<AppLockAssertion>();
  final Completer<AppLockCredential> enrollCompleter =
      Completer<AppLockCredential>();
  @override
  Future<AppLockCapability> capability() async => AppLockCapability.supported;
  @override
  Future<AppLockCredential> enroll() => enrollCompleter.future;
  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) =>
      unlockCompleter.future;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D18 app lock never unlocks a new patient after interrupted native proof',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_app_lock_credential_v1': _credential.encode(),
      'iamina_app_lock_required_v1': 'required',
    });
    final native = _DelayedAuthenticator();
    final lock = AppLockService(authenticator: native);
    addTearDown(lock.dispose);
    await lock.initialize();
    expect(lock.isUnlocked, isFalse);

    final inFlight = lock.unlock();
    // Auth epoch changes as A is retired; app-lock also receives lock() from
    // main.dart even when the old instance is already locked.
    AuthEpoch.advance();
    lock.lock();
    native.unlockCompleter.complete(const AppLockAssertion(signCount: 1));
    await expectLater(inFlight, throwsA(isA<AppLockException>().having(
      (error) => error.code, 'code', 'auth_context_changed',
    )));
    expect(lock.isUnlocked, isFalse);
  });

  test('D18 app lock cannot publish enrollment after account transition',
      () async {
    FlutterSecureStorage.setMockInitialValues({});
    final native = _DelayedAuthenticator();
    final lock = AppLockService(authenticator: native);
    addTearDown(lock.dispose);
    await lock.initialize();

    final enrollment = lock.configure();
    // Ensure the async capability() has resumed and enroll() was entered.
    await Future<void>.delayed(Duration.zero);
    AuthEpoch.advance();
    lock.lock();
    native.enrollCompleter.complete(_credential);
    await expectLater(enrollment, throwsA(isA<AppLockException>().having(
      (error) => error.code, 'code', 'auth_context_changed',
    )));
    expect(lock.isUnlocked, isFalse);
    expect(lock.isConfigured, isFalse);
  });
}
