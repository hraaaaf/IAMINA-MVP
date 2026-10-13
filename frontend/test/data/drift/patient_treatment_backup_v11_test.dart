import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> openVault(int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 13),
      treatment: const drift.Value('tablets'),
    ),
  );
  return db;
}

void main() {
  test('D7 scoped backup round-trip preserves multiple declarations exactly',
      () async {
    final db = await openVault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['insulin', 'oral_meds']);
    final backup = await LocalBackup.exportVaultJson(db);
    final decoded = jsonDecode(backup) as Map<String, dynamic>;
    expect(decoded['schemaVersion'], 12);
    expect(decoded['treatmentDeclarations'], hasLength(1));

    await store.write(state: 'unsure', codes: []);
    await LocalBackup.restoreVaultJson(db, backup);
    final restored = await store.read();
    expect(restored?.codes, ['insulin', 'oral_meds']);
    expect(restored?.state, 'declared');
    expect((await db.select(db.patientProfiles).getSingle()).treatment, 'tablets');
  });

  test('D7 v12 backup restores pending revision and exact generation', () async {
    final db = await openVault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle']);
    final serverAt = DateTime.utc(2026, 10, 13, 17, 42, 30, 123, 456);
    final first = (await store.read())!;
    expect(await store.acknowledgeIfUnchanged(
      expectedGeneration: first.localGeneration,
      serverUpdatedAtUtc: serverAt,
    ), isTrue);
    await store.write(state: 'declared', codes: ['lifestyle', 'oral_meds']);
    final expected = (await store.read())!;
    final backup = await LocalBackup.exportVaultJson(db);
    await store.write(state: 'none_declared', codes: []);
    await LocalBackup.restoreVaultJson(db, backup);
    final restored = (await store.read())!;
    expect(restored.codes, expected.codes);
    expect(restored.syncStatus, 'pending');
    expect(restored.localGeneration, expected.localGeneration);
    expect(restored.baseServerUpdatedAtUtc, serverAt);
  });

  test('D7 v12 backup rejects invalid generation without erasing owner', () async {
    final db = await openVault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['lifestyle']);
    final backup = jsonDecode(await LocalBackup.exportVaultJson(db))
        as Map<String, dynamic>;
    final row = (backup['treatmentDeclarations'] as List).single as Map;
    row['local_generation'] = 0;
    await expectLater(
      LocalBackup.restoreVaultJson(db, jsonEncode(backup)), throwsFormatException,
    );
    expect((await store.read())?.codes, ['lifestyle']);
    expect((await store.read())?.localGeneration, 1);
  });

  test('D7 foreign or malformed backup declarations fail without overwrite',
      () async {
    final a = await openVault(734);
    final b = await openVault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    final aStore = PatientTreatmentDeclarationStore(a);
    final bStore = PatientTreatmentDeclarationStore(b);
    await aStore.write(state: 'declared', codes: ['insulin']);
    await bStore.write(state: 'unsure', codes: []);
    final backup = jsonDecode(await LocalBackup.exportVaultJson(a))
        as Map<String, dynamic>;
    backup['vaultName'] = PatientVaultScope.nativeDjango(812).databaseName;
    final entries = backup['treatmentDeclarations'] as List;
    (entries.single as Map)['user_id'] = 734;
    await expectLater(
      LocalBackup.restoreVaultJson(b, jsonEncode(backup)), throwsFormatException,
    );
    expect((await bStore.read())?.state, 'unsure');
    expect((await aStore.read())?.codes, ['insulin']);

    (entries.single as Map)['user_id'] = 812;
    (entries.single as Map)['codes_json'] = jsonEncode(['insulin','insulin']);
    await expectLater(
      LocalBackup.restoreVaultJson(b, jsonEncode(backup)), throwsFormatException,
    );
    expect((await bStore.read())?.state, 'unsure');
  });

  test('D7 legacy backup cannot erase new declaration records', () async {
    final db = await openVault(734);
    addTearDown(db.close);
    final store = PatientTreatmentDeclarationStore(db);
    await store.write(state: 'declared', codes: ['insulin']);
    final backup = jsonDecode(await LocalBackup.exportVaultJson(db))
        as Map<String, dynamic>;
    backup.remove('treatmentDeclarations');
    backup['schemaVersion'] = 10;
    await expectLater(
      LocalBackup.restoreVaultJson(db, jsonEncode(backup)), throwsFormatException,
    );
    expect((await store.read())?.codes, ['insulin']);
  });
}
