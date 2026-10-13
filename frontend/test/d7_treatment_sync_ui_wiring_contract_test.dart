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
    expect(profile.indexOf('PatientTreatmentDeclarationStore(db).write('),
        lessThan(profile.indexOf('sendPendingTreatmentDeclaration()')));
    expect(onboarding.indexOf('PatientTreatmentDeclarationStore(db).write('),
        lessThan(onboarding.indexOf('sendPendingTreatmentDeclaration()')));
  });

  test('D7 offline profile save cannot present a remote-success receipt', () {
    final profile = _source('lib/features/profile/profile_screen.dart');
    expect(profile, contains('remoteMirrorConfirmed = false;'));
    expect(profile, contains('AminaTheme.warningOrange'));
    expect(profile, contains('Synchronisation non confirmée.'));
    expect(profile, contains('remoteMirrorConfirmed ='));
  });
}
