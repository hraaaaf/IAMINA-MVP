import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String source(String path) => File(path).readAsStringSync();

void main() {
  test('D9 native owner first-use verification is before patient-facing routes',
      () {
    final host = source('lib/services/patient_vault_app_host.dart');
    final consent = source('lib/services/consent_service.dart');
    expect(host, contains('profile == null && scope.nativeDjangoUserId != null'));
    expect(host, contains('widget.appLock.isUnlocked'));
    expect(host, contains('widget.auth.boundNativeAccountId == scope.nativeDjangoUserId'));
    expect(host, contains('current.consent.adoptVerifiedD9FirstUseProof('));
    expect(host, contains('current.d9Gate = _D9FirstUseGate.unavailable'));
    expect(host, contains('current.d9Gate = _D9FirstUseGate.newPatient'));
    expect(host, contains('return _buildD9VerificationGate(bundle)'));
    expect(host, contains('lockNonce != _d9LockNonce'));
    expect(host, contains('widget.controller.activeDatabase != current.db'));
    expect(consent, contains('profile != null || _d9VerifiedRemoteCompletion'));
    expect(consent, contains('proof.ownerUserId != activeOwner'));
    expect(consent, contains('_hasVerifiedEvidence'));
    expect(host, isNot(contains('.into(db.patientProfiles)')));
  });

  test('D9 local explicit save precedes server confirmation, no clinical POST',
      () {
    final onboarding = source('lib/features/auth/onboarding_chat_screen.dart');
    final readTransport = onboarding.indexOf(
      'final d9Transport = _optionalD9Transport(context);',
    );
    final localSave = onboarding.indexOf('.insertOnConflictUpdate(profile)');
    final remoteAck = onboarding.indexOf('d9Transport.confirmSavedFirstUse()');
    expect(readTransport, greaterThanOrEqualTo(0));
    expect(localSave, greaterThan(readTransport));
    expect(remoteAck, greaterThan(localSave));
    expect(onboarding, isNot(contains('patchProfile({')));
    expect(onboarding, contains('if (ack == null && mounted'));
    expect(onboarding, contains('Reprise sur un autre appareil non confirmée'));
  });

  test('D9 fail-closed gate permits a retry AND safe logout when offline',
      () {
    final host = source('lib/services/patient_vault_app_host.dart');
    expect(host, contains('D9FirstUseGate.unavailable'));
    expect(host, contains('onPressed: () => unawaited(_verifyD9FirstUse())'));
    expect(host, contains('onPressed: () => unawaited(widget.auth.signOut())'));
    expect(host, contains('if (widget.appLock.isUnlocked &&'));
    expect(host, contains('Vérification sécurisée du compte'));
  });
}
