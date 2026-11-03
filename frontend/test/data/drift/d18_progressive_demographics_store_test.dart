import 'dart:convert';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/local_backup.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<AppDatabase> _vault(int id) async {
  final db = AppDatabase.testPatientVault(
    NativeDatabase.memory(), PatientVaultScope.nativeDjango(id),
  );
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(id), preferredLanguage: const drift.Value('fr'),
      updatedAt: DateTime.utc(2026, 10, 15),
    ),
  );
  return db;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D18 optional fields are untouched until patient edits', () async {
    final a = await _vault(734), b = await _vault(812);
    addTearDown(a.close);
    addTearDown(b.close);
    final store = PatientProgressiveDemographicsStore(a);
    expect(await store.read(), isNull);
    expect(await PatientProgressiveDemographicsStore(b).read(), isNull);

    final year = await store.update(updateBirthYear: true, birthYear: 1994);
    expect(year.birthYear, 1994);
    expect(year.genderIdentity, isNull);
    expect(year.provenance, 'patient_declared');

    final identity = await store.update(
      updateGenderIdentity: true, genderIdentity: 'non_binary',
    );
    expect(identity.birthYear, 1994);
    expect(identity.genderIdentity, 'non_binary');
    expect((await PatientProgressiveDemographicsStore(b).read()), isNull);

    final cleared = await store.update(updateBirthYear: true, birthYear: null);
    expect(cleared.birthYear, isNull);
    expect(cleared.genderIdentity, 'non_binary');
    final allCleared = await store.update(
      updateGenderIdentity: true, genderIdentity: null,
    );
    expect(allCleared.birthYear, isNull);
    expect(allCleared.genderIdentity, isNull);
  });

  test('D18 invalid ages and inferred gender cannot mutate data', () async {
    final db = await _vault(734);
    addTearDown(db.close);
    final store = PatientProgressiveDemographicsStore(db);
    await store.update(updateBirthYear: true, birthYear: 1990);
    for (final bad in [1899, DateTime.now().toUtc().year + 1]) {
      await expectLater(
        store.update(updateBirthYear: true, birthYear: bad),
        throwsArgumentError,
      );
    }
    await expectLater(
      store.update(
        updateGenderIdentity: true, genderIdentity: 'biological_inference',
      ),
      throwsArgumentError,
    );
    await expectLater(store.update(), throwsArgumentError);
    expect((await store.read())?.birthYear, 1990);
    expect((await store.read())?.genderIdentity, isNull);
  });

  test('D18 legacy and audit scopes cannot store optional patient facts',
      () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    expect(() => PatientProgressiveDemographicsStore(legacy), throwsStateError);
    expect(() => PatientProgressiveDemographicsStore(audit), throwsStateError);
  });

  test('D18 demographics and weight backup survive same-owner roundtrip',
      () async {
    final a = await _vault(734);
    final restored = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(a.close);
    addTearDown(restored.close);
    await PatientProgressiveDemographicsStore(a).update(
      updateBirthYear: true, birthYear: 1989,
      updateGenderIdentity: true, genderIdentity: 'woman',
    );
    final backup = await LocalBackup.exportVaultJson(a);
    final root = jsonDecode(backup) as Map<String, dynamic>;
    expect(root['demographicsFormatVersion'], 1);
    expect(root['demographicDeclarations'], hasLength(1));
    await LocalBackup.restoreVaultJson(restored, backup);
    final value = await PatientProgressiveDemographicsStore(restored).read();
    expect(value?.birthYear, 1989);
    expect(value?.genderIdentity, 'woman');
    expect(value?.ownerId, 734);
  });

  test('D18 forged other-account declaration rejected before restore',
      () async {
    final a = await _vault(734);
    final dest = await _vault(734);
    addTearDown(a.close);
    addTearDown(dest.close);
    await PatientProgressiveDemographicsStore(a).update(
      updateBirthYear: true, birthYear: 1989,
    );
    await PatientProgressiveDemographicsStore(dest).update(
      updateBirthYear: true, birthYear: 1972,
    );
    final root = jsonDecode(await LocalBackup.exportVaultJson(a))
        as Map<String, dynamic>;
    (root['demographicDeclarations'] as List).first['user_id'] = 812;
    await expectLater(
      LocalBackup.restoreVaultJson(dest, jsonEncode(root)),
      throwsFormatException,
    );
    expect((await PatientProgressiveDemographicsStore(dest).read())?.birthYear,
        1972);
  });

  test('D18 legacy scoped backup cannot overwrite new declarations',
      () async {
    final db = await _vault(734);
    addTearDown(db.close);
    await PatientProgressiveDemographicsStore(db).update(
      updateBirthYear: true, birthYear: 1985,
    );
    final old = jsonDecode(await LocalBackup.exportVaultJson(db))
        as Map<String, dynamic>;
    old.remove('demographicsFormatVersion');
    old.remove('demographicDeclarations');
    await expectLater(
      LocalBackup.restoreVaultJson(db, jsonEncode(old)),
      throwsStateError,
    );
    expect((await PatientProgressiveDemographicsStore(db).read())?.birthYear,
        1985);
  });
}
