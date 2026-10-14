import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 native patients are separated from each other and legacy vault', () {
    final a = PatientVaultScope.nativeDjango(734).databaseName;
    final b = PatientVaultScope.nativeDjango(812).databaseName;
    expect(a, isNot(b));
    expect(a, PatientVaultScope.nativeDjango(734).databaseName);
    expect(a, isNot('amina'));
    expect(b, isNot('amina'));
    expect(a, isNot(PatientVaultScope.auditOnly().databaseName));
    expect(() => PatientVaultScope.nativeDjango(0), throwsArgumentError);
    expect(() => PatientVaultScope.nativeDjango(-1), throwsArgumentError);
  });

  test('D7 device UUID scope never collides with native/audit', () {
    const deviceA = 'b32afafd-8d9d-4ad4-8513-7dcfb54299a6';
    const deviceB = 'b32afafd-8d9d-4ad4-8513-7dcfb54299a7';
    final a = PatientVaultScope.deviceLocal(deviceA).databaseName;
    expect(a, PatientVaultScope.deviceLocal(deviceA.toUpperCase()).databaseName);
    expect(a, isNot(PatientVaultScope.deviceLocal(deviceB).databaseName));
    expect(a, isNot(PatientVaultScope.nativeDjango(734).databaseName));
    expect(a, isNot(PatientVaultScope.auditOnly().databaseName));
    expect(a, isNot('amina'));
  });

  test('D7 arbitrary strings may not select a vault', () {
    for (final value in [
      '', '1', 'native_734', 'amina', 'A@example.com', '../other',
      'b32afafd-8d9d-1ad4-8513-7dcfb54299a6',
      'b32afafd-8d9d-4ad4-0513-7dcfb54299a6',
    ]) {
      expect(() => PatientVaultScope.deviceLocal(value), throwsArgumentError);
    }
  });
}
