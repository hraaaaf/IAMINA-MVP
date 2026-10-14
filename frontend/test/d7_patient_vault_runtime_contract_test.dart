import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String source(String path) => File(path).readAsStringSync();

void main() {
  test('D7 app never injects pre-D7 mixed DB into a patient Provider', () {
    final main = source('lib/main.dart');
    final host = source('lib/services/patient_vault_app_host.dart');
    expect(main, contains('final legacy = AppDatabase.defaults();'));
    expect(main, contains('await legacy.close();'));
    expect(main, contains('PatientVaultSessionController.forAuth(authService)'));
    expect(main, isNot(contains('db.watchProfile()')));
    expect(host, contains('ConsentEvidenceStore.forPatientVault(scope)'));
    expect(host, contains('bundle.db.watchProfileForLocalUserId('));
    expect(host, contains('ValueKey(\'d7-patient-vault-'));
    expect(host, contains('bundle.authEpoch == AuthService.authEpoch'));
    expect(host, contains('widget.controller.activeDatabase == bundle.db'));
  });

  test('D7 treatment declarations are patient owned and optional', () {
    final onboarding = source('lib/features/auth/onboarding_chat_screen.dart');
    final profile = source('lib/features/profile/profile_screen.dart');
    final presentation =
        source('lib/features/profile/profile_screen_presentation.dart');
    expect(onboarding, contains('MedicalTreatmentMultiSelector('));
    expect(onboarding, contains('PatientTreatmentDeclarationStore(db).write('));
    expect(onboarding, isNot(contains('firebaseUser?.uid.hashCode.abs()')));
    expect(onboarding, contains('final ready = _language != null && _country != null;'));
    expect(profile, contains('PatientTreatmentDeclarationStore(db).write('));
    expect(presentation, contains('MedicalTreatmentMultiSelector('));
  });
}
