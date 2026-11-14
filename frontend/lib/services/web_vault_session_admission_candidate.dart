// D1-P0 candidate bridge ONLY; not imported by production main.dart.
// Native app behavior and the real Web safe-hold remain unchanged.
// This is not clinical authorization until old PWA fencing, backup UX,
// multi-tab/WebKit behavior and independent review are proved.
import 'package:flutter/foundation.dart';

import '../data/drift/web_patient_vault_cipher_candidate.dart';
import '../data/drift/revocable_patient_query_guard.dart';
import 'app_lock_service.dart';
import 'auth_epoch.dart';
import 'auth_service.dart';
import 'web_vault_explicit_admission.dart';

/// Connect the REAL AuthService / AppLockService state to the encrypted
/// candidate. There is no implicit enrollment, "forgot code" fallback,
/// browser-stored recovery code, or downgrade to unencrypted Drift.
WebVaultExplicitAdmission makeWebPatientAdmissionCandidate({
  required AuthService auth,
  required AppLockService appLock,
  WebPatientVaultCipherCandidate cipher = const WebPatientVaultCipherCandidate(),
}) {
  return WebVaultExplicitAdmission(
    sessionChanges: Listenable.merge([auth, appLock]),
    authEpoch: () => AuthEpoch.value,
    identity: () => (
      authenticated: auth.isAuthenticated && !auth.isAuditSession,
      appLockInitialized: appLock.isInitialized,
      appLockConfigured: appLock.isConfigured && appLock.isRequired,
      appLockUnlocked: appLock.isUnlocked,
      appLockRecoveryRequired: appLock.recoveryRequired,
      remoteCredentialVerified: auth.isRemoteCredentialVerified,
      hasRemoteCredential: auth.hasRemoteApiCredential,
      nativeAccountId: auth.boundNativeAccountId,
    ),
    resolveScope: auth.resolvePatientVaultScope,
    encryptedOpener: (scope, recoveryCode) async {
      final admissionEpoch = AuthEpoch.value;
      final key = await cipher.unlock(scope, recoveryCode);
      bool isStillAuthorized() {
        if (AuthEpoch.value != admissionEpoch ||
            !auth.isAuthenticated || auth.isAuditSession ||
            !appLock.isInitialized || !appLock.isConfigured ||
            !appLock.isRequired || !appLock.isUnlocked ||
            appLock.recoveryRequired) {
          return false;
        }
        final nativeId = scope.nativeDjangoUserId;
        return nativeId == null
            ? scope.databaseName.startsWith('amina_vault_v1_device_') &&
                !auth.hasRemoteApiCredential
            : auth.isRemoteCredentialVerified &&
                auth.hasRemoteApiCredential &&
                auth.boundNativeAccountId == nativeId;
      }
      try {
        if (!isStillAuthorized()) {
          throw StateError('web_vault_admission_revoked');
        }
        final guard = RevocablePatientQueryGuard(
          authorized: isStillAuthorized,
          revocationSignals: Listenable.merge([auth, appLock]),
        );
        try {
          return await cipher.openCandidateDatabase(
            scope, key, admissionGuard: guard,
          );
        } catch (_) {
          guard.revoke();
          rethrow;
        }
      } finally {
        // This key is never cached across logout, lock, or new admission.
        key.retire();
      }
    },
  );
}
