import 'dart:async';

import 'package:flutter/foundation.dart';

import '../data/drift/database.dart';
import '../data/drift/d18_source_lock_gate.dart';
import '../data/drift/patient_vault_scope.dart';
import 'auth_epoch.dart';
import 'auth_service.dart';

typedef PatientScopeResolver = Future<PatientVaultScope?> Function();
typedef ScopedDbFactory = AppDatabase Function(PatientVaultScope scope);

/// Opt-in async opener for a future, separately authorized cipher cutover.
/// Production forAuth() still uses AppDatabase.forPatientVault (plaintext).
typedef ScopedVaultLeaseFactory = Future<PatientVaultDbLease> Function(
  PatientVaultScope scope,
);

/// A physical DB + optional external encrypted worker, owned as ONE lease.
/// Always closes Drift before releasing its worker/physical Web Lock.
/// The caller must independently authenticate the worker and key before
/// returning a lease. This class is NOT a cipher validator or migration gate.
final class PatientVaultDbLease {
  final AppDatabase database;
  final PatientVaultScope scope;
  final Future<void> Function()? releaseWorker;
  final bool Function()? isKeyLocked;
  Future<void>? _closeFuture;

  PatientVaultDbLease({
    required this.database,
    required this.scope,
    this.releaseWorker,
    this.isKeyLocked,
  });

  bool get isAccessible {
    try {
      return !(isKeyLocked?.call() ?? false);
    } on Object {
      return false;
    }
  }

  Future<void> close() => _closeFuture ??= _closeOnce();

  Future<void> _closeOnce() async {
    try {
      await database.close();
    } finally {
      await releaseWorker?.call();
    }
  }
}

/// D7 authenticated-session boundary. An OPTIONAL async lease factory can
/// now be injected for D18 pre-cutover tests. forAuth() remains unchanged:
/// no patient-facing encrypted worker, migration or flag is enabled.
///
/// At every auth change the old lease becomes invisible SYNCHRONOUSLY.
/// Serial execution ensures the old physical worker is CLOSED before the
/// next opening, including overlapping reconciles and late A->B->A results.
/// Future key-session integration must notify reconcile() on locking; the
/// isKeyLocked getter alone hides the active DB but cannot close its worker.
class PatientVaultSessionController extends ChangeNotifier {
  final Listenable _authChanges;
  final PatientScopeResolver _resolveScope;
  final ScopedVaultLeaseFactory _openLease;

  PatientVaultDbLease? _currentLease;
  PatientVaultScope? _currentScope;
  int? _currentAuthEpoch;
  int _generation = 0;
  bool _disposed = false;
  bool _loading = true;
  // Permanent fail-closed latch when a prior physical worker fails to close.
  // Never start another patient vault in this process after such a failure.
  bool _physicalCloseFailed = false;
  Future<void> _serialized = Future<void>.value();

  PatientVaultSessionController({
    required Listenable authChanges,
    required PatientScopeResolver resolveScope,
    ScopedDbFactory? openDatabase,
    ScopedVaultLeaseFactory? openVaultLease,
  }) : _authChanges = authChanges,
       _resolveScope = resolveScope,
       _openLease = openVaultLease ?? ((scope) async =>
         PatientVaultDbLease(
           scope: scope,
           database: (openDatabase ?? AppDatabase.forPatientVault)(scope),
         )) {
    if (openDatabase != null && openVaultLease != null) {
      throw ArgumentError('D18: choose either sync DB or async lease opener');
    }
    _authChanges.addListener(_onAuthChanged);
    unawaited(reconcile());
  }

  // The opt-in CANARY guards the real plaintext source before opening it.
  // It cannot stop older cached clients and never authorizes a migration.
  factory PatientVaultSessionController.forAuth(
    AuthService auth, {bool d18SourceBarrierCanary = false},
  ) => PatientVaultSessionController(
    authChanges: auth,
    resolveScope: auth.resolvePatientVaultScope,
    openVaultLease: d18SourceBarrierCanary ? _openCanarySource : null,
  );

  static Future<PatientVaultDbLease> _openCanarySource(
    PatientVaultScope scope,
  ) async {
    final lock = await D18SourceLockGate.patient(scope);
    try {
      return PatientVaultDbLease(
        scope: scope,
        database: AppDatabase.forPatientVault(scope),
        releaseWorker: lock.close,
      );
    } catch (_) {
      await lock.close();
      rethrow;
    }
  }

  bool get isResolving => _loading;
  bool get hasVault =>
      !_disposed && !_loading && !_physicalCloseFailed &&
      _currentLease != null &&
      _currentAuthEpoch == AuthEpoch.value && _currentLease!.isAccessible;
  AppDatabase? get activeDatabase =>
      hasVault ? _currentLease!.database : null;
  PatientVaultScope? get activeScope => hasVault ? _currentScope : null;

  void _onAuthChanged() => unawaited(reconcile());

  bool _stillCurrent(int generation, int epoch) =>
      !_disposed && generation == _generation &&
      epoch == AuthEpoch.value;

  Future<void> reconcile() {
    if (_disposed) return Future<void>.value();
    final generation = ++_generation;
    final epoch = AuthEpoch.value;
    final retired = _currentLease;

    // Remove the old patient synchronously before any async resolution.
    _currentLease = null;
    _currentScope = null;
    _currentAuthEpoch = null;
    _loading = true;

    // Enqueue physical shutdown BEFORE notifying reentrant listeners.
    // Crucially, do NOT put the identity resolver on this queue: A's scope
    // resolution may hang indefinitely, while B must still be able to open.
    final closeTask = _serialized.then((_) => _retireLease(retired));
    _serialized = closeTask;
    notifyListeners();
    return _resolveThenEnqueue(generation, epoch, closeTask);
  }

  Future<void> _closeLease(PatientVaultDbLease lease) async {
    try {
      await lease.close();
    } on Object {
      _physicalCloseFailed = true;
      rethrow;
    }
  }

  // A physical close failure permanently seals this controller. Keep the
  // queue settled, otherwise later enqueues could never check that latch.
  Future<void> _retireLease(PatientVaultDbLease? retired) async {
    if (retired == null) return;
    try {
      await _closeLease(retired);
    } on Object {
      // _physicalCloseFailed was set before this failure was swallowed.
    }
  }

  // Concurrent identity resolutions are safe; physical opens are NOT.
  // Stale A can remain pending without holding the serial database lock.
  Future<void> _resolveThenEnqueue(
    int generation, int epoch, Future<void> closeTask,
  ) async {
    if (!_stillCurrent(generation, epoch)) {
      await closeTask;
      return;
    }
    PatientVaultScope? scope;
    try {
      scope = await _resolveScope();
    } on Object {
      // No fallback on an inaccessible authenticated principal.
      scope = null;
    }
    if (!_stillCurrent(generation, epoch)) {
      await closeTask;
      return;
    }
    final operation = _serialized.then(
      (_) => _openResolvedScope(generation, epoch, scope),
    );
    _serialized = operation;
    await operation;
  }

  Future<void> _openResolvedScope(
    int generation, int epoch, PatientVaultScope? scope,
  ) async {
    try {
      if (!_stillCurrent(generation, epoch)) return;
      if (_physicalCloseFailed || scope == null) {
        _loading = false;
        notifyListeners();
        return;
      }

      PatientVaultDbLease? lease;
      try {
        lease = await _openLease(scope);
        // Validate both the wrapper and the Drift database owner BEFORE SQL.
        if (lease.scope.databaseName != scope.databaseName ||
            lease.database.patientVaultScope?.databaseName !=
                scope.databaseName) {
          throw StateError('D18 lease owner mismatch');
        }
        await lease.database.customSelect('SELECT 1').getSingle();
        if (!_stillCurrent(generation, epoch) || !lease.isAccessible) {
          await _closeLease(lease);
          if (_stillCurrent(generation, epoch)) {
            _loading = false;
            notifyListeners();
          }
          return;
        }
        _currentLease = lease;
        _currentScope = scope;
        _currentAuthEpoch = epoch;
        _loading = false;
        notifyListeners();
      } on Object {
        if (lease != null) await _closeLease(lease);
        if (_stillCurrent(generation, epoch)) {
          _loading = false;
          notifyListeners();
        }
      }
    } on Object {
      // A worker close exception means fail-closed. No later opening may
      // rely on this result; _serialized is kept successful for safe retry.
      if (_stillCurrent(generation, epoch)) {
        _loading = false;
        notifyListeners();
      }
    }
  }

  /// Await when tearing down a pre-cutover test owner, including pending opens.
  Future<void> get physicalShutdownComplete => _serialized;

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    _generation++;
    _authChanges.removeListener(_onAuthChanged);
    final retired = _currentLease;
    _currentLease = null;
    _currentScope = null;
    _currentAuthEpoch = null;
    if (retired != null) {
      _serialized = _serialized.then((_) => _closeLease(retired));
      // A callback in releaseWorker can fail, but must not become an
      // unhandled async exception during widget disposal.
      unawaited(_serialized.catchError((Object _) {}));
    }
    super.dispose();
  }
}
