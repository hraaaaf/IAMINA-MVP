// CI-only D18 WebCrypto + physically isolated IndexedDB recovery proof.
// No real account, no patient data, no production import or automatic sync.
import 'dart:convert';
import 'dart:html' as html;

import 'package:flutter/widgets.dart';

import 'data/drift/d18_encrypted_backup.dart';
import 'data/drift/database.dart';
import 'data/drift/patient_progressive_demographics_store.dart';
import 'data/drift/patient_vault_scope.dart';
import 'data/drift/patient_weight_history_store.dart';

const sourceId = '2c4fedce-0033-4b33-8d24-1d97ca712339';
const otherId = '2c4fedce-0033-4b33-8d24-1d97ca712340';
const targetId = '2c4fedce-0033-4b33-8d24-1d97ca712341';
const obsId = '10b22501-d9cd-41f1-816d-d6b481db7e49';
const secret = 'synthetic-d18-browser-phrase-2026';

void check(bool condition, String message) {
  if (!condition) throw StateError(message);
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final args = Uri.base.queryParameters;
  final phase = args['phase'] ?? 'none';
  html.document.title = 'D18_CRYPTO_PENDING';
  final scope = PatientVaultScope.deviceLocal(
    phase == 'seed_a' || phase == 'verify_a'
        ? sourceId
        : phase == 'verify_b' ? otherId : targetId,
  );
  final db = AppDatabase.forPatientVault(scope);
  try {
    await db.customSelect('SELECT 1').getSingle();
    final demographics = PatientProgressiveDemographicsStore(db);
    final history = PatientWeightHistoryStore(db);
    Future<void> checkSource() async {
      final d = await demographics.read();
      final w = await history.recent();
      check(d?.birthYear == 1987 && d?.genderIdentity == 'woman',
          'Personal declaration mismatch');
      check(w.length == 1 && w.single.clientUuid == obsId &&
            w.single.valueHundredths == 7250 && w.single.unit == 'kg',
          'Synthetic weight history mismatch');
    }

    switch (phase) {
      case 'seed_a':
        check(await demographics.read() == null, 'A not empty on seed');
        check((await history.recent()).isEmpty, 'A weights not empty');
        await demographics.update(
          updateBirthYear: true, birthYear: 1987,
          updateGenderIdentity: true, genderIdentity: 'woman',
        );
        await history.append(
          clientUuid: obsId, value: '72.50', unit: 'kg',
          measuredAtUtc: DateTime.utc(2026, 10, 15, 9, 30),
        );
        await checkSource();
        final ciphertext = await D18EncryptedBackup.exportEncrypted(
          db, passphrase: secret,
        );
        final envelope = jsonDecode(ciphertext) as Map<String, dynamic>;
        check(!envelope.containsKey('vault') &&
              !envelope.containsKey('owner') &&
              !envelope.containsKey('weights') &&
              !envelope.containsKey('declarations'),
              'Leaking identifying data in unencrypted wrapper');
        check(!ciphertext.contains('72.50'), 'Leaking plaintext clinical measure');
        html.document.body?.append(html.PreElement()
          ..id = 'd18-crypto-synthetic-export'
          ..text = ciphertext);
        break;
      case 'verify_a':
        await checkSource();
        break;
      case 'verify_b':
        check(await demographics.read() == null, 'B sees A demographics');
        check((await history.recent()).isEmpty, 'B sees A weights');
        break;
      case 'wrong_pass':
        final ciphertext = args['payload'] ?? '';
        var rejected = false;
        try {
          await D18EncryptedBackup.open(
            ciphertext, passphrase: 'invalid-synthetic-passphrase',
          );
        } catch (_) { rejected = true; }
        check(rejected, 'Wrong password unexpectedly decrypted');
        check(await demographics.read() == null &&
              (await history.recent()).isEmpty,
              'Wrong passphrase mutated destination');
        break;
      case 'tampered':
        final ciphertext = args['payload'] ?? '';
        final envelope = jsonDecode(ciphertext) as Map<String, dynamic>;
        final encoded = envelope['sealed'] as String;
        final at = encoded.length ~/ 2;
        envelope['sealed'] = encoded.substring(0, at) +
          (encoded[at] == 'A' ? 'B' : 'A') + encoded.substring(at + 1);
        var rejected = false;
        try {
          await D18EncryptedBackup.open(
            jsonEncode(envelope), passphrase: secret,
          );
        } catch (_) { rejected = true; }
        check(rejected, 'Altered ciphertext unexpectedly decrypted');
        check(await demographics.read() == null &&
              (await history.recent()).isEmpty,
              'Corrupted file mutated destination');
        break;
      case 'restore_c':
        check(await demographics.read() == null &&
              (await history.recent()).isEmpty,
              'Target C was not initially empty');
        final ciphertext = args['payload'] ?? '';
        final preview = await D18EncryptedBackup.open(
          ciphertext, passphrase: secret,
        );
        check(preview.isDeviceOnly && preview.observationCount == 1,
            'Decrypted preview mismatch');
        await D18EncryptedBackup.restoreInto(
          db, preview, allowDeviceTransfer: true,
        );
        await checkSource();
        break;
      case 'verify_c':
        await checkSource();
        break;
      case 'reject_second_restore':
        final ciphertext = args['payload'] ?? '';
        final preview = await D18EncryptedBackup.open(
          ciphertext, passphrase: secret,
        );
        var rejected = false;
        try {
          await D18EncryptedBackup.restoreInto(
            db, preview, allowDeviceTransfer: true,
          );
        } catch (_) { rejected = true; }
        check(rejected, 'Restoring into nonempty vault did not fail closed');
        await checkSource();
        break;
      default:
        throw StateError('Unsupported synthetic D18 browser phase: $phase');
    }
    html.document.title = 'D18_CRYPTO_PASS:' + phase;
  } catch (error, stack) {
    html.document.title = 'D18_CRYPTO_FAIL:' + phase;
    html.document.documentElement?.dataset['d18Error'] =
        error.toString().substring(0,
          error.toString().length < 500 ? error.toString().length : 500);
    debugPrint('D18_WEB_CRYPTO_ERROR $phase $error');
    debugPrintStack(stackTrace: stack);
  } finally {
    await db.close();
  }
}
