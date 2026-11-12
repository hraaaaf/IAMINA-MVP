import 'dart:convert';

import '../../services/d1_session_fence.dart';
import 'database.dart';
import 'local_backup.dart';
import 'patient_vault_scope.dart';

/// Experimental D1 backup policy adapter. Not wired to patient UI.
/// This interface must be backed by a peer-reviewed authenticated encryption
/// implementation (the current tests use a deliberately INSECURE fake).
abstract interface class D1AuthenticatedBackupCipher {
  Future<String> seal({required String owner, required String plaintextJson});
  Future<String> authenticateAndOpen({
    required String expectedOwner,
    required String sealedEnvelope,
  });
}

/// Ensures owner and epoch remain current before exporting ciphertext and
/// BEFORE starting potentially destructive LocalBackup.restoreVaultJson.
/// It is NOT a complete key management or anti-rollback implementation.
final class D1AuthenticatedBackupBoundary {
  final AppDatabase _db;
  final D1SessionFence _fence;
  final D1AuthenticatedBackupCipher _cipher;
  final PatientVaultScope? Function() _currentScope;
  final int Function() _currentEpoch;

  D1AuthenticatedBackupBoundary({
    required AppDatabase db,
    required D1SessionFence sessionFence,
    required D1AuthenticatedBackupCipher cipher,
    required PatientVaultScope? Function() currentScope,
    required int Function() currentAuthEpoch,
  }) : _db = db, _fence = sessionFence, _cipher = cipher,
       _currentScope = currentScope, _currentEpoch = currentAuthEpoch;

  ({PatientVaultScope owner, D1SessionTicket ticket}) _begin() {
    final owner = _db.patientVaultScope;
    final current = _currentScope();
    if (owner == null || current == null ||
        owner.databaseName != current.databaseName ||
        owner.nativeDjangoUserId == null && !owner.databaseName.startsWith('amina_vault_v1_device_')) {
      throw StateError('D1_BACKUP_AUTHORIZATION_REQUIRED');
    }
    final ticket = _fence.beginOperation(
      currentScope: current, currentAuthEpoch: _currentEpoch(),
    );
    return (owner: owner, ticket: ticket);
  }

  void _assertCurrent(D1SessionTicket ticket) {
    final scope = _currentScope();
    if (scope == null) throw StateError('D1_BACKUP_SESSION_REVOKED');
    _fence.assertCanPublish(ticket,
      currentScope: scope, currentAuthEpoch: _currentEpoch());
  }

  Future<String> exportCiphertextOnly() async {
    final active = _begin();
    final encrypted = await LocalBackup.exportVaultCiphertextOnly(
      _db,
      seal: (raw) async {
        _assertCurrent(active.ticket);
        final sealed = await _cipher.seal(
          owner: active.owner.databaseName, plaintextJson: raw,
        );
        _assertCurrent(active.ticket);
        return sealed;
      },
    );
    _assertCurrent(active.ticket);
    // Refuse returning obviously unprotected plaintext / malformed output.
    // This cannot establish encryption strength: independent crypto review is
    // still required.
    if (encrypted.isEmpty || encrypted == raw ||
        encrypted.contains('"patientProfiles"') ||
        encrypted.contains('"logEntries"')) {
      throw StateError('D1_BACKUP_PLAINTEXT_REFUSED');
    }
    return encrypted;
  }

  Future<void> restoreAuthenticatedOnly(String sealedEnvelope) async {
    final active = _begin();
    Map<String, dynamic> header;
    try {
      header = jsonDecode(sealedEnvelope) as Map<String, dynamic>;
    } catch (_) {
      throw const FormatException('D1_BACKUP_INVALID_ENVELOPE');
    }
    if (header['format'] != 'IAMINA_D1_BACKUP' ||
        header['version'] != 1 ||
        header['owner'] != active.owner.databaseName) {
      throw const FormatException('D1_BACKUP_WRONG_OWNER_OR_FORMAT');
    }
    // Only AEAD-authenticated plaintext may reach the transactional importer.
    await LocalBackup.restoreVaultCiphertextOnly(
      _db,
      sealedEnvelope,
      authenticateAndOpen: (sealed) async {
        final raw = await _cipher.authenticateAndOpen(
          expectedOwner: active.owner.databaseName,
          sealedEnvelope: sealed,
        );
        _assertCurrent(active.ticket);
        return raw;
      },
    );
    _assertCurrent(active.ticket);
  }
}
