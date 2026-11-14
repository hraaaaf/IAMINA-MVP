// D1-P0 candidate only. NOT referenced by production main.dart.
//
// Bridges an explicit patient-entered recovery code into the existing
// PatientVaultSessionController without ever enabling an automatic Web vault
// opener. There is no creation/migration/deletion or unencrypted fallback.
// This does not constitute clinical access authorization or a patient UX.
import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';
import 'app_lock_service.dart';
import 'auth_service.dart';
import 'patient_vault_session_controller.dart';
import 'web_vault_explicit_admission.dart';
import 'web_vault_session_admission_candidate.dart';

final class _OneShotRecovery {
  final WebVaultExplicitAdmission admission;
  String? _code;
  String? _owner;

  _OneShotRecovery(this.admission);

  void supply(PatientVaultScope scope, String code) {
    if (_code != null) throw StateError('web_vault_recovery_pending');
    if (code.isEmpty) throw StateError('web_vault_explicit_recovery_required');
    _code = code;
    _owner = scope.databaseName;
  }

  Future<AppDatabase> consume(PatientVaultScope scope) {
    final code = _code;
    final owner = _owner;
    clear();
    if (code == null || owner != scope.databaseName) {
      // Preserve the existing production safe-hold identifier; a missing
      // patient-entered code NEVER opens a default plaintext Drift executor.
      throw StateError('web_patient_vault_encryption_not_verified');
    }
    return admission.openWithExplicitRecovery(
      scope: scope, recoveryCode: code,
    );
  }

  void clear() {
    _code = null;
    _owner = null;
  }
}

final class WebVaultRecoverySessionCandidate {
  final PatientVaultSessionController controller;
  final WebVaultExplicitAdmission _admission;
  final _OneShotRecovery _oneShot;
  bool _submitting = false;
  bool _disposed = false;

  WebVaultRecoverySessionCandidate._(
    this.controller, this._admission, this._oneShot,
  );

  static WebVaultRecoverySessionCandidate forAuthenticatedSession({
    required AuthService auth,
    required AppLockService appLock,
  }) {
    final admission = makeWebPatientAdmissionCandidate(
      auth: auth, appLock: appLock,
    );
    final slot = _OneShotRecovery(admission);
    // A lock/logout event hides a published database synchronously via the
    // admissionValid getter and retires the current DB via reconcile().
    final combinedChanges = Listenable.merge([auth, appLock]);
    final controller = PatientVaultSessionController(
      authChanges: combinedChanges,
      resolveScope: auth.resolvePatientVaultScope,
      admissionValid: () =>
          auth.isAuthenticated &&
          !auth.isAuditSession &&
          appLock.isInitialized &&
          appLock.isConfigured &&
          appLock.isRequired &&
          appLock.isUnlocked &&
          !appLock.recoveryRequired,
      openDatabase: slot.consume,
    );
    return WebVaultRecoverySessionCandidate._(
      controller, admission, slot,
    );
  }

  /// Called ONLY from a future explicit recovery UI after AppLock unlock.
  /// Neither this bridge nor the test candidate ever stores a recovery code in
  /// localStorage/sessionStorage, logs, artifacts, or long-lived application
  /// state. The one-shot slot is cleared in every success/failure branch.
  Future<bool> submitExplicitRecovery({
    required PatientVaultScope scope,
    required String recoveryCode,
  }) async {
    if (_disposed) throw StateError('web_vault_admission_revoked');
    if (_submitting) throw StateError('web_vault_recovery_pending');
    _submitting = true;
    try {
      _oneShot.supply(scope, recoveryCode);
      await controller.reconcile();
      return controller.hasVault &&
          controller.activeScope?.databaseName == scope.databaseName;
    } finally {
      _oneShot.clear();
      _submitting = false;
    }
  }

  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _oneShot.clear();
    controller.dispose();
    _admission.dispose();
  }
}
