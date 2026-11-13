import 'dart:async';

import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';
import 'auth_epoch.dart';
import 'auth_service.dart';

typedef PatientScopeResolver = Future<PatientVaultScope?> Function();
// Encrypted Web authorization, key unwrap and IndexedDB admission are async.
// Native synchronous factories remain source-compatible.
typedef ScopedDbFactory = FutureOr<AppDatabase> Function(PatientVaultScope scope);

/// D7: authenticated-session boundary for opening a *physical* local vault.
///
/// No legacy database fallback. On every auth transition the old database is
/// removed from public access synchronously, before asynchronous scope lookup
/// or opening the next vault. A stale result is always closed and discarded.
/// This is a primitive, not certification of app-wide provider isolation.
class PatientVaultSessionController extends ChangeNotifier {
  final Listenable _authChanges;
  final PatientScopeResolver _resolveScope;
  final ScopedDbFactory _openDatabase;

  AppDatabase? _currentDatabase;
  PatientVaultScope? _currentScope;
  int _generation = 0;
  bool _disposed = false;
  bool _loading = true;
  // Reason only, never a bypass token: access remains denied.
  bool _webEncryptionRequired = false;

  PatientVaultSessionController({
    required Listenable authChanges,
    required PatientScopeResolver resolveScope,
    ScopedDbFactory? openDatabase,
  }) : _authChanges = authChanges,
       _resolveScope = resolveScope,
       _openDatabase = openDatabase ?? AppDatabase.forPatientVault {
    _authChanges.addListener(_onAuthChanged);
    unawaited(reconcile());
  }

  factory PatientVaultSessionController.forAuth(AuthService auth) =>
      PatientVaultSessionController(
        authChanges: auth,
        resolveScope: auth.resolvePatientVaultScope,
      );

  bool get isResolving => _loading;
  bool get requiresEncryptedWebVault => _webEncryptionRequired && !_loading;
  bool get hasVault => _currentDatabase != null && !_loading;
  AppDatabase? get activeDatabase => hasVault ? _currentDatabase : null;
  PatientVaultScope? get activeScope => hasVault ? _currentScope : null;

  void _onAuthChanged() {
    unawaited(reconcile());
  }

  Future<void> reconcile() async {
    if (_disposed) return;
    final generation = ++_generation;
    final epoch = AuthEpoch.value;
    final retired = _currentDatabase;
    _currentDatabase = null;
    _currentScope = null;
    _webEncryptionRequired = false;
    _loading = true;
    notifyListeners();
    if (retired != null) await retired.close();
    if (_disposed || generation != _generation || epoch != AuthEpoch.value) {
      return;
    }

    PatientVaultScope? scope;
    try {
      scope = await _resolveScope();
    } catch (_) {
      // Unavailable account state cannot authorize an arbitrary local vault.
      scope = null;
    }
    if (_disposed || generation != _generation || epoch != AuthEpoch.value) {
      return;
    }
    if (scope == null) {
      _loading = false;
      notifyListeners();
      return;
    }

    AppDatabase? opened;
    try {
      opened = await _openDatabase(scope);
      // Key unwrap/IndexedDB admission may outlive an auth epoch. Discard
      // BEFORE even SELECT 1, since the first Drift query can run migrations.
      if (_disposed || generation != _generation || epoch != AuthEpoch.value) {
        await opened.close();
        return;
      }
      // Ensure opening/migrating the named vault completes before publication.
      await opened.customSelect('SELECT 1').getSingle();
      if (_disposed || generation != _generation || epoch != AuthEpoch.value) {
        await opened.close();
        return;
      }
      _currentDatabase = opened;
      _currentScope = scope;
      _loading = false;
      notifyListeners();
    } catch (error) {
      if (opened != null) await opened.close();
      if (!_disposed && generation == _generation &&
          epoch == AuthEpoch.value) {
        // D1: only this exact storage-admission refusal gets the explicit
        // encrypted-vault safe-hold screen. Unknown errors remain generic.
        _webEncryptionRequired = error is StateError &&
            error.message == 'web_patient_vault_encryption_not_verified';
        _loading = false;
        notifyListeners();
      }
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _generation++;
    _authChanges.removeListener(_onAuthChanged);
    final retired = _currentDatabase;
    _currentDatabase = null;
    _currentScope = null;
    if (retired != null) unawaited(retired.close());
    super.dispose();
  }
}
