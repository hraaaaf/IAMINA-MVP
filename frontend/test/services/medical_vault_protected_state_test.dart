import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/medical_vault_protected_state.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 empty named patient vault permits new lock enrollment', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    expect(await hasProtectedMedicalVaultRows(db), isFalse);
  });

  test('D7 existing account profile requires app-lock recovery', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value(null),
      ),
    );
    expect(await hasProtectedMedicalVaultRows(db), isTrue);
  });

  test('D7 ownerless pending log also protects local state', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await db.into(db.logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: DateTime.utc(2026, 10, 13),
        bloodSugar: 120,
        clientUuid: 'd7-protected-state-log-0001',
      ),
    );
    expect(await hasProtectedMedicalVaultRows(db), isTrue);
  });
}
