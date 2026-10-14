import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:amina/services/sync_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _D9NoRemoteAuth extends Mock implements AuthService {}

class _D9SessionNotifier extends ChangeNotifier {
  void switched() => notifyListeners();
}

bool _requiresFirstUse(ConsentService consent) =>
    shouldApplyOnboardingGate(
      isLoggedIn: true,
      isAnonymous: false,
      requiresHostedRemoteLogin: false,
      hasCompletedOnboarding: consent.hasCompletedOnboarding,
      hasProfileState: consent.isInitialized,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D9 and D7: A-B-A restores each local first-use state without borrowing consent',
      () async {
    // Synthetic Django IDs and on-disk vaults. This is NOT a remote-login,
    // multi-device hydration, or production-authentication certification.
    final folder = await Directory.systemTemp.createTemp('iamina-d9-d7-');
    addTearDown(() => folder.delete(recursive: true));
    final auth = _D9SessionNotifier();
    addTearDown(auth.dispose);
    var owner = 734;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => PatientVaultScope.nativeDjango(owner),
      openDatabase: (scope) => AppDatabase.testPatientVault(
        NativeDatabase(File('${folder.path}/${scope.databaseName}.sqlite')),
        scope,
      ),
    );
    addTearDown(controller.dispose);

    await controller.reconcile();
    final dbA = controller.activeDatabase!;
    expect(dbA.activeProfileRowId, 734);
    expect(await dbA.getProfileForLocalUserId(734), isNull);

    final firstA = ConsentService()
      ..seedInitialProfile(await dbA.getProfileForLocalUserId(734));
    expect(_requiresFirstUse(firstA), isTrue);
    expect(firstA.hasConsent, isFalse);
    firstA.dispose();

    // D7 deliberately makes clinical declarations optional. Persisting the
    // first-use profile (without diagnosis or treatment) must not repeat
    // onboarding for the same authenticated local patient on return.
    await dbA.into(dbA.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(dbA.activeProfileRowId),
        updatedAt: DateTime.utc(2026, 10, 14),
        aiConsentGivenAt: drift.Value(DateTime.utc(2026, 10, 13)),
      ),
    );
    final savedA = await dbA.getProfileForLocalUserId(734);
    expect(savedA?.diabetesType, isNull);
    expect(savedA?.treatment, isNull);
    final afterA = ConsentService()..seedInitialProfile(savedA);
    expect(_requiresFirstUse(afterA), isFalse);
    // A historic local timestamp is never enough to authorize AI.
    expect(afterA.hasConsent, isFalse);
    afterA.dispose();

    owner = 812;
    AuthEpoch.advance();
    auth.switched();
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    final dbB = controller.activeDatabase!;
    expect(dbB.activeProfileRowId, 812);
    expect(await dbB.getProfileForLocalUserId(812), isNull);
    expect(await dbB.select(dbB.patientProfiles).get(), isEmpty);
    final firstB = ConsentService()
      ..seedInitialProfile(await dbB.getProfileForLocalUserId(812));
    expect(_requiresFirstUse(firstB), isTrue);
    expect(firstB.hasConsent, isFalse);
    firstB.dispose();

    await dbB.into(dbB.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(dbB.activeProfileRowId),
        updatedAt: DateTime.utc(2026, 10, 14),
        diabetesType: const drift.Value('type2'),
      ),
    );
    final savedB = await dbB.getProfileForLocalUserId(812);
    final afterB = ConsentService()..seedInitialProfile(savedB);
    expect(_requiresFirstUse(afterB), isFalse);
    expect(afterB.hasConsent, isFalse);
    afterB.dispose();

    owner = 734;
    AuthEpoch.advance();
    auth.switched();
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    final restored = controller.activeDatabase!;
    expect(restored.activeProfileRowId, 734);
    final restoredA = await restored.getProfileForLocalUserId(734);
    expect(restoredA, isNotNull);
    expect(restoredA?.diabetesType, isNull);
    expect(restoredA?.treatment, isNull);
    expect(await restored.getProfileForLocalUserId(812), isNull);
    final consentA = ConsentService()..seedInitialProfile(restoredA);
    expect(_requiresFirstUse(consentA), isFalse);
    expect(consentA.hasConsent, isFalse);
    consentA.dispose();
  });

  test('D9 gap: same verified account on another fresh device has no local first-use proof',
      () async {
    // NEGATIVE CAPABILITY EVIDENCE, NOT AN ACCEPTANCE TEST for remote restore:
    // the per-device vault cannot reconstruct an existing remote profile.
    // Cross-device D9 requires a separately authenticated, owner-scoped
    // hydration contract before the onboarding redirect is decided.
    final deviceA = await Directory.systemTemp.createTemp('iamina-d9-phone-a-');
    final deviceB = await Directory.systemTemp.createTemp('iamina-d9-phone-b-');
    addTearDown(() => deviceA.delete(recursive: true));
    addTearDown(() => deviceB.delete(recursive: true));
    final scope = PatientVaultScope.nativeDjango(734);
    final dbA = AppDatabase.testPatientVault(
      NativeDatabase(File('${deviceA.path}/${scope.databaseName}.sqlite')),
      scope,
    );
    final dbB = AppDatabase.testPatientVault(
      NativeDatabase(File('${deviceB.path}/${scope.databaseName}.sqlite')),
      scope,
    );
    addTearDown(dbA.close);
    addTearDown(dbB.close);

    await dbA.into(dbA.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: drift.Value(dbA.activeProfileRowId),
        updatedAt: DateTime.utc(2026, 10, 14),
      ),
    );
    final original = await dbA.getProfileForLocalUserId(734);
    final originalConsent = ConsentService()..seedInitialProfile(original);
    expect(_requiresFirstUse(originalConsent), isFalse);
    originalConsent.dispose();

    // Same authenticated server ID, different physical installation.
    // No remote download is implemented in this local-only gate.
    final newDevice = await dbB.getProfileForLocalUserId(734);
    expect(newDevice, isNull);
    final freshConsent = ConsentService()
      ..seedInitialProfile(newDevice);
    expect(_requiresFirstUse(freshConsent), isTrue);
    expect(freshConsent.hasConsent, isFalse);
    freshConsent.dispose();
  });


  test('D9 cold local restart keeps A outbox pending, never exposes it to B or syncs',
      () async {
    // Two synthetic on-disk vaults, but only ONE host. This is a close/reopen
    // of SQLite under denied transport, NOT a physical-device certification.
    final folder = await Directory.systemTemp.createTemp('iamina-d9-cold-');
    addTearDown(() => folder.delete(recursive: true));
    final a = PatientVaultScope.nativeDjango(734);
    final b = PatientVaultScope.nativeDjango(812);
    final pathA = '${folder.path}/${a.databaseName}.sqlite';
    final pathB = '${folder.path}/${b.databaseName}.sqlite';

    final initialA = AppDatabase.testPatientVault(
      NativeDatabase(File(pathA)), a,
    );
    await initialA.into(initialA.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 14),
        aiConsentGivenAt: drift.Value(DateTime.utc(2026, 10, 13)),
      ),
    );
    await PatientTreatmentDeclarationStore(initialA).write(
      state: 'declared', codes: ['insulin', 'lifestyle'],
    );
    await initialA.into(initialA.logEntries).insert(
      LogEntriesCompanion.insert(
        bloodSugar: 112,
        clientUuid: 'd9-synthetic-a-offline-1',
      ),
    );
    expect((await PatientTreatmentDeclarationStore(initialA).read())?.syncStatus,
        'pending');
    expect((await initialA.getPendingLogs()).length, 1);
    // Actually close all SQLite handles before trying to read the files again.
    await initialA.close();

    final databaseB = AppDatabase.testPatientVault(
      NativeDatabase(File(pathB)), b,
    );
    expect(await databaseB.getProfileForLocalUserId(812), isNull);
    expect(await databaseB.getPendingLogs(), isEmpty);
    expect(await PatientTreatmentDeclarationStore(databaseB).read(), isNull);
    await databaseB.into(databaseB.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(812),
        updatedAt: DateTime.utc(2026, 10, 14),
        diabetesType: const drift.Value('type2'),
      ),
    );
    await PatientTreatmentDeclarationStore(databaseB).write(
      state: 'declared', codes: ['oral_meds'],
    );
    await databaseB.close();

    final coldA = AppDatabase.testPatientVault(
      NativeDatabase(File(pathA)), a,
    );
    addTearDown(coldA.close);
    final restored = await coldA.getProfileForLocalUserId(734);
    expect(restored, isNotNull);
    expect(restored?.diabetesType, isNull);
    final consent = ConsentService()..seedInitialProfile(restored);
    addTearDown(consent.dispose);
    expect(_requiresFirstUse(consent), isFalse);
    expect(consent.hasConsent, isFalse,
        reason: 'A historic timestamp without proof must not grant consent');

    final store = PatientTreatmentDeclarationStore(coldA);
    final pendingBefore = await store.read();
    expect(pendingBefore?.ownerId, 734);
    expect(pendingBefore?.codes, ['insulin', 'lifestyle']);
    expect(pendingBefore?.syncStatus, 'pending');
    final logBefore = await coldA.getPendingLogs();
    expect(logBefore.map((x) => x.clientUuid).toList(),
        ['d9-synthetic-a-offline-1']);
    expect(logBefore.single.syncAttempts, 0);
    expect(await coldA.getProfileForLocalUserId(812), isNull);

    // Simulate an offline/local-only cold launch, including explicit retry.
    final auth = _D9NoRemoteAuth();
    final api = ApiClient(authService: auth);
    expect(api.canSyncClinicalData, isFalse);
    final sync = SyncService(coldA, api);
    addTearDown(sync.dispose);
    sync.init();
    await sync.resumeAfterUnlock();
    await sync.refreshState();
    await sync.syncPendingLogs();
    expect(await sync.sendPendingTreatmentDeclaration(), isFalse);
    await sync.restorePatientTreatmentDeclaration();

    expect(sync.state.value, SyncUiState.localOnly);
    expect((await store.read())?.localGeneration, pendingBefore?.localGeneration);
    expect((await store.read())?.syncStatus, 'pending');
    final logAfter = await coldA.getPendingLogs();
    expect(logAfter.map((x) => x.clientUuid).toList(),
        ['d9-synthetic-a-offline-1']);
    expect(logAfter.single.syncAttempts, 0);
    verifyNever(() => auth.getIdToken());

    final coldB = AppDatabase.testPatientVault(
      NativeDatabase(File(pathB)), b,
    );
    addTearDown(coldB.close);
    expect((await PatientTreatmentDeclarationStore(coldB).read())?.codes,
        ['oral_meds']);
    expect(await coldB.getPendingLogs(), isEmpty);
    expect(await coldB.getProfileForLocalUserId(734), isNull);
  });

}
