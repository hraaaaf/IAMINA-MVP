import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D9 existing complete account never repeats onboarding', () async {
    final db = AppDatabase(NativeDatabase.memory());
    final consent = ConsentService();
    addTearDown(db.close);
    addTearDown(consent.dispose);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        preferredLanguage: const drift.Value('fr'),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
      ),
    );
    consent.seedInitialProfile(
      await db.select(db.patientProfiles).getSingleOrNull(),
    );
    expect(consent.hasCompletedOnboarding, isTrue);
    expect(consent.isInitialized, isTrue);
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: consent.hasCompletedOnboarding,
        hasProfileState: consent.isInitialized,
      ),
      isFalse,
    );
    expect(consent.hasConsent, isFalse);
    expect(
      shouldApplyConsentGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasConsentService: true,
      ),
      isTrue,
    );
  });

  test('D9 incomplete or unavailable session profiles do not bypass gate', () {
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true, isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: false, hasProfileState: true,
      ), isTrue,
    );
    for (final scenario in [(false, false, false, true),
                            (true, true, false, true),
                            (true, false, true, true),
                            (true, false, false, false)]) {
      expect(
        shouldApplyOnboardingGate(
          isLoggedIn: scenario.$1, isAnonymous: scenario.$2,
          requiresHostedRemoteLogin: scenario.$3,
          hasCompletedOnboarding: false, hasProfileState: scenario.$4,
        ), isFalse,
      );
    }
  });

  test('D9 reopened local profile preserves onboarding completion without granting AI consent', () async {
    // This proves persistence on the SAME local installation only. It does not
    // prove a different device can fetch a patient-owned remote profile.
    final temp = await Directory.systemTemp.createTemp('iamina-d9-');
    addTearDown(() => temp.delete(recursive: true));
    final databasePath = '${temp.path}/patient.sqlite';

    final first = AppDatabase(NativeDatabase(File(databasePath)));
    try {
      await first.into(first.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(734),
          preferredLanguage: const drift.Value('fr'),
          updatedAt: DateTime.utc(2026, 10, 14),
          diabetesType: const drift.Value('type2'),
          treatment: const drift.Value('tablets'),
          aiConsentGivenAt: drift.Value(DateTime.utc(2026, 10, 13)),
        ),
      );
    } finally {
      await first.close();
    }

    final reopened = AppDatabase(NativeDatabase(File(databasePath)));
    addTearDown(reopened.close);
    final profile = await reopened.select(reopened.patientProfiles).getSingle();
    final consent = ConsentService();
    addTearDown(consent.dispose);
    consent.seedInitialProfile(profile);

    expect(profile.userId, 734);
    expect(consent.isInitialized, isTrue);
    expect(consent.hasCompletedOnboarding, isTrue);
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: consent.hasCompletedOnboarding,
        hasProfileState: consent.isInitialized,
      ),
      isFalse,
    );
    // An old consent timestamp alone is never verified evidence.
    expect(consent.hasConsent, isFalse);
  });

  test('D9 missing profile after startup still requires onboarding', () async {
    final db = AppDatabase(NativeDatabase.memory());
    final consent = ConsentService(hasVerifiedEvidence: true);
    addTearDown(db.close);
    addTearDown(consent.dispose);

    consent.seedInitialProfile(
      await db.select(db.patientProfiles).getSingleOrNull(),
    );
    expect(consent.isInitialized, isTrue);
    expect(consent.hasCompletedOnboarding, isFalse);
    expect(consent.hasConsent, isFalse);
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: consent.hasCompletedOnboarding,
        hasProfileState: consent.isInitialized,
      ),
      isTrue,
    );
  });

  test('D9 profile hydration must finish before the onboarding gate acts', () {
    final consent = ConsentService();
    addTearDown(consent.dispose);
    expect(consent.isInitialized, isFalse);
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: false,
        hasProfileState: consent.isInitialized,
      ),
      isFalse,
    );
    consent.seedInitialProfile(null);
    expect(consent.isInitialized, isTrue);
    expect(
      shouldApplyOnboardingGate(
        isLoggedIn: true,
        isAnonymous: false,
        requiresHostedRemoteLogin: false,
        hasCompletedOnboarding: consent.hasCompletedOnboarding,
        hasProfileState: consent.isInitialized,
      ),
      isTrue,
    );
  });

}
