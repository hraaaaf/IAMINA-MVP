import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/data/drift/patient_weight_notice_delivery_ledger.dart';
import 'package:amina/data/drift/patient_weight_notice_dispatch_preflight.dart';
import 'package:amina/data/drift/patient_weight_notice_preferences_store.dart';
import 'package:amina/features/profile/weight_notice_policy.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

const _first = '123e4567-e89b-42d3-a456-426614174000';
const _latest = '123e4567-e89b-42d3-a456-426614174001';
const _new = '123e4567-e89b-42d3-a456-426614174002';

Future<AppDatabase> _vault(int owner) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(owner));
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(owner),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 15),
    ),
  );
  return db;
}

Future<void> _seed(AppDatabase db) async {
  final h = PatientWeightHistoryStore(db);
  await h.append(clientUuid: _first, value: '70', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 1, 9));
  await h.append(clientUuid: _latest, value: '71.50', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 7, 9));
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

Future<LocalWeightNoticeReservation> _reserve(AppDatabase db) async =>
  (await PatientWeightNoticeDeliveryLedger(db).reserveIfEligible(
    osNotificationPermission: true, nowUtc: DateTime.utc(2026, 10, 8),
  ))!;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D20-G valid current reservation is eligible but NOT a delivery', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    final gate = PatientWeightNoticeDispatchPreflight(db);
    expect(await gate.check(reservation: reservation,
        osNotificationPermission: true,
        nowUtc: DateTime.utc(2026, 10, 8, 12)), true);
    expect(await PatientWeightNoticeDeliveryLedger(db).reservationCount(), 1);
  });

  test('D20-G OS permission withdrawn blocks reserved candidate', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: false,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
  });

  test('D20-G local opt-out makes a reservation ineligible', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    await PatientWeightNoticePreferencesStore(db).optOut();
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
  });

  test('D20-G fresh re-consent does not revive old reservation', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    final prefs = PatientWeightNoticePreferencesStore(db);
    await prefs.optOut();
    await prefs.optIn(
      confirmedByUser: true,
      policy: const LocalWeightNoticePolicy(
        enabled: true,
        minimumAbsoluteChangeKgHundredths: 100,
        minimumMeasurementSpan: Duration(days: 3),
        maximumLatestReadingAge: Duration(days: 10),
        minimumNoticeSpacing: Duration(days: 4),
      ),
      consentedAtUtc: DateTime.utc(2026, 10, 10),
      nowUtc: DateTime.utc(2026, 10, 10),
    );
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 11),
    ), false);
  });

  test('D20-G reservation never belongs to another patient vault', () async {
    final a = await _vault(734);
    final b = await _vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    await _seed(a);
    await _seed(b);
    final reservation = await _reserve(a);
    expect(await PatientWeightNoticeDispatchPreflight(b).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
    expect(await PatientWeightNoticeDispatchPreflight(a).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), true);
  });

  test('D20-G another newer reading makes queued notice stale', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    await PatientWeightHistoryStore(db).append(
      clientUuid: _new, value: '72', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 9),
    );
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 10),
    ), false);
  });

  test('D20-G original reservation is rejected when reading ages out',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 19),
    ), false);
  });

  test('D20-G updated user threshold cancels reserved notice', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    await PatientWeightNoticePreferencesStore(db).optIn(
      confirmedByUser: true,
      policy: const LocalWeightNoticePolicy(
        enabled: true, minimumAbsoluteChangeKgHundredths: 200,
        minimumMeasurementSpan: Duration(days: 3),
        maximumLatestReadingAge: Duration(days: 10),
        minimumNoticeSpacing: Duration(days: 4),
      ),
      consentedAtUtc: DateTime.utc(2026, 10, 6, 12),
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    );
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
  });

  test('D20-G missing or tampered local ledger row fails closed', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    await db.customStatement('''
      UPDATE patient_weight_notice_reservations_v1
      SET delta_kg_hundredths = 999
      WHERE user_id = 734
    ''');
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
  });

  test('D20-G foreign reservation row blocks even own valid candidate',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    await db.customStatement('''
      INSERT INTO patient_weight_notice_reservations_v1
        (user_id, latest_evidence_id, baseline_evidence_id,
         delta_kg_hundredths, baseline_at_utc, latest_at_utc, reserved_at_utc)
      VALUES
        (812, 'foreign-id', 'foreign-baseline', 100,
         '2026-10-01T09:00:00.000Z', '2026-10-07T09:00:00.000Z',
         '2026-10-08T00:00:00.000Z')
    ''');
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 8, 12),
    ), false);
  });

  test('D20-G invalid clocks and audit/legacy vaults reject preflight',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _seed(db);
    final reservation = await _reserve(db);
    expect(() => PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime(2026, 10, 8),
    ), throwsArgumentError);
    expect(await PatientWeightNoticeDispatchPreflight(db).check(
      reservation: reservation, osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 7),
    ), false);
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly());
    addTearDown(legacy.close);
    addTearDown(audit.close);
    expect(() => PatientWeightNoticeDispatchPreflight(legacy), throwsStateError);
    expect(() => PatientWeightNoticeDispatchPreflight(audit), throwsStateError);
  });
}
