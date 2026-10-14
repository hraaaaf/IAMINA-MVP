import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

bool _firstUseRequired(ConsentService consent) =>
    shouldApplyOnboardingGate(
      isLoggedIn: true,
      isAnonymous: false,
      requiresHostedRemoteLogin: false,
      hasCompletedOnboarding: consent.hasCompletedOnboarding,
      hasProfileState: consent.isInitialized,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D9 first-use gate waits for profile hydration, then fails closed on absence',
      () {
    final consent = ConsentService();
    addTearDown(consent.dispose);
    expect(consent.isInitialized, isFalse);
    expect(_firstUseRequired(consent), isFalse);
    consent.seedInitialProfile(null);
    expect(consent.isInitialized, isTrue);
    expect(_firstUseRequired(consent), isTrue);
    expect(consent.hasConsent, isFalse);
  });

  test('D9 incomplete account profile cannot be mistaken for completed onboarding',
      () async {
    for (final fields in [
      (type: null, treatment: null),
      (type: 'type2', treatment: null),
      (type: null, treatment: 'tablets'),
      (type: '  ', treatment: 'tablets'),
      (type: 'type2', treatment: '   '),
    ]) {
      final db = AppDatabase(NativeDatabase.memory());
      final consent = ConsentService();
      try {
        await db.into(db.patientProfiles).insert(
          PatientProfilesCompanion.insert(
            userId: const drift.Value(734),
            updatedAt: DateTime.utc(2026, 10, 14),
            diabetesType: drift.Value(fields.type),
            treatment: drift.Value(fields.treatment),
          ),
        );
        consent.seedInitialProfile(
          await db.select(db.patientProfiles).getSingleOrNull(),
        );
        expect(_firstUseRequired(consent), isTrue,
            reason: 'type=${fields.type} treatment=${fields.treatment}');
        expect(consent.hasConsent, isFalse);
      } finally {
        consent.dispose();
        await db.close();
      }
    }
  });

  test('D9 reactive local profile save clears first-use gate without granting AI',
      () async {
    final db = AppDatabase(NativeDatabase.memory());
    final consent = ConsentService();
    addTearDown(db.close);
    addTearDown(consent.dispose);
    final initialized = Completer<void>();
    final completed = Completer<void>();
    consent.addListener(() {
      if (consent.isInitialized && !initialized.isCompleted) {
        initialized.complete();
      }
      if (consent.hasCompletedOnboarding && !completed.isCompleted) {
        completed.complete();
      }
    });
    consent.attachStream(db.watchProfile());
    await initialized.future.timeout(const Duration(seconds: 5));
    expect(_firstUseRequired(consent), isTrue);

    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 14),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
      ),
    );
    await completed.future.timeout(const Duration(seconds: 5));
    expect(_firstUseRequired(consent), isFalse);
    expect(consent.hasConsent, isFalse);
  });

  test('D9 AI consent withdrawal cannot reset a saved onboarding profile',
      () async {
    final db = AppDatabase(NativeDatabase.memory());
    final consent = ConsentService(hasVerifiedEvidence: true);
    addTearDown(db.close);
    addTearDown(consent.dispose);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 14),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
        aiConsentGivenAt: drift.Value(DateTime.utc(2026, 10, 14)),
      ),
    );
    consent.seedInitialProfile(
      await db.select(db.patientProfiles).getSingleOrNull(),
    );
    expect(_firstUseRequired(consent), isFalse);
    expect(consent.hasConsent, isTrue);
    consent.clearVerifiedConsent();
    expect(consent.hasConsent, isFalse);
    expect(_firstUseRequired(consent), isFalse);
    consent.declineLocally();
    expect(consent.hasDeclinedLocally, isTrue);
    expect(_firstUseRequired(consent), isFalse);
  });

  test('D9 negative gap: a fresh installation has no restored profile by itself',
      () async {
    // A passing test here is evidence of an UNIMPLEMENTED remote restore,
    // not evidence that an existing account is recognized across devices.
    const owner = 734;
    final originalDevice = AppDatabase(NativeDatabase.memory());
    final freshDevice = AppDatabase(NativeDatabase.memory());
    addTearDown(originalDevice.close);
    addTearDown(freshDevice.close);
    await originalDevice.into(originalDevice.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(owner),
        updatedAt: DateTime.utc(2026, 10, 14),
        diabetesType: const drift.Value('type2'),
        treatment: const drift.Value('tablets'),
      ),
    );
    final originalConsent = ConsentService()
      ..seedInitialProfile(
        await originalDevice.select(originalDevice.patientProfiles)
            .getSingleOrNull(),
      );
    final freshConsent = ConsentService()
      ..seedInitialProfile(
        await freshDevice.select(freshDevice.patientProfiles)
            .getSingleOrNull(),
      );
    addTearDown(originalConsent.dispose);
    addTearDown(freshConsent.dispose);
    expect(_firstUseRequired(originalConsent), isFalse);
    expect(_firstUseRequired(freshConsent), isTrue);
    expect(freshConsent.hasConsent, isFalse);
  });
}
