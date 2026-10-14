import 'dart:async';

import 'package:amina/services/consent_service.dart';
import 'package:amina/services/d9_first_use_transport.dart';
import 'package:flutter_test/flutter_test.dart';

D9FirstUseProof proof(int owner, {bool completed = true}) =>
    D9FirstUseProof(
      ownerUserId: owner,
      completed: completed,
      completedAt: completed ? DateTime.utc(2026, 10, 14) : null,
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D9 complete server proof lifts first-use only for matching patient',
      () async {
    final consent = ConsentService()..seedInitialProfile(null);
    addTearDown(consent.dispose);
    expect(consent.hasCompletedOnboarding, isFalse);
    expect(consent.hasConsent, isFalse);
    expect(
      consent.adoptVerifiedD9FirstUseProof(proof(812), activeOwner: 734),
      isFalse,
    );
    expect(consent.hasCompletedOnboarding, isFalse);
    expect(
      consent.adoptVerifiedD9FirstUseProof(
        proof(734, completed: false), activeOwner: 734,
      ),
      isFalse,
    );
    expect(consent.hasCompletedOnboarding, isFalse);
    expect(
      consent.adoptVerifiedD9FirstUseProof(proof(734), activeOwner: 734),
      isTrue,
    );
    expect(consent.hasCompletedOnboarding, isTrue);
    expect(consent.hasConsent, isFalse);
    expect(consent.isInitialized, isTrue);
  });

  test('D9 remote completion survives null profile streams; AI stays denied',
      () async {
    final stream = StreamController<dynamic>.broadcast();
    addTearDown(stream.close);
    final consent = ConsentService()..seedInitialProfile(null);
    addTearDown(consent.dispose);
    expect(consent.adoptVerifiedD9FirstUseProof(proof(734), activeOwner: 734),
        isTrue);
    // Use a correctly typed null patient-profile stream: no clinical record is
    // invented by D9 and no AI consent is allowed.
    consent.attachStream(Stream<Never?>.value(null));
    await Future<void>.delayed(Duration.zero);
    expect(consent.hasCompletedOnboarding, isTrue);
    expect(consent.hasConsent, isFalse);
  });

  test('D9 A-B-A instances cannot inherit a previous vault first-use proof',
      () {
    final a = ConsentService()..seedInitialProfile(null);
    final b = ConsentService()..seedInitialProfile(null);
    addTearDown(a.dispose);
    addTearDown(b.dispose);
    expect(a.adoptVerifiedD9FirstUseProof(proof(734), activeOwner: 734), isTrue);
    expect(b.hasCompletedOnboarding, isFalse);
    expect(b.adoptVerifiedD9FirstUseProof(proof(734), activeOwner: 812), isFalse);
    expect(b.hasCompletedOnboarding, isFalse);
    // A future separate vault instance does not retain in-memory status.
    final newA = ConsentService()..seedInitialProfile(null);
    addTearDown(newA.dispose);
    expect(newA.hasCompletedOnboarding, isFalse);
    expect(newA.hasConsent, isFalse);
  });

  test('D9 only server-confirmed completion can bypass first-use; not consent',
      () {
    final consent = ConsentService(hasVerifiedEvidence: false)
      ..seedInitialProfile(null);
    addTearDown(consent.dispose);
    final incomplete = D9FirstUseProof(
      ownerUserId: 734, completed: true, completedAt: null,
    );
    expect(consent.adoptVerifiedD9FirstUseProof(incomplete, activeOwner: 734),
        isFalse);
    expect(consent.hasCompletedOnboarding, isFalse);
    expect(consent.hasConsent, isFalse);
  });
}
