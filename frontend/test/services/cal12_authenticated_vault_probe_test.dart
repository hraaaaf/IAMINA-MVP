import 'dart:async';
import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/app_lock_authenticator.dart';
import 'package:amina/services/app_lock_service.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/cal12_authenticated_vault_probe.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const aToken = 'iamina.syntheticA:123abc:fixture_A';
const bToken = 'iamina.syntheticB:123abd:fixture_B';

class _FixtureAuthenticator implements AppLockAuthenticator {
  static const credential = AppLockCredential(
    credentialId: 'cal12-fixture-credential',
    publicKeySpki: 'cal12-fixture-public-key',
    rpId: 'localhost',
    origin: 'http://localhost',
    signCount: 1,
  );

  @override
  Future<AppLockCapability> capability() async => AppLockCapability.supported;

  @override
  Future<AppLockCredential> enroll() async => credential;

  @override
  Future<AppLockAssertion> unlock(AppLockCredential credential) async =>
      const AppLockAssertion(signCount: 2);
}

http.Client fixtureHttpClient() => MockClient((request) async {
      if (request.url.path == '/api/v1/auth/logout') {
        return http.Response('', 204);
      }
      if (request.url.path != '/api/v1/auth/login') {
        fail('CAL12 unexpected HTTP endpoint');
      }
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      final isA = body['email'] == 'a@example.invalid';
      if (!isA && body['email'] != 'b@example.invalid') {
        fail('CAL12 unexpected synthetic account');
      }
      return http.Response(
        jsonEncode({
          'access_token': isA ? aToken : bToken,
          'user': {'id': isA ? 734 : 812},
        }),
        200,
        headers: const {'content-type': 'application/json'},
      );
    });

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthService auth;
  late AppLockService lock;
  late PatientVaultSessionController vault;

  setUp(() async {
    FlutterSecureStorage.setMockInitialValues({});
    auth = AuthService(httpClient: fixtureHttpClient());
    await auth.initialize();
    lock = AppLockService(
      authService: auth,
      authenticator: _FixtureAuthenticator(),
      protectedLocalStateProbe: () async => false,
    );
    await lock.initialize();
    vault = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: auth.resolvePatientVaultScope,
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
    );
    await vault.reconcile();
  });

  tearDown(() {
    vault.dispose();
    lock.dispose();
    auth.dispose();
  });

  Future<void> login(String email) async {
    await auth.signInWithEmail(email, 'cal12-fictional-password');
    await vault.reconcile();
  }

  Cal12AuthenticatedVaultProbe? capture() =>
      Cal12AuthenticatedVaultProbe.tryCapture(
        auth: auth,
        vault: vault,
        appLock: lock,
      );

  test('CAL12 no login, local device, audit and no lock are denied', () async {
    expect(Cal12AuthenticatedVaultProbe.realPatientExportEnabled, isFalse);
    expect(capture(), isNull);
    await auth.enrollLocalDevice();
    await vault.reconcile();
    expect(capture(), isNull);
    await auth.signOut();
    auth.enterAuditSession();
    await vault.reconcile();
    expect(capture(), isNull);
  });

  test('CAL12 current Django account opens matching physical vault only',
      () async {
    await login('a@example.invalid');
    expect(auth.isRemoteCredentialVerified, isTrue);
    expect(vault.activeScope?.nativeDjangoUserId, 734);
    expect(vault.activeDatabase, isNotNull);
    expect(capture(), isNull);
    await lock.configure();
    final bound = capture();
    expect(bound, isNotNull);
    expect(bound!.isCurrent, isTrue);
    bound.retire();
    expect(bound.isCurrent, isFalse);
  });

  test('CAL12 locking irreversibly revokes even after unlocking', () async {
    await login('a@example.invalid');
    await lock.configure();
    final bound = capture()!;
    lock.lock();
    expect(bound.isCurrent, isFalse);
    await lock.unlock();
    expect(bound.isCurrent, isFalse);
    final fresh = capture();
    expect(fresh?.isCurrent, isTrue);
    fresh?.retire();
  });

  test('CAL12 A logout B login A and same-owner relogin expire snapshots',
      () async {
    await login('a@example.invalid');
    await lock.configure();
    final oldA = capture()!;
    final signOut = auth.signOut();
    expect(oldA.isCurrent, isFalse);
    await signOut;
    await vault.reconcile();
    expect(capture(), isNull);
    await login('b@example.invalid');
    await lock.unlock();
    expect(vault.activeScope?.nativeDjangoUserId, 812);
    final oldB = capture()!;
    expect(oldB.isCurrent, isTrue);
    await auth.signOut();
    await login('a@example.invalid');
    await lock.unlock();
    expect(vault.activeScope?.nativeDjangoUserId, 734);
    expect(oldA.isCurrent, isFalse);
    expect(oldB.isCurrent, isFalse);
    final freshA = capture()!;
    expect(freshA.isCurrent, isTrue);
    await auth.signOut();
    await login('a@example.invalid');
    await lock.unlock();
    expect(freshA.isCurrent, isFalse);
    final again = capture()!;
    expect(again.isCurrent, isTrue);
    again.retire();
  });

  test('CAL12 mismatched open vault owner denies current native account',
      () async {
    await login('a@example.invalid');
    await lock.configure();
    final wrong = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => PatientVaultScope.nativeDjango(812),
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
    );
    addTearDown(wrong.dispose);
    await wrong.reconcile();
    expect(wrong.activeScope?.nativeDjangoUserId, 812);
    expect(
      Cal12AuthenticatedVaultProbe.tryCapture(
        auth: auth,
        vault: wrong,
        appLock: lock,
      ),
      isNull,
    );
    final correct = capture()!;
    expect(correct.isCurrent, isTrue);
    correct.retire();
  });

  test('CAL12 async transition denies stale work before inspection',
      () async {
    await login('a@example.invalid');
    await lock.configure();
    final bound = capture()!;
    final pending = Completer<void>();
    var inspected = false;
    Future<void> afterAwait() async {
      await pending.future;
      if (!bound.isCurrent) throw StateError('CAL12_STALE_SESSION');
      inspected = true;
    }

    final operation = afterAwait();
    AuthEpoch.advance();
    pending.complete();
    await expectLater(operation, throwsStateError);
    expect(inspected, isFalse);
    expect(bound.isCurrent, isFalse);
  });

  test('CAL12 cached native bearer restores vault but not live login proof',
      () async {
    FlutterSecureStorage.setMockInitialValues({
      'iamina_native_access_token': aToken,
      'iamina_native_account_binding_v1':
          jsonEncode({'token': aToken, 'user_id': 734}),
    });
    final restored = AuthService(
      httpClient: MockClient((_) async {
        fail('No external network during offline restoration');
      }),
    );
    await restored.initialize();
    final rvault = PatientVaultSessionController(
      authChanges: restored,
      resolveScope: restored.resolvePatientVaultScope,
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
    );
    final rlock = AppLockService(
      authService: restored,
      authenticator: _FixtureAuthenticator(),
      protectedLocalStateProbe: () async => false,
    );
    await rlock.initialize();
    await rlock.configure();
    await rvault.reconcile();
    expect(restored.boundNativeAccountId, 734);
    expect(restored.isRemoteCredentialVerified, isFalse);
    expect(rvault.activeScope?.nativeDjangoUserId, 734);
    expect(
      Cal12AuthenticatedVaultProbe.tryCapture(
        auth: restored,
        vault: rvault,
        appLock: rlock,
      ),
      isNull,
    );
    rvault.dispose();
    rlock.dispose();
    restored.dispose();
  });
}
