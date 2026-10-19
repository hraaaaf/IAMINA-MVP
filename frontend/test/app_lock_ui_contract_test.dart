import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('patient enrollment continues into strong app-lock setup', () {
    final enrollment = File(
      'lib/features/auth/local_device_enrollment_screen.dart',
    ).readAsStringSync();
    final router = File('lib/routes/app_router.dart').readAsStringSync();

    expect(enrollment, contains("kIaminaPreviewSameOriginApi"));
    expect(enrollment, contains("'/w01-preview'"));
    expect(enrollment, contains("'/app-lock/setup'"));
    expect(router, contains("initialLocation: kIaminaPreviewSameOriginApi"));
    expect(router, contains("path: '/app-lock/setup'"));
    expect(router, contains("path: '/app-lock/unlock'"));
    expect(router, contains('activeLock.recoveryRequired'));
    expect(router, contains('!activeLock.isConfigured'));
    expect(router, contains('!activeLock.isUnlocked'));
  });

  test('app-lock UI exposes no weak patient bypass', () {
    final setup = File(
      'lib/features/auth/app_lock_setup_screen.dart',
    ).readAsStringSync();
    final unlock = File(
      'lib/features/auth/app_lock_unlock_screen.dart',
    ).readAsStringSync();

    for (final weakSecret in <String>[
      'password',
      'mot de passe',
      'code PIN',
      'forgot',
    ]) {
      expect(setup.toLowerCase(), isNot(contains(weakSecret.toLowerCase())));
      expect(unlock.toLowerCase(), isNot(contains(weakSecret.toLowerCase())));
    }
    expect(unlock, contains('if (!recovery)'));
    expect(unlock, contains('recoveryRequired'));
    expect(unlock, contains("appLockPreview'] == 'recovery'"));
    // Optional exploration is scoped to W01 preview and NEVER unlocks a vault.
    expect(setup, contains('kIaminaPreviewSameOriginApi'));
    expect(unlock, contains('kIaminaPreviewSameOriginApi'));
    expect(setup, contains("context.go('/w01-preview')"));
    expect(unlock, contains("context.go('/w01-preview')"));
    final router = File('lib/routes/app_router.dart').readAsStringSync();
    final readOnly = File('lib/features/auth/w01_read_only_preview_screen.dart').readAsStringSync();
    expect(router, contains("kIaminaPreviewSameOriginApi ? null : '/login'"));
    expect(router, contains('activeLock.recoveryRequired'));
    expect(router, contains('!activeLock.isUnlocked'));
    expect(readOnly, isNot(contains("import '../../data/drift/")));
    expect(readOnly, isNot(contains("import '../../services/api_client.dart'")));
    expect(unlock, contains('appLockRecoveryReauthenticate'));
    expect(unlock, contains('appLockRecoveryReenroll'));
    expect(unlock, contains('recoverWithVerifiedRemoteAccount()'));
  });

  test('missing app-lock state is cross-checked against all local patient state', () {
    final mainSource = File('lib/main.dart').readAsStringSync();
    final serviceSource = File(
      'lib/services/app_lock_service.dart',
    ).readAsStringSync();

    expect(mainSource, contains('protectedLocalStateProbe:'));
    expect(mainSource, contains('authService.isAuthenticated'));
    // D7 extraction: the presence check now lives in a separate security
    // helper; inspecting only main.dart would miss the real protection.
    final vaultProbe = File(
      'lib/services/medical_vault_protected_state.dart',
    ).readAsStringSync();
    expect(mainSource, contains('hasProtectedMedicalVaultRows('));
    expect(mainSource, contains('AppDatabase.forPatientVault(scope)'));
    expect(mainSource, contains('legacyProtected || currentVaultProtected'));
    for (final table in <String>[
      'patientProfiles',
      'logEntries',
      'chatMessages',
      'medicationEvents',
      'reminders',
    ]) {
      expect(vaultProbe, contains('db.$table'));
    }
    expect(vaultProbe, contains('patient_treatment_declarations_v1'));
    expect(serviceSource, contains('await _hasProtectedLocalState()'));
    expect(serviceSource, contains('_recoveryRequired = true;'));
    expect(serviceSource, contains('return true;'));
  });

  test('WebAuthn bridge requires local user verification and exact binding', () {
    final source = File('web/iamina_app_lock.js').readAsStringSync();

    expect(source, contains("userVerification: 'required'"));
    expect(source, contains("authenticatorAttachment: 'platform'"));
    expect(source, contains("attestation: 'none'"));
    expect(source, contains("parsed.origin !== location.origin"));
    expect(source, contains("stored.origin !== location.origin"));
    expect(source, contains("stored.rpId !== location.hostname"));
    expect(source, contains('rp_id_hash_mismatch'));
    expect(source, contains('user_presence_missing'));
    expect(source, contains('user_verification_missing'));
    expect(source, contains('crypto.subtle.verify'));
    expect(source, contains('signature_counter_rollback'));
  });

  test('WebAuthn bridge has no application-network primitive', () {
    final source = File('web/iamina_app_lock.js').readAsStringSync();

    expect(source, isNot(contains('fetch(')));
    expect(source, isNot(contains('XMLHttpRequest')));
    expect(source, isNot(contains('WebSocket')));
    expect(source, isNot(contains('EventSource')));
  });

  test('audit preview is compile-time and loopback constrained', () {
    final setup = File(
      'lib/features/auth/app_lock_setup_screen.dart',
    ).readAsStringSync();
    final auditPolicy = File(
      'lib/services/audit_access_policy.dart',
    ).readAsStringSync();

    expect(setup, contains('AuditAccessPolicy.isAllowed(Uri.base)'));
    expect(auditPolicy, contains("'IAMINA_AUDIT_ACCESS'"));
    expect(auditPolicy, contains("defaultValue: false"));
    expect(auditPolicy, contains("host == 'localhost'"));
    expect(auditPolicy, contains("host == '127.0.0.1'"));
  });
}
