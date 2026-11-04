import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_progressive_demographics_store.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D18 optional personal information needs no medical onboarding', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    final store = PatientProgressiveDemographicsStore(db);
    expect(await store.read(), isNull);
    final result = await store.update(updateBirthYear: true, birthYear: 1994);
    expect(result.ownerId, 734);
    expect(result.birthYear, 1994);
    expect(result.genderIdentity, isNull);
    final newer = await store.update(
      updateGenderIdentity: true, genderIdentity: 'non_binary',
    );
    expect(newer.birthYear, 1994);
    expect(newer.genderIdentity, 'non_binary');
    final cleared = await store.update(
      updateGenderIdentity: true, genderIdentity: null,
    );
    expect(cleared.genderIdentity, isNull);
    expect(cleared.birthYear, 1994);
  });

  test('D18 invalid year and inferred biological identity fail closed', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    final store = PatientProgressiveDemographicsStore(db);
    await store.update(updateBirthYear: true, birthYear: 1988);
    for (final year in [1899, DateTime.now().year + 1]) {
      await expectLater(
        store.update(updateBirthYear: true, birthYear: year),
        throwsArgumentError,
      );
    }
    await expectLater(
      store.update(updateGenderIdentity: true,
        genderIdentity: 'clinical_biological_inference'),
      throwsArgumentError,
    );
    expect((await store.read())!.birthYear, 1988);
    expect((await store.read())!.genderIdentity, isNull);
  });

  test('D18 audit/legacy vaults cannot store sensitive declarations', () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    expect(() => PatientProgressiveDemographicsStore(legacy), throwsStateError);
    expect(() => PatientProgressiveDemographicsStore(audit), throwsStateError);
  });
}
