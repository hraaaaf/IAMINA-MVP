// D1 experimental encrypted backup/restoration fixture. Synthetic ONLY.
// Not a product backup feature, not a patient-data path, no clinical GO.
// Recovery code temporarily passed through sessionStorage ONLY for this
// isolated CI fixture; never use this mechanism for real patients.
import 'dart:convert';
import 'dart:html' as html;

import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/web_patient_vault_cipher_candidate.dart';

const marker = 'D1_SYNTHETIC_FRESH_PROFILE_RECOVERY_755';

Future<void> main() async {
  final scope = PatientVaultScope.nativeDjango(755);
  final candidate = WebPatientVaultCipherCandidate();
  final phase = Uri.base.queryParameters['phase'];
  final result = <String, Object?>{
    'scope': 'synthetic encrypted IndexedDB export/restore, separate browser profiles',
    'clinicalGo': false, 'phase': phase ?? 'missing',
    'result': 'NOT_RUN',
  };
  WebVaultKey? activeKey;
  String? ciRaceRecovery;
  try {
    if (phase == 'source') {
      final enrolled = await candidate.enrollEmptyScope(scope);
      activeKey = await candidate.unlock(scope, enrolled.recoveryCode);
      final db = await candidate.openCandidateDatabase(scope, activeKey);
      try {
        await db.customStatement(
          'INSERT INTO log_entries (created_at, blood_sugar, client_uuid) '
          'VALUES (?, ?, ?)',
          [DateTime.utc(2026, 11, 13).millisecondsSinceEpoch ~/ 1000,
            151.0, marker],
        );
      } finally {
        await db.close();
      }
      // Test-only handoff; never put real clinical keys into web storage.
      html.window.sessionStorage['d1_fixture_recovery'] = enrolled.recoveryCode;
      if (Uri.base.queryParameters['race'] == '1') {
        ciRaceRecovery = enrolled.recoveryCode;
      }
      result['result'] = 'SOURCE_READY';
    } else if (phase == 'target') {
      final proceed = html.ButtonElement()
        ..id = 'd1-fresh-profile-restore-trigger'
        ..text = 'Test-only restore after encrypted files imported';
      html.document.body!.append(proceed);
      await proceed.onClick.first;
      proceed.remove();
      final recovery = html.window.sessionStorage['d1_fixture_recovery'];
      if (recovery == null) throw StateError('missing_ci_fixture_recovery');

      var wrongRejected = false;
      try {
        await candidate.unlock(scope, base64UrlEncode(List<int>.filled(32, 17)));
      } on StateError {
        wrongRejected = true;
      }
      activeKey = await candidate.unlock(scope, recovery);
      final db = await candidate.openCandidateDatabase(scope, activeKey);
      try {
        final rows = await db.customSelect(
          'SELECT client_uuid FROM log_entries WHERE blood_sugar = 151.0',
        ).get();
        result['restoredOriginalRecord'] = rows.length == 1 &&
            rows.single.read<String>('client_uuid') == marker;
        if (Uri.base.queryParameters['race'] == '1') {
          final concurrentRows = await db.customSelect(
            'SELECT client_uuid FROM log_entries WHERE blood_sugar = 152.0',
          ).get();
          result['concurrentSqlWriteRecovered'] =
              concurrentRows.length == 1 &&
              concurrentRows.single.read<String>('client_uuid') ==
                  'D1_SYNTHETIC_CONCURRENT_CIPHER_WRITER_755';
        }
      } finally {
        await db.close();
      }
      result['wrongRecoveryRejected'] = wrongRejected;
      result['result'] = result['restoredOriginalRecord'] == true &&
          wrongRejected &&
          (Uri.base.queryParameters['race'] != '1' ||
              result['concurrentSqlWriteRecovered'] == true)
          ? 'PASS'
          : 'FAIL';
    } else {
      throw StateError('unknown_ci_fixture_phase');
    }
  } catch (e) {
    result['result'] = 'FAIL';
    result['error'] = e.toString();
  } finally {
    activeKey?.retire();
    html.document.body?.text = jsonEncode(result);
    // CI-only source mutation with the ACTUAL encrypted Drift/SQLite3MC
    // opener. This is intentionally not part of any patient application.
    final recovery = ciRaceRecovery;
    if (phase == 'source' &&
        Uri.base.queryParameters['race'] == '1' &&
        result['result'] == 'SOURCE_READY' &&
        recovery != null) {
      final writerTrigger = html.ButtonElement()
        ..id = 'd1-synthetic-encrypted-write-after-backup'
        ..text = 'CI synthetic encrypted writer';
      html.document.body?.append(writerTrigger);
      writerTrigger.onClick.listen((_) async {
        WebVaultKey? writerKey;
        try {
          html.window.localStorage['d1_synthetic_race_state'] = 'STARTED';
          writerKey = await candidate.unlock(scope, recovery);
          final writer = await candidate.openCandidateDatabase(scope, writerKey);
          try {
            await writer.customStatement(
              'INSERT INTO log_entries (created_at, blood_sugar, client_uuid) '
              'VALUES (?, ?, ?)',
              [DateTime.utc(2026, 11, 14).millisecondsSinceEpoch ~/ 1000,
                152.0, 'D1_SYNTHETIC_CONCURRENT_CIPHER_WRITER_755'],
            );
          } finally {
            await writer.close();
          }
          html.window.localStorage['d1_synthetic_race_state'] = 'COMMITTED';
        } catch (error) {
          html.window.localStorage['d1_synthetic_race_state'] =
              'FAILED:' + error.toString();
        } finally {
          writerKey?.retire();
        }
      });
    }
  }
}
