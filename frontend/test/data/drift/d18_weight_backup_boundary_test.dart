import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

const _uuid = '123e4567-e89b-42d3-a456-426614174000';
const _uuid2 = '123e4567-e89b-42d3-a456-426614174001';

Future<AppDatabase> _vault(int user) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(user),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(user),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 15),
    ),
  );
  return db;
}

Future<void> _twoMeasurements(AppDatabase db) async {
  final store = PatientWeightHistoryStore(db);
  await store.append(
    clientUuid: _uuid, value: '71.20', unit: 'kg',
    measuredAtUtc: DateTime.utc(2026, 10, 13),
  );
  await store.append(
    clientUuid: _uuid2, value: '155.00', unit: 'lb',
    measuredAtUtc: DateTime.utc(2026, 10, 14),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D18 backup restores all explicitly dated weights in same-owner vault',
      () async {
    final source = await _vault(734);
    final destination = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(source.close);
    addTearDown(destination.close);
    await _twoMeasurements(source);

    final backup = await LocalBackup.exportVaultJson(source);
    final envelope = jsonDecode(backup) as Map<String, dynamic>;
    expect(envelope['weightHistoryFormatVersion'], 1);
    expect(envelope['weightObservations'], hasLength(2));

    await LocalBackup.restoreVaultJson(destination, backup);
    final rows = await PatientWeightHistoryStore(destination).recent();
    expect(rows, hasLength(2));
    expect(rows.map((r) => r.clientUuid), [_uuid2, _uuid]);
    expect(rows.first.kilogramsHundredths, 7031);

    // A second roundtrip must not invent timestamps or clinical authority.
    final again = jsonDecode(await LocalBackup.exportVaultJson(destination))
        as Map<String, dynamic>;
    expect(again['weightObservations'], envelope['weightObservations']);
  });

  test('D18 forged other-owner row fails before destructive restore', () async {
    final source = await _vault(734);
    final target = await _vault(734);
    addTearDown(source.close);
    addTearDown(target.close);
    await _twoMeasurements(source);
    await PatientWeightHistoryStore(target).append(
      clientUuid: _uuid, value: '59', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 13),
    );
    final envelope = jsonDecode(await LocalBackup.exportVaultJson(source))
        as Map<String, dynamic>;
    final weightRows = (envelope['weightObservations'] as List).cast<Map>();
    weightRows.first['user_id'] = 812;
    await expectLater(
      LocalBackup.restoreVaultJson(target, jsonEncode(envelope)),
      throwsFormatException,
    );
    final untouched = await PatientWeightHistoryStore(target).recent();
    expect(untouched, hasLength(1));
    expect(untouched.single.valueHundredths, 5900);
  });

  test('D18 incompatible unit conversion or malformed timestamp is rejected',
      () async {
    final source = await _vault(734);
    final dest = await _vault(734);
    addTearDown(source.close);
    addTearDown(dest.close);
    await _twoMeasurements(source);

    final original = jsonDecode(await LocalBackup.exportVaultJson(source))
        as Map<String, dynamic>;
    for (final tamper in ['metric', 'timezone', 'provenance', 'uuid']) {
      final payload = jsonDecode(jsonEncode(original)) as Map<String, dynamic>;
      final rows = (payload['weightObservations'] as List).cast<Map>();
      switch (tamper) {
        case 'metric':
          rows.first['kilograms_hundredths'] = 12345;
        case 'timezone':
          rows.first['measured_at_utc'] = '2026-10-14T10:00:00';
        case 'provenance':
          rows.first['provenance'] = 'ai_inferred';
        case 'uuid':
          rows.first['client_uuid'] = 'not-a-uuid';
      }
      await expectLater(
        LocalBackup.restoreVaultJson(dest, jsonEncode(payload)),
        throwsFormatException,
      );
      expect(await PatientWeightHistoryStore(dest).recent(), isEmpty);
    }
  });

  test('D18 old scoped-v2 backup cannot erase newer local history', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _twoMeasurements(db);
    final old = jsonDecode(await LocalBackup.exportVaultJson(db))
        as Map<String, dynamic>;
    old.remove('weightHistoryFormatVersion');
    old.remove('weightObservations');

    await expectLater(
      LocalBackup.restoreVaultJson(db, jsonEncode(old)), throwsStateError,
    );
    expect(await PatientWeightHistoryStore(db).recent(), hasLength(2));
  });

  test('D18 old scoped-v2 backup still restores to empty same-owner vault',
      () async {
    final source = await _vault(734);
    final empty = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(source.close);
    addTearDown(empty.close);
    final old = jsonDecode(await LocalBackup.exportVaultJson(source))
        as Map<String, dynamic>;
    old.remove('weightHistoryFormatVersion');
    old.remove('weightObservations');

    await LocalBackup.restoreVaultJson(empty, jsonEncode(old));
    expect(await PatientWeightHistoryStore(empty).recent(), isEmpty);
    expect(await empty.getProfileForLocalUserId(734), isNotNull);
  });

  test('D18 contaminated physical vault refuses export of foreign rows',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await _twoMeasurements(db);
    await db.customStatement('''
      INSERT INTO patient_weight_observations_v1
        (user_id, client_uuid, value_hundredths, unit,
         kilograms_hundredths, measured_at_utc, provenance)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [812, '123e4567-e89b-42d3-a456-426614174009',
          6000, 'kg', 6000, '2026-10-14T00:00:00.000Z', 'patient_declared']);
    await expectLater(LocalBackup.exportVaultJson(db), throwsStateError);
  });
}
