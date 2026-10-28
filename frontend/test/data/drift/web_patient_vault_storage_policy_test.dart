import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W02 Web refuses persistent Django patient vaults by default', () {
    for (final patientId in [1, 734, 812]) {
      final scope = PatientVaultScope.nativeDjango(patientId);
      expect(
        allowUnencryptedPatientVaultForPlatform(scope, isWeb: true),
        isFalse,
      );
      expect(
        allowUnencryptedPatientVaultForPlatform(scope, isWeb: false),
        isTrue,
      );
    }
  });

  test('W02 Web also refuses device-local clinical vaults', () {
    final scope = PatientVaultScope.deviceLocal(
      'b32afafd-8d9d-4ad4-8513-7dcfb54299a6',
    );
    expect(
      allowUnencryptedPatientVaultForPlatform(scope, isWeb: true),
      isFalse,
    );
    expect(
      allowUnencryptedPatientVaultForPlatform(scope, isWeb: false),
      isTrue,
    );
  });

  test('W02 synthetic audit vault remains isolated and testable on Web', () {
    final scope = PatientVaultScope.auditOnly();
    expect(
      allowUnencryptedPatientVaultForPlatform(scope, isWeb: true),
      isTrue,
    );
    expect(scope.databaseName, isNot('amina'));
    expect(
      scope.databaseName,
      isNot(PatientVaultScope.nativeDjango(734).databaseName),
    );
  });

  test('W02 actual Web constructor fails before opening a patient database', () {
    if (!kIsWeb) return;
    expect(
      () => AppDatabase.forPatientVault(
        PatientVaultScope.nativeDjango(734),
      ),
      throwsA(isA<StateError>().having(
        (error) => error.message,
        'message',
        'encrypted_web_patient_vault_unavailable',
      )),
    );
  });
}
