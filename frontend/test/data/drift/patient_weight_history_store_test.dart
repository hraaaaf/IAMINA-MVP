import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

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

const _aUuid = '123e4567-e89b-42d3-a456-426614174000';
const _bUuid = '123e4567-e89b-42d3-a456-426614174001';
const _cUuid = '123e4567-e89b-42d3-a456-426614174002';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D18 scoped vault starts empty, appends without losing older values',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightHistoryStore(db);
    expect(await store.recent(), isEmpty);

    final firstAt = DateTime.utc(2026, 10, 13, 8, 0);
    final secondAt = DateTime.utc(2026, 10, 14, 8, 0);
    final first = await store.append(
      clientUuid: _aUuid,
      value: '71.20',
      unit: 'kg',
      measuredAtUtc: firstAt,
    );
    final second = await store.append(
      clientUuid: _bUuid,
      value: '155.00',
      unit: 'lb',
      measuredAtUtc: secondAt,
    );
    expect(first.valueHundredths, 7120);
    expect(first.kilogramsHundredths, 7120);
    expect(second.valueHundredths, 15500);
    expect(second.kilogramsHundredths, 7031);
    expect(second.provenance, 'patient_declared');
    final rows = await store.recent();
    expect(rows, hasLength(2));
    expect(rows.map((r) => r.clientUuid), [_bUuid, _aUuid]);
    expect(rows.map((r) => r.measuredAtUtc), [secondAt, firstAt]);
    expect(await store.exportOwnedRows(), hasLength(2));
  });

  test('D18 A/B physical vault isolation rejects legacy and audit scopes',
      () async {
    final a = await _vault(734);
    final b = await _vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    final aStore = PatientWeightHistoryStore(a);
    final bStore = PatientWeightHistoryStore(b);

    await aStore.append(
      clientUuid: _aUuid, value: '60', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 14),
    );
    expect(await bStore.recent(), isEmpty);
    await bStore.append(
      clientUuid: _aUuid, value: '65', unit: 'kg',
      measuredAtUtc: DateTime.utc(2026, 10, 14),
    );
    expect((await aStore.recent()).single.valueHundredths, 6000);
    expect((await bStore.recent()).single.valueHundredths, 6500);
    expect((await aStore.exportOwnedRows()).single['user_id'], 734);
    expect((await bStore.exportOwnedRows()).single['user_id'], 812);

    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    expect(() => PatientWeightHistoryStore(legacy), throwsStateError);
    expect(() => PatientWeightHistoryStore(audit), throwsStateError);
  });

  test('D18 repeated UUID is idempotent, changed payload cannot overwrite',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightHistoryStore(db);
    final at = DateTime.utc(2026, 10, 14, 13);
    final first = await store.append(
      clientUuid: _aUuid, value: '72', unit: 'kg', measuredAtUtc: at,
    );
    final replay = await store.append(
      clientUuid: _aUuid, value: '72.00', unit: 'kg', measuredAtUtc: at,
    );
    expect(replay.clientUuid, first.clientUuid);
    await expectLater(
      store.append(
        clientUuid: _aUuid, value: '75', unit: 'kg', measuredAtUtc: at,
      ),
      throwsStateError,
    );
    expect((await store.recent()).single.valueHundredths, 7200);
  });

  test('D18 invalid units/values/timestamps fail without writes', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientWeightHistoryStore(db);
    final at = DateTime.utc(2026, 10, 14);
    for (final bad in ['0', '-1', '60.123', 'NaN', '10000']) {
      await expectLater(
        store.append(
          clientUuid: _aUuid, value: bad, unit: 'kg', measuredAtUtc: at,
        ),
        throwsArgumentError,
      );
    }
    for (final invalid in ['stones', '']) {
      await expectLater(
        store.append(
          clientUuid: _aUuid, value: '70', unit: invalid, measuredAtUtc: at,
        ),
        throwsArgumentError,
      );
    }
    await expectLater(
      store.append(
        clientUuid: 'other-id', value: '70', unit: 'kg', measuredAtUtc: at,
      ),
      throwsArgumentError,
    );
    await expectLater(
      store.append(
        clientUuid: _aUuid, value: '70', unit: 'kg',
        measuredAtUtc: DateTime.now().toUtc().add(const Duration(days: 1)),
      ),
      throwsArgumentError,
    );
    expect(await store.recent(), isEmpty);
  });

  test('D18 no patient-owned profile means no orphan weight history',
      () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    final store = PatientWeightHistoryStore(db);
    await expectLater(
      store.append(
        clientUuid: _cUuid, value: '62', unit: 'kg',
        measuredAtUtc: DateTime.utc(2026, 10, 14),
      ),
      throwsStateError,
    );
    expect(await store.recent(), isEmpty);
  });
}
