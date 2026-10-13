import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> seedPatient(AppDatabase db, int ownerId) async {
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: drift.Value(ownerId),
      updatedAt: DateTime.utc(2026, 10, 13),
      diabetesType: const drift.Value('type2'),
      treatment: const drift.Value('tablets'),
    ),
  );
}

void main() {
  test('D7 native owner writes never touch foreign rows in a poisoned vault', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await seedPatient(db, 812);
    await seedPatient(db, 734);

    expect(db.activeProfileRowId, 734);
    await db.setAiConsent(granted: true);
    final saved = await db.setRamadanPeriod(
      start: DateTime.utc(2026, 2, 18),
      end: DateTime.utc(2026, 3, 20),
    );
    expect(saved, isTrue);

    final alice = (await db.getProfileForLocalUserId(734))!;
    final bob = (await db.getProfileForLocalUserId(812))!;
    expect(alice.aiConsentGivenAt, isNotNull);
    expect(alice.ramadanStartDate, DateTime.utc(2026, 2, 18));
    expect(alice.ramadanEndDate, DateTime.utc(2026, 3, 20));
    expect(bob.aiConsentGivenAt, isNull);
    expect(bob.ramadanStartDate, isNull);
    expect(bob.ramadanEndDate, isNull);

    await db.setAiConsent(granted: false);
    expect((await db.getProfileForLocalUserId(734))!.aiConsentGivenAt, isNull);
    expect((await db.getProfileForLocalUserId(812))!.aiConsentGivenAt, isNull);
  });

  test('D7 native owner missing must not change another profile', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await seedPatient(db, 812);
    await db.setAiConsent(granted: true);
    final saved = await db.setRamadanPeriod(
      start: DateTime.utc(2026, 2, 18),
      end: DateTime.utc(2026, 3, 20),
    );
    expect(saved, isFalse);
    final foreign = (await db.getProfileForLocalUserId(812))!;
    expect(foreign.aiConsentGivenAt, isNull);
    expect(foreign.ramadanStartDate, isNull);
  });

  test('D7 device vault keeps its local row 1 distinct from native 1', () async {
    final device = AppDatabase.testPatientVault(
      NativeDatabase.memory(),
      PatientVaultScope.deviceLocal(
        'b32afafd-8d9d-4ad4-8513-7dcfb54299a6',
      ),
    );
    final native = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(1),
    );
    addTearDown(device.close);
    addTearDown(native.close);
    expect(device.activeProfileRowId, 1);
    expect(native.activeProfileRowId, 1);
    expect(
      device.patientVaultScope!.databaseName,
      isNot(native.patientVaultScope!.databaseName),
    );
    await seedPatient(device, 1);
    await seedPatient(native, 1);
    await device.setAiConsent(granted: true);
    expect((await device.getProfileForLocalUserId(1))!.aiConsentGivenAt,
        isNotNull);
    expect((await native.getProfileForLocalUserId(1))!.aiConsentGivenAt,
        isNull);
  });
}
