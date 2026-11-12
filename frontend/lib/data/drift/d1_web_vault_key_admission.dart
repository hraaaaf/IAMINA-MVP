// D1 security candidate only. NOT wired into patient main.dart.
// The device KEK is a non-extractable IndexedDB CryptoKey, but same-origin
// JavaScript and XSS can still use it. Never claim hardware-bound security.
import 'dart:async';
import 'dart:js_interop';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';

import '../../services/auth_epoch.dart';
import '../../services/auth_service.dart';
import '../../services/app_lock_service.dart';
import 'd1_web_encrypted_vault.dart';
import 'database.dart';
import 'patient_vault_scope.dart';

@JS('iaminaD1DeviceKeyCustody.unlockDevice')
external JSPromise<JSUint8Array> _deviceUnlockJs(JSString owner);

typedef D1ResolveOwner = Future<PatientVaultScope?> Function();

/// Ties one volatile database lease to the current verified owner,
/// authentication epoch and app-lock state. A logout/lock event synchronously
/// removes public access, then closes and flushes the worker asynchronously.
/// Does NOT solve an in-flight operation that had already obtained AppDatabase.
/// Do not use for clinical patients until cancellation and audit are complete.
final class D1WebVaultKeySessionCoordinator extends ChangeNotifier {
  final Listenable _authChanges;
  final Listenable _lockChanges;
  final D1ResolveOwner _resolveOwner;
  final int Function() _authEpoch;
  final bool Function() _authenticated;
  final bool Function() _unlocked;

  D1WebEncryptedVaultLease? _lease;
  PatientVaultScope? _scope;
  Future<void> _draining = Future<void>.value();
  int _generation = 0;
  bool _disposed = false;

  D1WebVaultKeySessionCoordinator({
    required Listenable authChanges,
    required Listenable appLockChanges,
    required D1ResolveOwner resolveOwner,
    required int Function() currentAuthEpoch,
    required bool Function() isAuthenticated,
    required bool Function() isUnlocked,
  }) : _authChanges = authChanges,
       _lockChanges = appLockChanges,
       _resolveOwner = resolveOwner,
       _authEpoch = currentAuthEpoch,
       _authenticated = isAuthenticated,
       _unlocked = isUnlocked {
    _authChanges.addListener(_invalidate);
    _lockChanges.addListener(_invalidate);
  }

  /// Factory for the actual two services, but intentionally not called
  /// by IAMINA patient app until mandatory clinical gate is satisfied.
  factory D1WebVaultKeySessionCoordinator.forAuth({
    required AuthService auth,
    required AppLockService appLock,
  }) => D1WebVaultKeySessionCoordinator(
    authChanges: auth,
    appLockChanges: appLock,
    resolveOwner: auth.resolvePatientVaultScope,
    currentAuthEpoch: () => AuthEpoch.value,
    isAuthenticated: () => auth.isAuthenticated && !auth.isAuditSession,
    isUnlocked: () => appLock.isInitialized && appLock.isUnlocked,
  );

  bool get hasVault => !_disposed && _lease?.valid == true;

  AppDatabase? get activeDatabase {
    if (!hasVault) return null;
    try { return _lease!.database; } on StateError { return null; }
  }

  PatientVaultScope? get activeScope => hasVault ? _scope : null;

  void _invalidate() {
    if (_disposed) return;
    _generation++;
    final old = _lease;
    _lease = null;
    _scope = null;
    if (old != null) {
      _draining = _draining.then((_) => old.retire(),
          onError: (Object _) => old.retire());
    }
    notifyListeners();
  }

  bool _isCurrent(int generation, int epoch) =>
      !_disposed && generation == _generation &&
      _authEpoch() == epoch && _authenticated() && _unlocked();

  Future<void> admitAfterUnlock() async {
    _invalidate();
    final generation = _generation;
    final epoch = _authEpoch();
    if (!_isCurrent(generation, epoch)) {
      throw StateError('D1_KEY_ADMISSION_REQUIRES_AUTH_AND_UNLOCK');
    }
    // Never open another encrypted owner namespace while an older worker
    // is still holding a physical SQLite/IndexedDB connection.
    await _draining;
    if (!_isCurrent(generation, epoch)) {
      throw StateError('D1_KEY_SESSION_CHANGED');
    }
    final scope = await _resolveOwner();
    if (!_isCurrent(generation, epoch) || scope == null ||
        scope.databaseName == 'amina_vault_v1_audit') {
      throw StateError('D1_KEY_VERIFIED_OWNER_REQUIRED');
    }
    _scope = scope;
    Uint8List? dbKey;
    D1WebEncryptedVaultLease? opened;
    try {
      // JS returns a temporary 32-byte DEK. The browser profile CryptoKey
      // remains non-extractable, but the DEK necessarily crosses a transient
      // JS/Dart memory boundary before transfer to the SQLite3MC worker.
      final jsKey = await _deviceUnlockJs(scope.databaseName.toJS).toDart;
      dbKey = Uint8List.fromList(jsKey.toDart);
      jsKey.toDart.fillRange(0, jsKey.toDart.length, 0);
      if (!_isCurrent(generation, epoch) ||
          _scope?.databaseName != scope.databaseName) {
        throw StateError('D1_KEY_SESSION_CHANGED_AFTER_UNWRAP');
      }
      opened = await D1WebEncryptedVaultAdmission.open(
        scope: scope, authEpoch: epoch,
        currentScope: () => _scope,
        currentEpoch: _authEpoch,
        isUnlocked: () => _authenticated() && _unlocked() &&
            !_disposed && generation == _generation,
        keyMaterial: dbKey,
      );
      if (!_isCurrent(generation, epoch)) {
        throw StateError('D1_KEY_SESSION_CHANGED_DURING_WORKER_OPEN');
      }
      _lease = opened;
      opened = null;
      notifyListeners();
    } catch (_) {
      if (opened != null) await opened.retire();
      if (!_disposed && generation == _generation) _scope = null;
      rethrow;
    } finally {
      dbKey?.fillRange(0, dbKey.length, 0);
    }
  }

  Future<void> revokeAndFlush() async {
    _invalidate();
    await _draining;
  }

  @override
  void dispose() {
    if (_disposed) return;
    _invalidate();
    _disposed = true;
    _authChanges.removeListener(_invalidate);
    _lockChanges.removeListener(_invalidate);
    super.dispose();
  }
}
