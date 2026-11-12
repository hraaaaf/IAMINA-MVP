// Only CI synthetic glucose. This probes the candidate patient admission API
// without altering IAMINA's patient UI, real credentials or existing vaults.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:typed_data';

import 'data/drift/database.dart';
import 'data/drift/d1_web_encrypted_vault.dart';
import 'data/drift/patient_vault_scope.dart';

const _marker = 'D1_HIGH_FAKE_PATIENT_ROW_731';
final _ownerA = PatientVaultScope.nativeDjango(731);
final _ownerB = PatientVaultScope.nativeDjango(812);

Future<void> main() async {
  html.document.title = 'D1_HIGH_RUNNING';
  final phase = Uri.base.queryParameters['phase'] ?? '';
  var owner = _ownerA;
  var epoch = 17;
  var unlocked = true;
  var stage = 'INIT';
  try {
    if (phase == 'unkeyed') {
      try {
        final legacy = AppDatabase.forPatientVault(_ownerA);
        await legacy.close();
        throw StateError('UNKEYED_OPEN_ALLOWED');
      } on StateError catch (e) {
        if (!e.message.toString().contains(
            'D1_ENCRYPTED_WEB_PATIENT_VAULT_ADMISSION_REQUIRED')) {
          rethrow;
        }
      }
      html.document.title = 'D1_HIGH_PASS_UNKEYED';
      return;
    }
    if (phase == 'locked' || phase == 'foreign' || phase == 'missing_key') {
      if (phase == 'locked') unlocked = false;
      if (phase == 'foreign') owner = _ownerB;
      final key = phase == 'missing_key'
          ? Uint8List(0)
          : Uint8List.fromList(List.generate(32, (i) => i + 1));
      var denied = false;
      try {
        await D1WebEncryptedVaultAdmission.open(
          scope: _ownerA, authEpoch: epoch,
          currentScope: () => owner,
          currentEpoch: () => epoch,
          isUnlocked: () => unlocked,
          keyMaterial: key,
        );
      } on StateError {
        denied = true;
      }
      if (!denied) throw StateError('NO_ADMISSION_DENIAL');
      if (key.any((b) => b != 0)) throw StateError('KEY_BUFFER_NOT_WIPED');
      html.document.title = 'D1_HIGH_PASS_${phase.toUpperCase()}';
      return;
    }
    if (!{'seed', 'reopen', 'wrong_key', 'retire'}.contains(phase)) {
      throw StateError('INVALID_PHASE');
    }
    final key = Uint8List.fromList(List.generate(32, (i) => i + 1));
    if (phase == 'wrong_key') key[0] = 51;
    D1WebEncryptedVaultLease? vault;
    try {
      stage = 'OPEN';
      vault = await D1WebEncryptedVaultAdmission.open(
        scope: _ownerA, authEpoch: epoch,
        currentScope: () => owner,
        currentEpoch: () => epoch,
        isUnlocked: () => unlocked,
        keyMaterial: key,
      );
      if (phase == 'wrong_key') {
        throw StateError('WRONG_KEY_WAS_ACCEPTED');
      }
      stage = 'SELECT';
      final db = vault.database;
      if (phase == 'seed') {
        stage = 'INSERT';
        await db.into(db.logEntries).insert(
          LogEntriesCompanion.insert(
            createdAt: DateTime.utc(2026, 11, 12),
            bloodSugar: 117.0,
            clientUuid: _marker,
          ),
        );
      }
      final logs = await db.getRecentLogs();
      if (logs.length != 1 || logs.single.clientUuid != _marker ||
          logs.single.bloodSugar != 117.0) {
        throw StateError('WRONG_GENERATED_SCHEMA_ROWS');
      }
      if (phase == 'retire') {
        epoch++;
        owner = _ownerB;
        unlocked = false;
        stage = 'REVOKE';
        if (vault.valid) throw StateError('STALE_VAULT_STILL_VALID');
        try {
          vault.database;
          throw StateError('STALE_VAULT_PUBLISHED');
        } on StateError catch (e) {
          if (!e.message.toString().contains('D1_VAULT_SESSION_REVOKED')) {
            rethrow;
          }
        }
      }
      stage = 'CLOSE';
      await vault.retire();
      vault = null;
      if (key.any((b) => b != 0)) throw StateError('KEY_BUFFER_NOT_WIPED');
    } catch (e) {
      if (vault != null) {
        try { await vault.retire(); } catch (_) { /* fail-closed */ }
      }
      if (phase == 'wrong_key' && e is StateError &&
          e.message.toString().contains('D1_VAULT_KEY_OR_CIPHER_REFUSED')) {
        html.document.title = 'D1_HIGH_PASS_WRONG_KEY';
        return;
      }
      rethrow;
    }
    html.document.title = 'D1_HIGH_PASS_${phase.toUpperCase()}';
  } catch (_) {
    // Error classes only, no SQL error text or key details emitted.
    html.document.title = 'D1_HIGH_FAIL_$stage';
  }
}
