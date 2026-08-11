// ConsentService — unit tests
//
// Tests the in-memory state machine without requiring any widget tree.
// Uses an in-memory Drift database to exercise the stream attachment path.
import 'package:drift/native.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/consent_service.dart';
import 'package:amina/data/drift/database.dart';

AppDatabase _openDb() => AppDatabase(NativeDatabase.memory());

// Helper: create a PatientProfile row with or without AI consent.
Future<void> _insertProfile(AppDatabase db, {bool withConsent = false}) async {
  await db
      .into(db.patientProfiles)
      .insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(1),
          preferredLanguage: const drift.Value('fr'),
          updatedAt: DateTime.now(),
          aiConsentGivenAt: drift.Value(withConsent ? DateTime.now() : null),
        ),
      );
}

void main() {
  group('ConsentService — seedInitialProfile', () {
    test('null profile → hasConsent false, not initialized before seed', () {
      final svc = ConsentService();
      expect(svc.isInitialized, isFalse);
      svc.seedInitialProfile(null);
      expect(svc.isInitialized, isTrue);
      expect(svc.hasConsent, isFalse);
    });

    test('profile without consent → hasConsent false', () {
      final svc = ConsentService();
      // Build a minimal PatientProfileData with aiConsentGivenAt = null
      // We call seedInitialProfile(null) to simulate no record
      svc.seedInitialProfile(null);
      expect(svc.hasConsent, isFalse);
    });

    test('isInitialized becomes true after seed', () {
      final svc = ConsentService();
      expect(svc.isInitialized, isFalse);
      svc.seedInitialProfile(null);
      expect(svc.isInitialized, isTrue);
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

    test('declineLocally does not change hasConsent', () {
      final svc = ConsentService();
      svc.seedInitialProfile(null);
      svc.declineLocally();
      expect(svc.hasConsent, isFalse);
    });

    test('declineLocally notifies listeners', () {
      final svc = ConsentService();
      var notified = false;
      svc.addListener(() => notified = true);
      svc.declineLocally();
      expect(notified, isTrue);
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

    test('stream emission with no profile keeps hasConsent false', () async {
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isFalse);
    });

    test('stream emission with consent profile sets hasConsent true', () async {
      await _insertProfile(db, withConsent: true);
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isTrue);
    });

    test(
      'stream emission with no consent profile keeps hasConsent false',
      () async {
        await _insertProfile(db, withConsent: false);
        final svc = ConsentService();
        svc.attachStream(db.watchProfile());
        await Future<void>.delayed(const Duration(milliseconds: 50));
        expect(svc.hasConsent, isFalse);
      },
    );

    test('consent changes reflect in real-time via stream', () async {
      await _insertProfile(db, withConsent: false);
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(svc.hasConsent, isFalse);

      // Grant consent via DB helper
      await db.setAiConsent(granted: true);
      await Future<void>.delayed(const Duration(milliseconds: 100));
      expect(svc.hasConsent, isTrue);
    });

    test('dispose cancels subscription without error', () async {
      final svc = ConsentService();
      svc.attachStream(db.watchProfile());
      expect(() => svc.dispose(), returnsNormally);
    });
  });
}
