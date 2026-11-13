// Synthetic integration test entrypoint compiled with Flutter Web.
// Imports the actual AppDatabase/Drift schema through encrypted SQLite3MC.
import 'dart:convert';
import 'dart:html' as html;
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/services/web_vault_explicit_admission.dart';

import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/web_patient_vault_cipher_candidate.dart';

const _syntheticMarker = 'D1_SYNTHETIC_GLUCOSE_ONLY_735_XY';

class _AdmissionSignals extends ChangeNotifier {
  void changed() => notifyListeners();
}

Future<void> main() async {
  final a = PatientVaultScope.nativeDjango(735);
  final b = PatientVaultScope.nativeDjango(736);
  final candidate = WebPatientVaultCipherCandidate();
  final proof = <String, Object?>{
    'scope': 'synthetic AppDatabase schema + WebCrypto + sqlite3mc',
    'noRealPatients': true,
    'clinicalGo': false,
    'ownerABound': false,
    'ownerBBound': false,
    'ownerSwapRejected': false,
    'envelopeSwapRejected': false,
    'missingCipherRefused': false,
    'wrongRecoveryRejected': false,
    'ciphertextTamperRejected': false,
    'retiredKeyRejected': false,
    'actualDriftSchemaRoundTrip': false,
    'ownerIsolation': false,
    'explicitAdmissionLockedRefused': false,
    'explicitAdmissionOwnerSwapRefused': false,
    'explicitAdmissionRecovered': false,
    'explicitAdmissionEpochRaceDenied': false,
  };
  try {
    final enrolledA = await candidate.enrollEmptyScope(a);
    final enrolledB = await candidate.enrollEmptyScope(b);
    final headerAKey = WebPatientVaultCipherCandidate.diagnosticMetadataKey(a);
    final headerBKey = WebPatientVaultCipherCandidate.diagnosticMetadataKey(b);
    final originalB = html.window.localStorage[headerBKey]!;
    html.window.localStorage[headerBKey] =
        html.window.localStorage[headerAKey]!;
    try {
      await candidate.unlock(b, enrolledB.recoveryCode);
    } on StateError {
      proof['envelopeSwapRejected'] = true;
    } finally {
      html.window.localStorage[headerBKey] = originalB;
    }
    final keyA = await candidate.unlock(a, enrolledA.recoveryCode);
    final keyB = await candidate.unlock(b, enrolledB.recoveryCode);
    proof['ownerABound'] = keyA.cipherPassphraseFor(a) !=
        keyB.cipherPassphraseFor(b);
    proof['ownerBBound'] = keyB.cipherPassphraseFor(b).isNotEmpty;
    try {
      keyA.cipherPassphraseFor(b);
    } on StateError {
      proof['ownerSwapRejected'] = true;
    }
    try {
      await candidate.unlock(
        a, base64UrlEncode(List<int>.filled(32, 17)).replaceAll('=', ''));
    } on StateError {
      proof['wrongRecoveryRejected'] = true;
    }
    final raw = html.window.localStorage[
        WebPatientVaultCipherCandidate.diagnosticMetadataKey(a)]!;
    final envelope = jsonDecode(raw) as Map<String, dynamic>;
    envelope['ciphertext'] =
        base64UrlEncode(List<int>.filled(48, 77));
    html.window.localStorage[
        WebPatientVaultCipherCandidate.diagnosticMetadataKey(a)] =
        jsonEncode(envelope);
    try {
      await candidate.unlock(a, enrolledA.recoveryCode);
    } on StateError {
      proof['ciphertextTamperRejected'] = true;
    }
    html.window.localStorage[
        WebPatientVaultCipherCandidate.diagnosticMetadataKey(a)] = raw;

    final dbA = await candidate.openCandidateDatabase(a, keyA);
    try {
      final selectedCipher = await dbA.customSelect('PRAGMA cipher').get();
      proof['cipherMode'] = selectedCipher.isNotEmpty
          ? selectedCipher.first.data.values.first.toString() : 'missing';
      await dbA.customStatement(
        'INSERT INTO log_entries '
        '(created_at, blood_sugar, client_uuid) VALUES (?, ?, ?)',
        [DateTime.utc(2026, 11, 13).millisecondsSinceEpoch ~/ 1000,
          135.0, _syntheticMarker],
      );
      final rows = await dbA.customSelect(
        'SELECT client_uuid FROM log_entries WHERE blood_sugar = 135.0',
      ).get();
      proof['actualDriftSchemaRoundTrip'] =
          rows.length == 1 && rows.single.read<String>('client_uuid') ==
              _syntheticMarker;
    } finally {
      await dbA.close();
    }

    final dbB = await candidate.openCandidateDatabase(b, keyB);
    try {
      final rows = await dbB.customSelect('SELECT * FROM log_entries').get();
      proof['ownerIsolation'] = rows.isEmpty;
    } finally {
      await dbB.close();
    }

    // After a cold database reopen the owner can recover A's own record.
    final recoveredA = await candidate.unlock(a, enrolledA.recoveryCode);
    final reopenedA = await candidate.openCandidateDatabase(a, recoveredA);
    try {
      final rows = await reopenedA.customSelect(
        'SELECT client_uuid FROM log_entries',
      ).get();
      proof['recoveredAfterClose'] = rows.length == 1 &&
          rows.single.read<String>('client_uuid') == _syntheticMarker;
    } finally {
      await reopenedA.close();
    }
    // A sealed header without persisted ciphertext must never cause a new
    // empty clinical database to be silently created.
    final lost = PatientVaultScope.nativeDjango(737);
    final enrolledLost = await candidate.enrollEmptyScope(lost);
    final lostHeaderKey =
        WebPatientVaultCipherCandidate.diagnosticMetadataKey(lost);
    final lostHeader =
        jsonDecode(html.window.localStorage[lostHeaderKey]!) as Map<String, dynamic>;
    lostHeader['state'] = 'sealed';
    html.window.localStorage[lostHeaderKey] = jsonEncode(lostHeader);
    final lostKey = await candidate.unlock(lost, enrolledLost.recoveryCode);
    try {
      await candidate.openCandidateDatabase(lost, lostKey);
    } on StateError {
      proof['missingCipherRefused'] = true;
    } finally {
      lostKey.retire();
    }
    // D1 guarded admission must use the REAL encrypted SQLite3MC opener,
    // never unencrypted AppDatabase.forPatientVault, and the code must come
    // explicitly from the owner. No key/ciphertext/code goes into this proof.
    final changes = _AdmissionSignals();
    var currentNative = 735;
    var unlocked = false;
    var sessionEpoch = 0;
    Future<AppDatabase> openForOwner(
        PatientVaultScope scope, String explicitRecoveryCode) async {
      final key = await candidate.unlock(scope, explicitRecoveryCode);
      try {
        return await candidate.openCandidateDatabase(scope, key);
      } finally {
        key.retire();
      }
    }
    final gate = WebVaultExplicitAdmission(
      sessionChanges: changes,
      identity: () => (
        authenticated: true,
        appLockInitialized: true,
        appLockConfigured: true,
        appLockUnlocked: unlocked,
        appLockRecoveryRequired: false,
        remoteCredentialVerified: true,
        hasRemoteCredential: true,
        nativeAccountId: currentNative,
      ),
      resolveScope: () async => PatientVaultScope.nativeDjango(currentNative),
      encryptedOpener: openForOwner,
      authEpoch: () => sessionEpoch,
    );
    try {
      try {
        final unexpected = await gate.openWithExplicitRecovery(
          scope: a, recoveryCode: enrolledA.recoveryCode,
        );
        await unexpected.close();
      } on StateError {
        proof['explicitAdmissionLockedRefused'] = true;
      }
      unlocked = true;
      currentNative = 736;
      changes.changed();
      try {
        final unexpected = await gate.openWithExplicitRecovery(
          scope: a, recoveryCode: enrolledA.recoveryCode,
        );
        await unexpected.close();
      } on StateError {
        proof['explicitAdmissionOwnerSwapRefused'] = true;
      }
      currentNative = 735;
      changes.changed();
      final guardedA = await gate.openWithExplicitRecovery(
        scope: a, recoveryCode: enrolledA.recoveryCode,
      );
      try {
        final records = await guardedA.customSelect(
          'SELECT client_uuid FROM log_entries',
        ).get();
        proof['explicitAdmissionRecovered'] = records.length == 1 &&
            records.single.read<String>('client_uuid') == _syntheticMarker;
      } finally {
        await guardedA.close();
      }

      final started = Completer<void>();
      final late = Completer<AppDatabase>();
      final raceGate = WebVaultExplicitAdmission(
        sessionChanges: changes,
        identity: () => (
          authenticated: true,
          appLockInitialized: true,
          appLockConfigured: true,
          appLockUnlocked: unlocked,
          appLockRecoveryRequired: false,
          remoteCredentialVerified: true,
          hasRemoteCredential: true,
          nativeAccountId: currentNative,
        ),
        resolveScope: () async => a,
        authEpoch: () => sessionEpoch,
        encryptedOpener: (scope, code) {
          started.complete();
          return late.future;
        },
      );
      try {
        final attempt = raceGate.openWithExplicitRecovery(
          scope: a, recoveryCode: enrolledA.recoveryCode,
        );
        await started.future;
        final lateKey = await candidate.unlock(a, enrolledA.recoveryCode);
        final stale = await candidate.openCandidateDatabase(a, lateKey);
        lateKey.retire();
        unlocked = false;
        sessionEpoch++;
        changes.changed();
        late.complete(stale);
        try {
          final unexpected = await attempt;
          await unexpected.close();
        } on StateError {
          proof['explicitAdmissionEpochRaceDenied'] = true;
        }
      } finally {
        raceGate.dispose();
      }
    } finally {
      gate.dispose();
      changes.dispose();
    }

    keyA.retire();
    try {
      keyA.cipherPassphraseFor(a);
    } on StateError {
      proof['retiredKeyRejected'] = true;
    }
    keyB.retire();
    recoveredA.retire();

    proof['ok'] = [
      'ownerABound', 'ownerBBound', 'ownerSwapRejected',
      'envelopeSwapRejected', 'missingCipherRefused',
      'wrongRecoveryRejected', 'ciphertextTamperRejected',
      'retiredKeyRejected', 'actualDriftSchemaRoundTrip', 'ownerIsolation',
      'recoveredAfterClose',
      'explicitAdmissionLockedRefused',
      'explicitAdmissionOwnerSwapRefused',
      'explicitAdmissionRecovered',
      'explicitAdmissionEpochRaceDenied',
    ].every((k) => proof[k] == true) && proof['cipherMode'] == 'chacha20';
  } catch (error, stack) {
    proof['ok'] = false;
    proof['error'] = error.toString();
    proof['stack'] = stack.toString().split('\n').take(5).join('\n');
  }
  html.document.body?.text = jsonEncode(proof);
}