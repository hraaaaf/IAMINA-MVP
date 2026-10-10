// ConsentService — unit tests
import 'package:drift/native.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/data/drift/database.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Future<void> _insertProfile(
  AppDatabase db, {
  bool withConsent = false,
  bool completedOnboarding = false,
}) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: const drift.Value(1),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.now(),
      diabetesType: drift.Value(completedOnboarding ? 'type2' : null),
      treatment: drift.Value(completedOnboarding ? 'tablets' : null),
      aiConsentGivenAt: drift.Value(withConsent ? DateTime.now() : null),
    ),
  );
}

void main() {
  group('ConsentService — evidence-bound seed', () {
    test('null profile → hasConsent false', () {
      final svc = ConsentService(hasVerifiedEvidence: true);
      svc.seedInitialProfile(null);
      expect(svc.isInitialized, isTrue);
      expect(svc.hasConsent, isFalse);
    });

    test('legacy timestamp without verified evidence stays false', () async {
      final db = _openDb();
      addTearDown(db.close);
      await _insertProfile(db, withConsent: true);
      final profile = await db.select(db.patientProfiles).getSingle();
      final svc = ConsentService();
      svc.seedInitialProfile(profile);
      expect(svc.hasConsent, isFalse);
    });

    test('timestamp plus verified evidence is accepted locally', () async {
      final db = _openDb();
      addTearDown(db.close);
      await _insertProfile(db, withConsent: true);
      final profile = await db.select(db.patientProfiles).getSingle();
      final svc = ConsentService(hasVerifiedEvidence: true);
      svc.seedInitialProfile(profile);
      expect(svc.hasConsent, isTrue);
    });
  });

  group('ConsentService — onboarding completeness', () {
    test('null profile is not completed', () {
      final svc = ConsentService();
      svc.seedInitialProfile(null);
      expect(svc.hasCompletedOnboarding, isFalse);
    });

    test('partial profile is not completed', () async {
      final db = _openDb();
      addTearDown(db.close);
      await _insertProfile(db);
      final profile = await db.select(db.patientProfiles).getSingle();
      final svc = ConsentService();
      svc.seedInitialProfile(profile);
      expect(svc.hasCompletedOnboarding, isFalse);
    });

    test('diabetes type and treatment complete onboarding', () async {
      final db = _openDb();
      addTearDown(db.close);
      await _insertProfile(db, completedOnboarding: true);
      final profile = await db.select(db.patientProfiles).getSingle();
      final svc = ConsentService();
      svc.seedInitialProfile(profile);
      expect(svc.hasCompletedOnboarding, isTrue);
    });
  });

  group('ConsentService — declineLocally', () {
    test('hasDeclinedLocally starts false', () {
      final svc = ConsentService();
      expect(svc.hasDeclinedLocally, isFalse);
    });

    test('declineLocally sets hasDeclinedLocally true', () {
      final svc = ConsentService();
      svc.declineLocally();
      expect(svc.hasDeclinedLocally, isTrue);
    });

    test('declineLocally does not grant consent', () {
      final svc = ConsentService();
      svc.seedInitialProfile(null);
      svc.declineLocally();
      expect(svc.hasConsent, isFalse);
    });

    test('local decline masks earlier locally verified consent immediately', () {
      final svc = ConsentService();
      svc.seedInitialProfile(null);
      svc.markVerifiedConsent();
      expect(svc.hasConsent, isTrue);

      svc.declineLocally();
      expect(svc.hasDeclinedLocally, isTrue);
      expect(svc.hasConsent, isFalse);

      // A newly verified explicit acceptance is required to re-enable UI AI.
      svc.markVerifiedConsent();
      expect(svc.hasDeclinedLocally, isFalse);
      expect(svc.hasConsent, isTrue);
    });

    test('profile stream updates cannot undo an active local decline', () async {
      final db = _openDb();
      addTearDown(db.close);
      await _insertProfile(db, withConsent: true);
      final svc = ConsentService(hasVerifiedEvidence: true);
      addTearDown(svc.dispose);
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isTrue);

      svc.declineLocally();
      await db.setAiConsent(granted: true);
      await Future<void>.delayed(const Duration(milliseconds: 100));
      expect(svc.hasDeclinedLocally, isTrue);
      expect(svc.hasConsent, isFalse);
    });
  });

  group('ConsentService — attachStream', () {
    late AppDatabase db;

    setUp(() {
      db = _openDb();
    });

    tearDown(() async {
      await db.close();
    });

    test('stream timestamp without secure evidence remains denied', () async {
      await _insertProfile(db, withConsent: true);
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isFalse);
    });

    test(
      'onboarding completion notifies listeners when consent stays false',
      () async {
        await _insertProfile(db);
        final svc = ConsentService();
        var notifications = 0;
        svc.addListener(() => notifications++);
        svc.attachStream(db.watchProfile());
        await Future<void>.delayed(const Duration(milliseconds: 50));

        notifications = 0;
        await (db.update(db.patientProfiles)..where((tbl) => tbl.userId.equals(1)))
            .write(
          const PatientProfilesCompanion(
            diabetesType: drift.Value('type2'),
            treatment: drift.Value('tablets'),
          ),
        );
        await Future<void>.delayed(const Duration(milliseconds: 100));

        expect(svc.hasCompletedOnboarding, isTrue);
        expect(svc.hasConsent, isFalse);
        expect(notifications, greaterThan(0));
      },
    );

    test('stream timestamp with verified evidence sets consent true', () async {
      await _insertProfile(db, withConsent: true);
      final svc = ConsentService(hasVerifiedEvidence: true);
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isTrue);
    });

    test('verified evidence alone does not grant without timestamp', () async {
      await _insertProfile(db, withConsent: false);
      final svc = ConsentService(hasVerifiedEvidence: true);
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isFalse);
    });

    test('markVerifiedConsent opens gate only after verified flow', () {
      final svc = ConsentService();
      svc.seedInitialProfile(null);
      svc.markVerifiedConsent();
      expect(svc.hasConsent, isTrue);
      expect(svc.hasDeclinedLocally, isFalse);
      svc.clearVerifiedConsent();
      expect(svc.hasConsent, isFalse);
    });

    test('withdrawal timestamp update closes gate in real time', () async {
      await _insertProfile(db, withConsent: true);
      final svc = ConsentService(hasVerifiedEvidence: true);
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isTrue);

      await db.setAiConsent(granted: false);
      await Future<void>.delayed(const Duration(milliseconds: 100));
      expect(svc.hasConsent, isFalse);
    });

    test('dispose cancels subscription without error', () {
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      expect(() => svc.dispose(), returnsNormally);
    });
  });
}
