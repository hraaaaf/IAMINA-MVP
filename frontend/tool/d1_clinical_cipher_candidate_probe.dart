// Synthetic integration test entrypoint compiled with Flutter Web.
// Imports the actual AppDatabase/Drift schema through encrypted SQLite3MC.
import 'dart:convert';
import 'dart:html' as html;

import 'package:flutter/widgets.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/web_patient_vault_cipher_candidate.dart';

const _syntheticMarker = 'D1_SYNTHETIC_GLUCOSE_ONLY_735_XY';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
    'wrongRecoveryRejected': false,
    'ciphertextTamperRejected': false,
    'retiredKeyRejected': false,
    'actualDriftSchemaRoundTrip': false,
    'ownerIsolation': false,
  };
  try {
    final enrolledA = await candidate.enrollEmptyScope(a);
    final enrolledB = await candidate.enrollEmptyScope(b);
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
      'wrongRecoveryRejected', 'ciphertextTamperRejected',
      'retiredKeyRejected', 'actualDriftSchemaRoundTrip', 'ownerIsolation',
      'recoveredAfterClose',
    ].every((k) => proof[k] == true);
  } catch (error, stack) {
    proof['ok'] = false;
    proof['error'] = error.toString();
    proof['stack'] = stack.toString().split('\n').take(5).join('\n');
  }
  html.document.body?.text = jsonEncode(proof);
}