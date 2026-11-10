// D18-A CI-only: actual browser WebCrypto exercise of approved local key
// policy. Synthetic secret, temporary Chromium profile, NO patient data.
 // ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:flutter/widgets.dart';
import 'data/drift/d18_vault_key_policy.dart';
import 'data/drift/patient_vault_scope.dart';

const _pass = 'D18-SYNTHETIC-LOCAL-PASSPHRASE-2026';
const _next = 'D18-SYNTHETIC-NEW-PASSPHRASE-2026';
final _a = PatientVaultScope.deviceLocal(
  '7e0bb410-2c7f-4d3e-9b61-36f092c76210',
);
final _b = PatientVaultScope.deviceLocal(
  '7e0bb410-2c7f-4d3e-9b61-36f092c76211',
);
void _check(bool value, String message) {
  if (!value) throw StateError(message);
}
void _stage(String stage) {
  html.document.documentElement?.dataset['d18Stage'] = stage;
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  html.document.title = 'D18_KEY_PENDING';
  D18VaultKeyEnrollment? created;
  D18VaultKeyEnrollment? reset;
  try {
    _stage('create');
    created = await D18VaultKeyPolicy.createForEmptyVault(
      scope: _a, passphrase: _pass,
    );
    final original = await created.session.requireUnlockedKey().extractBytes();
    _check(original.length == 32, 'Wrong generated key length');
    _check(!created.publicEnvelopeJson.contains(_pass), 'Passphrase leaked');
    _check(!created.publicEnvelopeJson.contains(created.offlineRecoveryCode),
        'Offline recovery code leaked');

    _stage('passphrase_reopen');
    final opened = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      passphrase: _pass,
    );
    try {
      _check(
        (await opened.requireUnlockedKey().extractBytes()).join(',') ==
            original.join(','),
        'Passphrase yielded a different DEK',
      );
    } finally { opened.lock(); }
    _check(opened.isLocked, 'Session did not lock');

    _stage('wrong_passphrase');
    var rejected = false;
    try {
      final wrong = await D18VaultKeyPolicy.unlockWithPassphrase(
        scope: _a,
        publicEnvelopeJson: created.publicEnvelopeJson,
        passphrase: _next,
      );
      wrong.lock();
    } catch (_) { rejected = true; }
    _check(rejected, 'Wrong passphrase accepted');

    _stage('cross_vault_reject');
    rejected = false;
    try {
      final wrong = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _b,
        publicEnvelopeJson: created.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      );
      wrong.lock();
    } catch (_) { rejected = true; }
    _check(rejected, 'Recovery code crossed patient vault boundary');

    _stage('offline_recovery');
    final recovered = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
    );
    try {
      _check(
        (await recovered.requireUnlockedKey().extractBytes()).join(',') ==
            original.join(','),
        'Recovery code did not restore the same DEK',
      );
    } finally { recovered.lock(); }

    _stage('reset_after_recovery');
    reset = await D18VaultKeyPolicy.resetAfterRecovery(
      scope: _a,
      publicEnvelopeJson: created.publicEnvelopeJson,
      offlineRecoveryCode: created.offlineRecoveryCode,
      newPassphrase: _next,
    );
    _check(reset.offlineRecoveryCode != created.offlineRecoveryCode,
        'Recovery code was reused');
    _check(
      (await reset.session.requireUnlockedKey().extractBytes()).join(',') ==
          original.join(','),
      'Rewrapped data key changed during recovery',
    );

    _stage('reject_old_code_on_new_envelope');
    rejected = false;
    try {
      final wrong = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
        scope: _a,
        publicEnvelopeJson: reset.publicEnvelopeJson,
        offlineRecoveryCode: created.offlineRecoveryCode,
      );
      wrong.lock();
    } catch (_) { rejected = true; }
    _check(rejected, 'Old recovery code accepted with updated envelope');

    _stage('new_code_recovers');
    final newRecovery = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
      scope: _a,
      publicEnvelopeJson: reset.publicEnvelopeJson,
      offlineRecoveryCode: reset.offlineRecoveryCode,
    );
    try {
      _check(
        (await newRecovery.requireUnlockedKey().extractBytes()).join(',') ==
            original.join(','),
        'Rotated recovery code did not recover original DEK',
      );
    } finally { newRecovery.lock(); }

    _stage('complete');
    html.document.title = 'D18_KEY_PASS';
  } catch (e, st) {
    html.document.documentElement?.dataset['d18Error'] =
        e.toString().substring(0, e.toString().length.clamp(0, 450));
    html.document.title = 'D18_KEY_FAIL';
    debugPrint('D18_A_WEB_KEY_POLICY_ERROR $e');
    debugPrintStack(stackTrace: st);
  } finally {
    reset?.session.lock();
    created?.session.lock();
  }
}
