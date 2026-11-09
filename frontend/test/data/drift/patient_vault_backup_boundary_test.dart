import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> seed(AppDatabase db, int id) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id),
      preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 13),
      diabetesType: const drift.Value('type1'),
      treatment: const drift.Value('insulin'),
    ),
  );
}

void main() {
  test('D7 vault backup cannot cross from native A to B', () async {
    final a = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    final b = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(812),
    );
    addTearDown(a.close);
    addTearDown(b.close);
    await seed(a, 734);
    await seed(b, 812);
    final backupA = await LocalBackup.exportVaultJson(a);
    final payload = jsonDecode(backupA) as Map<String, dynamic>;
    expect(payload['formatVersion'], LocalBackup.scopedFormatVersion);
    expect(payload['vaultName'], PatientVaultScope.nativeDjango(734).databaseName);
    await expectLater(
      LocalBackup.restoreVaultJson(b, backupA), throwsFormatException,
    );
    final bRows = await b.select(b.patientProfiles).get();
    expect(bRows.single.userId, 812);
    expect(bRows.single.diabetesType, 'type1');

    await LocalBackup.restoreVaultJson(a, backupA);
    expect((await a.select(a.patientProfiles).getSingle()).userId, 734);
  });

  test('D7 legacy backup cannot be relabelled into patient vault', () async {
    final oldDb = AppDatabase(NativeDatabase.memory());
    final vault = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(oldDb.close);
    addTearDown(vault.close);
    await seed(oldDb, 1);
    await seed(vault, 734);
    final legacy = await LocalBackup.exportJson(oldDb);
    await expectLater(
      LocalBackup.restoreVaultJson(vault, legacy), throwsFormatException,
    );
    expect(() => LocalBackup.exportJson(vault), throwsStateError);
    await expectLater(
      LocalBackup.restoreJson(vault, legacy), throwsStateError,
    );
    final scoped = await LocalBackup.exportVaultJson(vault);
    await expectLater(
      LocalBackup.restoreJson(oldDb, scoped), throwsFormatException,
    );
    expect((await oldDb.select(oldDb.patientProfiles).getSingle()).userId, 1);
    expect((await vault.select(vault.patientProfiles).getSingle()).userId, 734);
  });

  test('D7 destructive legacy restore refuses mismatched account', () async {
    final oldDb = AppDatabase(NativeDatabase.memory());
    final other = AppDatabase(NativeDatabase.memory());
    addTearDown(oldDb.close);
    addTearDown(other.close);
    await seed(oldDb, 734);
    await seed(other, 812);
    final backup = await LocalBackup.exportJson(oldDb);
    await expectLater(
      LocalBackup.restoreJson(other, backup), throwsStateError,
    );
    expect((await other.select(other.patientProfiles).getSingle()).userId, 812);
  });


  test('D7 spoofed vault name cannot relabel A profile as B', () async {
    final a = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    final emptyB = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(812),
    );
    addTearDown(a.close);
    addTearDown(emptyB.close);
    await seed(a, 734);
    final original = jsonDecode(await LocalBackup.exportVaultJson(a))
        as Map<String, dynamic>;
    original['vaultName'] = PatientVaultScope.nativeDjango(812).databaseName;
    await expectLater(
      LocalBackup.restoreVaultJson(emptyB, jsonEncode(original)),
      throwsFormatException,
    );
    expect(await emptyB.select(emptyB.patientProfiles).get(), isEmpty);
  });

  test('D7 native vault refuses a foreign profile at export', () async {
    final wrong = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(812),
    );
    addTearDown(wrong.close);
    await seed(wrong, 734);
    await expectLater(LocalBackup.exportVaultJson(wrong), throwsStateError);
  });

  test('D7 ambiguous legacy export refuses multiple owners', () async {
    final db = AppDatabase(NativeDatabase.memory());
    addTearDown(db.close);
    await seed(db, 734);
    await seed(db, 812);
    await expectLater(LocalBackup.exportJson(db), throwsStateError);
  });
}
