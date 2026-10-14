import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

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

}
