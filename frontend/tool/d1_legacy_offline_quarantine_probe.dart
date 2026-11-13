// D1 P0 adversarial-only browser probe. All identities/readings are synthetic.
// This DOES NOT stop already-installed offline PWA writers or authorize patients.
import 'dart:convert';
import 'dart:html' as html;
import 'dart:js_interop';

import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/web_patient_vault_cipher_candidate.dart';

@JS('IaminaD1CryptoCandidate.indexedDbNames')
external JSPromise<JSString> _indexedDbNames();

Future<void> main() async {
  final scope = PatientVaultScope.nativeDjango(745);
  final candidate = WebPatientVaultCipherCandidate();
  final proof = <String, Object?>{
    'scope': 'synthetic late legacy/offline writer quarantine',
    'clinicalGo': false,
    'encryptedBeforeOldWriter': false,
    'tamperedPendingHeaderRejected': false,
    'lateLegacyRejected': false,
    'legacyStorePreserved': false,
    'otherOwnerEnrollmentDenied': false,
    'ciphertextPreserved': false,
    'result': 'NOT_RUN',
  };
  WebVaultKey? key;
  try {
    final enrollment = await candidate.enrollEmptyScope(scope);
    key = await candidate.unlock(scope, enrollment.recoveryCode);
    final db = await candidate.openCandidateDatabase(scope, key);
    try {
      await db.customStatement(
        'INSERT INTO log_entries (created_at, blood_sugar, client_uuid) '
        'VALUES (?, ?, ?)',
        [DateTime.utc(2026, 11, 13).millisecondsSinceEpoch ~/ 1000,
          135.0, 'D1_SYNTHETIC_OFFLINE_OLD_WRITER_745'],
      );
    } finally {
      await db.close();
    }
    final before = jsonDecode((await _indexedDbNames().toDart).toDart) as List;
    proof['encryptedBeforeOldWriter'] = before.contains(
      WebPatientVaultCipherCandidate.diagnosticStoreName(scope),
    );
    // The first open sealed the envelope. A localStorage attacker must not
    // be able to flip the unauthenticated 'state' back to 'pending' to reuse
    // the one-time database-creation grant (including after browser restart).
    final headerKey =
        WebPatientVaultCipherCandidate.diagnosticMetadataKey(scope);
    final sealedHeader = html.window.localStorage[headerKey]!;
    final replay = jsonDecode(sealedHeader) as Map<String, dynamic>;
    replay['state'] = 'pending';
    html.window.localStorage[headerKey] = jsonEncode(replay);
    try {
      final unintended = await candidate.openCandidateDatabase(scope, key);
      await unintended.close();
    } on StateError catch (error) {
      proof['tamperedPendingHeaderRejected'] =
          error.message == 'web_vault_pending_enrollment_replay_blocked';
    } finally {
      html.window.localStorage[headerKey] = sealedHeader;
    }

    // Browser test writes an old 'amina' IndexedDB store OFFLINE after
    // encryption enrollment, then explicitly clicks to continue. Never
    // insert synthetic plaintext into the candidate encrypted database.
    final trigger = html.ButtonElement()
      ..id = 'd1-late-legacy-probe-trigger'
      ..text = 'Continue synthetic offline legacy test';
    html.document.body!.append(trigger);
    await trigger.onClick.first;
    trigger.remove();

    try {
      final unexpected = await candidate.openCandidateDatabase(scope, key);
      await unexpected.close();
    } on StateError catch (error) {
      proof['lateLegacyRejected'] =
          error.message == 'web_vault_legacy_data_quarantined';
    }
    final after = jsonDecode((await _indexedDbNames().toDart).toDart) as List;
    proof['legacyStorePreserved'] =
        after.contains('amina_vault_v1_native_999');
    try {
      await candidate.enrollEmptyScope(PatientVaultScope.nativeDjango(746));
    } on StateError catch (error) {
      proof['otherOwnerEnrollmentDenied'] =
          error.message == 'web_vault_legacy_data_quarantined';
    }
    proof['ciphertextPreserved'] = after.contains(
      WebPatientVaultCipherCandidate.diagnosticStoreName(scope),
    );
    proof['result'] = [
      'encryptedBeforeOldWriter', 'tamperedPendingHeaderRejected',
      'lateLegacyRejected',
      'legacyStorePreserved', 'otherOwnerEnrollmentDenied',
      'ciphertextPreserved',
    ].every((field) => proof[field] == true) ? 'PASS' : 'FAIL';
  } catch (error) {
    proof['result'] = 'FAIL';
    proof['error'] = error.toString();
  } finally {
    key?.retire();
    html.document.body?.text = jsonEncode(proof);
  }
}
