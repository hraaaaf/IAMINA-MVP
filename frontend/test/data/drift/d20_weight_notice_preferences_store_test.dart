import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_notice_preferences_store.dart';
import 'package:amina/features/profile/weight_notice_policy.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> _vault(int owner) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(owner),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(owner),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 15),
    ),
  );
  return db;
}

const _configured = LocalWeightNoticePolicy(
  enabled: true,
  minimumAbsoluteChangeKgHundredths: 120,
  minimumMeasurementSpan: Duration(days: 7),
  maximumLatestReadingAge: Duration(days: 4),
  minimumNoticeSpacing: Duration(days: 5),
);

final _now = DateTime.utc(2026, 10, 15, 18);
final _consented = DateTime.utc(2026, 10, 15, 17);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D20-C never opts in by default, even with a patient profile', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final p = await PatientWeightNoticePreferencesStore(db).read();
    expect(p.enabled, false);
    expect(p.consentedAtUtc, null);
    expect(p.policy.enabled, false);
  });

  test('D20-C opt-in roundtrips exact user thresholds and provenance', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    await store.optIn(
      confirmedByUser: true, policy: _configured,
      consentedAtUtc: _consented, nowUtc: _now,
    );
    final persisted = await PatientWeightNoticePreferencesStore(db).read();
    expect(persisted.enabled, true);
    expect(persisted.minimumChangeKgHundredths, 120);
    expect(persisted.minimumSpan, const Duration(days: 7));
    expect(persisted.maximumLatestAge, const Duration(days: 4));
    expect(persisted.minimumSpacing, const Duration(days: 5));
    expect(persisted.consentedAtUtc, _consented);
    expect(persisted.policy.minimumNoticeSpacing, const Duration(days: 5));
  });

  test('D20-C revoked consent stays OFF without any inherited criteria',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    await store.optIn(
      confirmedByUser: true, policy: _configured,
      consentedAtUtc: _consented, nowUtc: _now,
    );
    await store.optOut();
    final after = await PatientWeightNoticePreferencesStore(db).read();
    expect(after.enabled, false);
    expect(after.minimumChangeKgHundredths, isNull);
    expect(after.consentedAtUtc, isNull);
  });

  test('D20-C no user action, OFF policy, missing thresholds refuse ON',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    await expectLater(store.optIn(
      confirmedByUser: false, policy: _configured,
      consentedAtUtc: _consented, nowUtc: _now,
    ), throwsArgumentError);
    await expectLater(store.optIn(
      confirmedByUser: true, policy: const LocalWeightNoticePolicy(),
      consentedAtUtc: _consented, nowUtc: _now,
    ), throwsArgumentError);
    await expectLater(store.optIn(
      confirmedByUser: true,
      policy: const LocalWeightNoticePolicy(enabled: true),
      consentedAtUtc: _consented, nowUtc: _now,
    ), throwsArgumentError);
    expect((await store.read()).enabled, false);
  });

  test('D20-C future or ambiguous consent time is never persisted', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    for (final invalid in [DateTime(2026, 10, 15, 17),
                           DateTime.utc(2026, 10, 16)]) {
      await expectLater(store.optIn(
        confirmedByUser: true, policy: _configured,
        consentedAtUtc: invalid, nowUtc: _now,
      ), throwsArgumentError);
    }
    expect((await store.read()).enabled, false);
  });

  test('D20-C zero/subsecond criteria and magnitude are not accepted',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    for (final invalid in [
      const LocalWeightNoticePolicy(
        enabled: true, minimumAbsoluteChangeKgHundredths: 0,
        minimumMeasurementSpan: Duration(days: 7),
        maximumLatestReadingAge: Duration(days: 4),
        minimumNoticeSpacing: Duration(days: 5),
      ),
      const LocalWeightNoticePolicy(
        enabled: true, minimumAbsoluteChangeKgHundredths: 120,
        minimumMeasurementSpan: Duration(milliseconds: 500),
        maximumLatestReadingAge: Duration(days: 4),
        minimumNoticeSpacing: Duration(days: 5),
      ),
    ]) {
      await expectLater(store.optIn(
        confirmedByUser: true, policy: invalid,
        consentedAtUtc: _consented, nowUtc: _now,
      ), throwsArgumentError);
    }
    expect((await store.read()).enabled, false);
  });

  test('D20-C separate A and B physical vaults never share opt-in',
      () async {
    final a = await _vault(734), b = await _vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    final aStore = PatientWeightNoticePreferencesStore(a);
    final bStore = PatientWeightNoticePreferencesStore(b);
    await aStore.optIn(
      confirmedByUser: true, policy: _configured,
      consentedAtUtc: _consented, nowUtc: _now,
    );
    expect((await bStore.read()).enabled, false);
    await bStore.optIn(
      confirmedByUser: true,
      policy: const LocalWeightNoticePolicy(
        enabled: true, minimumAbsoluteChangeKgHundredths: 230,
        minimumMeasurementSpan: Duration(days: 3),
        maximumLatestReadingAge: Duration(days: 8),
        minimumNoticeSpacing: Duration(days: 7),
      ),
      consentedAtUtc: _consented, nowUtc: _now,
    );
    expect((await aStore.read()).minimumChangeKgHundredths, 120);
    expect((await bStore.read()).minimumChangeKgHundredths, 230);
    await aStore.optOut();
    expect((await aStore.read()).enabled, false);
    expect((await bStore.read()).enabled, true);
  });

  test('D20-C legacy/audit vaults and profile-less vault refuse settings',
      () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    final missingProfile = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    addTearDown(missingProfile.close);
    expect(() => PatientWeightNoticePreferencesStore(legacy), throwsStateError);
    expect(() => PatientWeightNoticePreferencesStore(audit), throwsStateError);
    await expectLater(
      PatientWeightNoticePreferencesStore(missingProfile).read(),
      throwsStateError,
    );
  });

  test('D20-C foreign consent row inside same vault fails closed', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightNoticePreferencesStore(db);
    await store.read(); // Initializes the local-only table.
    await db.customStatement('''
      INSERT INTO patient_weight_notice_preferences_v1 VALUES
      (812, 1, 120, 86400, 86400, 86400, '2026-10-15T17:00:00.000Z')
    ''');
    await expectLater(store.read(), throwsStateError);
    await expectLater(store.optIn(
      confirmedByUser: true, policy: _configured,
      consentedAtUtc: _consented, nowUtc: _now,
    ), throwsStateError);
  });
}
