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
}
