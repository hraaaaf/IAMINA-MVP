import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _source(String path) => File(path).readAsStringSync();

void main() {
  test('D7 profile and onboarding write local vault before CAS synchronizer', () {
    final profile = _source('lib/features/profile/profile_screen.dart');
    final onboarding = _source('lib/features/auth/onboarding_chat_screen.dart');
    for (final source in [profile, onboarding]) {
      expect(source, contains('PatientTreatmentDeclarationStore(db).write('));
      expect(source, contains('sendPendingTreatmentDeclaration()'));
      expect(source, isNot(contains('_declaredTreatments.toApiPatch()')));
      expect(source, contains('hasRemoteApiCredential'));
      expect(source, contains('nativeDjangoUserId != null'));
    }
    // Limit ordering to the save handler: conflict-resolution UI also calls
    // the synchronizer, but cannot replace the local-first save invariant.
    final profileSave = profile.substring(profile.indexOf('  void _saveProfile() async {'));
    expect(profileSave.indexOf('PatientTreatmentDeclarationStore(db).write('),
        lessThan(profileSave.indexOf('sendPendingTreatmentDeclaration()')));
    expect(onboarding.indexOf('PatientTreatmentDeclarationStore(db).write('),
        lessThan(onboarding.indexOf('sendPendingTreatmentDeclaration()')));
  });

  test('D7 onboarding never fabricates profile to bypass first-use restoration', () {
    final onboarding = _source('lib/features/auth/onboarding_chat_screen.dart');
    expect(onboarding, contains('insertOnConflictUpdate(profile)'));
    expect(onboarding, contains('restorePatientTreatmentDeclaration()'));
    expect(onboarding, contains('!_treatmentTouched'));
    expect(
      onboarding.indexOf('insertOnConflictUpdate(profile)'),
      lessThan(onboarding.indexOf('restorePatientTreatmentDeclaration()')),
    );
  });

  test('D7 offline profile save cannot present a remote-success receipt', () {
    final profile = _source('lib/features/profile/profile_screen.dart');
    expect(profile, contains('remoteMirrorConfirmed = false;'));
    expect(profile, contains('AminaTheme.warningOrange'));
    expect(profile, contains('Synchronisation non confirmée.'));
    expect(profile, contains('remoteMirrorConfirmed ='));
  });
}
