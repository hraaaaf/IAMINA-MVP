import 'package:amina/data/drift/database.dart';
import 'package:amina/routes/app_router.dart';
import 'package:amina/services/consent_service.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

bool _gate({
  required bool complete,
  bool initialized = true,
  bool authenticated = true,
  bool anonymous = false,
  bool requiresRemote = false,
}) => shouldApplyOnboardingGate(
  isLoggedIn: authenticated,
  isAnonymous: anonymous,
  requiresHostedRemoteLogin: requiresRemote,
  hasCompletedOnboarding: complete,
  hasProfileState: initialized,
);

void main() {
  test('returning patient with verified local minimum never repeats onboarding', () {
    expect(_gate(complete: true), isFalse);
    expect(_gate(complete: true), isFalse); // after router refresh
    expect(_gate(complete: false), isTrue);
  });

  test('no silent bypass from unauthenticated or uninitialized states', () {
    expect(_gate(complete: false, initialized: false), isFalse);
    expect(_gate(complete: false, authenticated: false), isFalse);
    expect(_gate(complete: false, anonymous: true), isFalse);
    expect(_gate(complete: false, requiresRemote: true), isFalse);
    expect(_gate(complete: false, initialized: true), isTrue);
  });

  test('real local medical profile drives returning gate, not login or AI consent', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    final service = ConsentService();
    addTearDown(service.dispose);
    service.seedInitialProfile(null);
    expect(service.isInitialized, isTrue);
    expect(service.hasCompletedOnboarding, isFalse);
    expect(_gate(complete: service.hasCompletedOnboarding), isTrue);

    await db.into(db.patientProfiles).insert(PatientProfilesCompanion.insert(
      userId: const drift.Value(734),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 12),
      diabetesType: const drift.Value('type2'),
      treatment: const drift.Value('tablets'),
    ));
    final profile = await db.select(db.patientProfiles).getSingle();
    service.seedInitialProfile(profile);
    expect(service.hasCompletedOnboarding, isTrue);
    expect(service.hasConsent, isFalse); // never fabricate AI consent
    expect(_gate(complete: service.hasCompletedOnboarding), isFalse);
    service.seedInitialProfile(profile); // simulated relaunch
    expect(_gate(complete: service.hasCompletedOnboarding), isFalse);

    await (db.update(db.patientProfiles)
      ..where((row) => row.userId.equals(734)))
      .write(const PatientProfilesCompanion(treatment: drift.Value(null)));
    final incomplete = await db.select(db.patientProfiles).getSingle();
    service.seedInitialProfile(incomplete);
    expect(service.hasCompletedOnboarding, isFalse);
    expect(_gate(complete: service.hasCompletedOnboarding), isTrue);
  });
}
