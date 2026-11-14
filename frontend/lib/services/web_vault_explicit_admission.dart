import 'dart:async';

import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';

/// D1-P0: single-request Web admission policy. This policy grants NO clinical
/// access by itself: production still refuses every Web patient database.
///
/// The caller MUST supply the real authenticated and App-Lock state, and MUST
/// retire the returned database on *every* auth/lock transition. In particular,
/// bind the eventual PatientVaultSessionController to the same [sessionChanges]
/// listenable. A one-shot recovery code is supplied by the patient on each
/// attempt; this class neither caches nor stores it in a browser storage API.
typedef WebVaultAdmissionIdentity = ({
  bool authenticated,
  bool appLockInitialized,
  bool appLockConfigured,
  bool appLockUnlocked,
  bool appLockRecoveryRequired,
  bool remoteCredentialVerified,
  bool hasRemoteCredential,
  int? nativeAccountId,
});

typedef WebVaultIdentitySnapshot = WebVaultAdmissionIdentity Function();
typedef WebVaultScopeResolver = Future<PatientVaultScope?> Function();
typedef WebVaultEncryptedOpener = Future<AppDatabase> Function(
    PatientVaultScope scope, String explicitRecoveryCode);

final class WebVaultExplicitAdmission {
  final Listenable sessionChanges;
  final WebVaultIdentitySnapshot identity;
  final WebVaultScopeResolver resolveScope;
  final WebVaultEncryptedOpener encryptedOpener;
  final int Function() authEpoch;

  bool _disposed = false;
  bool _opening = false;
  int _revision = 0;

  WebVaultExplicitAdmission({
    required this.sessionChanges,
    required this.identity,
    required this.resolveScope,
    required this.encryptedOpener,
    required this.authEpoch,
  }) {
    sessionChanges.addListener(_revokePending);
  }

  void _revokePending() => ++_revision;

  void _requireOwner(PatientVaultScope scope) {
    final current = identity();
    if (_disposed ||
        !current.authenticated ||
        !current.appLockInitialized ||
        !current.appLockConfigured ||
        !current.appLockUnlocked ||
        current.appLockRecoveryRequired) {
      throw StateError('web_vault_identity_or_app_lock_required');
    }

    final nativeId = scope.nativeDjangoUserId;
    if (nativeId != null) {
      // An old bearer, a local marker or a server login for owner B may
      // NEVER authorize opening owner A's patient vault.
      if (!current.remoteCredentialVerified ||
          !current.hasRemoteCredential ||
          current.nativeAccountId != nativeId) {
        throw StateError('web_vault_verified_native_owner_required');
      }
    } else if (!scope.databaseName.startsWith('amina_vault_v1_device_')) {
      // Audit/guest namespaces have no clinical Web admission authority.
      throw StateError('web_vault_authenticated_owner_scope_required');
    }
  }

  void _requireFresh(
      PatientVaultScope scope, int revision, int expectedEpoch) {
    if (_disposed || _revision != revision || authEpoch() != expectedEpoch) {
      throw StateError('web_vault_admission_revoked');
    }
    _requireOwner(scope);
  }

  /// Caller-supplied recovery material is required on every attempt. This
  /// method NEVER enrolls, silently resets, imports, migrates or deletes a
  /// historical vault. Missing/stale ciphertext must fail in the opener.
  Future<AppDatabase> openWithExplicitRecovery({
    required PatientVaultScope scope,
    required String recoveryCode,
  }) async {
    if (_disposed) throw StateError('web_vault_admission_revoked');
    if (_opening) throw StateError('web_vault_admission_already_pending');
    if (recoveryCode.isEmpty) {
      throw StateError('web_vault_explicit_recovery_required');
    }
    _opening = true;
    final revision = _revision;
    final epoch = authEpoch();
    try {
      _requireFresh(scope, revision, epoch);
      final resolved = await resolveScope();
      _requireFresh(scope, revision, epoch);
      if (resolved == null || resolved.databaseName != scope.databaseName) {
        throw StateError('web_vault_authenticated_scope_mismatch');
      }
      final opened = await encryptedOpener(scope, recoveryCode);
      try {
        // A logout/account switch/app lock revocation while WebCrypto or
        // IndexedDB is pending must close the result before publication.
        _requireFresh(scope, revision, epoch);
        final stillResolved = await resolveScope();
        _requireFresh(scope, revision, epoch);
        if (stillResolved?.databaseName != scope.databaseName) {
          throw StateError('web_vault_authenticated_scope_mismatch');
        }
        return opened;
      } catch (_) {
        await opened.close();
        rethrow;
      }
    } finally {
      _opening = false;
    }
  }

  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _revokePending();
    sessionChanges.removeListener(_revokePending);
  }
}
