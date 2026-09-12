// ConsentService — unit tests
import 'package:drift/native.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/data/drift/database.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

Future<void> _insertProfile(AppDatabase db, {bool withConsent = false}) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: const drift.Value(1),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.now(),
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
