import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/data/drift/patient_weight_notice_preferences_store.dart';
import 'package:amina/data/drift/patient_weight_notice_delivery_ledger.dart';
import 'package:amina/features/profile/weight_notice_policy.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

const _uuidA = '123e4567-e89b-42d3-a456-426614174000';
const _uuidB = '123e4567-e89b-42d3-a456-426614174001';
const _uuidC = '123e4567-e89b-42d3-a456-426614174002';

Future<AppDatabase> _vault(int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 15),
    ),
  );
  return db;
}

Future<void> _history(AppDatabase db) async {
  final history = PatientWeightHistoryStore(db);
  await history.append(
    clientUuid: _uuidA, value: '70', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 1),
  );
  await history.append(
    clientUuid: _uuidB, value: '71.50', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 6),
  );
}

Future<void> _consent(AppDatabase db) async {
  await PatientWeightNoticePreferencesStore(db).optIn(
    confirmedByUser: true,
    policy: const LocalWeightNoticePolicy(
      enabled: true,
      minimumAbsoluteChangeKgHundredths: 100,
      minimumMeasurementSpan: Duration(days: 3),
      maximumLatestReadingAge: Duration(days: 10),
      minimumNoticeSpacing: Duration(days: 4),
    ),
    consentedAtUtc: DateTime.utc(2026, 10, 6, 12),
    nowUtc: DateTime.utc(2026, 10, 15, 18),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D20-D no consent never creates a reservation', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    expect(await ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 7),
    ), isNull);
    expect(await ledger.reservationCount(), 0);
  });

  test('D20-D OS permission OFF means zero reservation', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    expect(await ledger.reserveIfEligible(
      osNotificationPermission: false, nowUtc: DateTime.utc(2026, 10, 15),
    ), isNull);
    expect(await ledger.reservationCount(), 0);
  });

  test('D20-D creates only a source-bound reservation, not delivery', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    final reservation = await ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 15),
    );
    expect(reservation, isNotNull);
    expect(reservation!.ownerId, 734);
    expect(reservation.latestEvidenceId, _uuidB);
    expect(reservation.baselineEvidenceId, _uuidA);
    expect(reservation.deltaKgHundredths, 150);
    expect(reservation.latestAtUtc, DateTime.utc(2026, 10, 6));
    expect(await ledger.reservationCount(), 1);
  });

  test('D20-D dedup survives a new ledger instance in same vault', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final now = DateTime.utc(2026, 10, 15);
    expect(await PatientWeightNoticeDeliveryLedger(db).reserveIfEligible(
      osNotificationPermission: true, nowUtc: now,
    ), isNotNull);
    expect(await PatientWeightNoticeDeliveryLedger(db).reserveIfEligible(
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
    expect(await PatientWeightNoticeDeliveryLedger(db).reservationCount(), 1);
  });

  test('D20-D revoke before delivery prevents further reservation', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    await PatientWeightNoticePreferencesStore(db).optOut();
    expect(await ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 15),
    ), isNull);
    expect(await ledger.reservationCount(), 0);
  });

  test('D20-D two vaults cannot observe or revoke each other claims',
      () async {
    final a = await _vault(734);
    final b = await _vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    await _history(a);
    await _history(b);
    await _consent(a);
    final aLedger = PatientWeightNoticeDeliveryLedger(a);
    final bLedger = PatientWeightNoticeDeliveryLedger(b);
    expect(await aLedger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 15),
    ), isNotNull);
    expect(await bLedger.reservationCount(), 0);
    expect(await bLedger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 15),
    ), isNull);
    await PatientWeightNoticePreferencesStore(a).optOut();
    expect(await aLedger.reservationCount(), 1);
    expect(await bLedger.reservationCount(), 0);
  });

  test('D20-D stale readings, negative time and missing data fail closed',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    expect(await ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 30),
    ), isNull);
    expect(await ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 4),
    ), isNull);
    expect(() => ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime(2026, 10, 15),
    ), throwsArgumentError);
    expect(await ledger.reservationCount(), 0);
  });

  test('D20-D foreign reservation in a physical vault denies new claim',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _history(db);
    await _consent(db);
    final ledger = PatientWeightNoticeDeliveryLedger(db);
    await ledger.reservationCount();
    await db.customStatement('''
      INSERT INTO patient_weight_notice_reservations_v1 VALUES
        (812, 'foreign-id', 'foreign-base', 100,
         '2026-10-01T00:00:00.000Z', '2026-10-06T00:00:00.000Z',
         '2026-10-07T00:00:00.000Z')
    ''');
    await expectLater(ledger.reserveIfEligible(
      osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 15),
    ), throwsStateError);
  });

  test('D20-D legacy and audit DBs may not reserve', () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    expect(() => PatientWeightNoticeDeliveryLedger(legacy), throwsStateError);
    expect(() => PatientWeightNoticeDeliveryLedger(audit), throwsStateError);
  });
}
