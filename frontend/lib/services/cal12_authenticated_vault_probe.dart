import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';
import 'app_lock_service.dart';
import 'auth_service.dart';
import 'patient_vault_session_controller.dart';

/// CAL-12 read-only preflight; NOT medical-export authorization.
///
/// Uses real IAMINA auth/vault/lock objects, but cannot prove that a bearer
/// remains valid on the server. No consent, patient record, file or network I/O.
final class Cal12AuthenticatedVaultProbe {
  Cal12AuthenticatedVaultProbe._({
    required AuthService auth,
    required PatientVaultSessionController vault,
    required AppLockService appLock,
    required AppDatabase database,
    required int accountId,
    required int epoch,
  })  : _auth = auth,
        _vault = vault,
        _appLock = appLock,
        _database = database,
        _accountId = accountId,
        _epoch = epoch {
    _auth.addListener(_onBoundaryChanged);
    _vault.addListener(_onBoundaryChanged);
    _appLock.addListener(_onBoundaryChanged);
  }

  static const bool realPatientExportEnabled = false;

  final AuthService _auth;
  final PatientVaultSessionController _vault;
  final AppLockService _appLock;
  final AppDatabase _database;
  final int _accountId;
  final int _epoch;
  bool _retired = false;

  static bool _strongSessionAndLock(AuthService auth, AppLockService lock) =>
      auth.isInitialized &&
      auth.isAuthenticated &&
      !auth.isAuditSession &&
      !auth.isAnonymous &&
      auth.isRemoteCredentialVerified &&
      auth.hasRemoteApiCredential &&
      lock.isInitialized &&
      lock.isConfigured &&
      lock.isRequired &&
      !lock.isExplicitlySkipped &&
      !lock.recoveryRequired &&
      lock.isUnlocked;

  /// Returns null on any ambiguity. It never authorizes patient export.
  static Cal12AuthenticatedVaultProbe? tryCapture({
    required AuthService auth,
    required PatientVaultSessionController vault,
    required AppLockService appLock,
  }) {
    final epoch = AuthService.authEpoch;
    final id = auth.boundNativeAccountId;
    final scope = vault.activeScope;
    final db = vault.activeDatabase;
    if (!_strongSessionAndLock(auth, appLock) ||
        id == null ||
        id <= 0 ||
        vault.isResolving ||
        db == null ||
        scope == null ||
        scope.nativeDjangoUserId != id ||
        scope.databaseName != PatientVaultScope.nativeDjango(id).databaseName ||
        epoch != AuthService.authEpoch) {
      return null;
    }
    final snapshot = Cal12AuthenticatedVaultProbe._(
      auth: auth,
      vault: vault,
      appLock: appLock,
      database: db,
      accountId: id,
      epoch: epoch,
    );
    if (!snapshot.isCurrent) {
      snapshot.retire();
      return null;
    }
    return snapshot;
  }

  /// Permanently false after authentication, vault or app-lock invalidation.
  bool get isCurrent {
    if (_retired) return false;
    final scope = _vault.activeScope;
    final stillCurrent = _strongSessionAndLock(_auth, _appLock) &&
        AuthService.authEpoch == _epoch &&
        _auth.boundNativeAccountId == _accountId &&
        !_vault.isResolving &&
        identical(_vault.activeDatabase, _database) &&
        scope != null &&
        scope.nativeDjangoUserId == _accountId &&
        scope.databaseName ==
            PatientVaultScope.nativeDjango(_accountId).databaseName;
    if (!stillCurrent) retire();
    return stillCurrent;
  }

  void _onBoundaryChanged() {
    // A synchronous lock/logout notification irrevocably retires the probe:
    // even a later unlock for the same identity cannot resurrect it.
    if (!_retired) {
      final stillCurrent = isCurrent;
      if (!stillCurrent) return;
    }
  }

  /// The caller must retire unused probes to detach listeners.
  void retire() {
    if (_retired) return;
    _retired = true;
    _auth.removeListener(_onBoundaryChanged);
    _vault.removeListener(_onBoundaryChanged);
    _appLock.removeListener(_onBoundaryChanged);
  }
}
