import 'dart:async';

import 'package:flutter/foundation.dart';

import 'database.dart';
import 'patient_vault_scope.dart';

typedef PatientVaultResolver = Future<PatientVaultScope?> Function();
typedef PatientVaultOpener = Future<AppDatabase> Function(PatientVaultScope scope);

/// D7 fail-closed physical-vault lifecycle for an authenticated principal.
///
/// Auth changes synchronously revoke the old database from consumers before
/// any asynchronous secure-storage read or vault open. Legacy "amina" rows are
/// never adopted into a new owner. This component is not an authentication or
/// strong device-unlock gate.
class PatientVaultSessionCoordinator extends ChangeNotifier {
  final Listenable _authChanges;
  final PatientVaultResolver _resolve;
  final PatientVaultOpener _open;
  AppDatabase? _database;
  PatientVaultScope? _scope;
  Object? _failure;
  bool _ready = false;
  bool _disposed = false;
  int _generation = 0;

  PatientVaultSessionCoordinator({
    required Listenable authChanges,
    required PatientVaultResolver resolve,
    PatientVaultOpener? open,
  })  : _authChanges = authChanges,
        _resolve = resolve,
        _open = open ?? _defaultOpen;

  static Future<AppDatabase> _defaultOpen(PatientVaultScope scope) async =>
      AppDatabase.forPatientVault(scope);

  bool get isReady => _ready;
  bool get isSwitching => !_ready;
  bool get hasVault => _database != null;
  bool get isBlocked => !_ready || _failure != null;
  Object? get failure => _failure;
  PatientVaultScope? get scope => _scope;

  /// Never retain this reference across authentication changes. Consumers
  /// should rebind inside a subtree keyed by the selected vault and generation.
  AppDatabase? get activeDatabase => isBlocked ? null : _database;

  Future<void> initialize() async {
    if (_disposed) throw StateError('Coordinator disposed');
    _authChanges.addListener(_onAuthChanged);
    await _switch();
  }

  void _onAuthChanged() {
    unawaited(_switch());
  }

  Future<void> _switch() async {
    if (_disposed) return;
    final generation = ++_generation;
    final previous = _database;
    // Redact synchronously. A -> B cannot read A while B's identity resolves.
    _database = null;
    _scope = null;
    _ready = false;
    _failure = null;
    notifyListeners();
    if (previous != null) {
      try {
        await previous.close();
      } catch (_) {
        // A failed close never authorizes returning the old patient data.
      }
    }
    if (_disposed || generation != _generation) return;

    try {
      final resolved = await _resolve();
      if (_disposed || generation != _generation) return;
      if (resolved == null) {
        // Unauthenticated, unknown/legacy or ambiguous binding: no vault.
        _ready = true;
        notifyListeners();
        return;
      }
      final next = await _open(resolved);
      if (_disposed || generation != _generation) {
        await next.close();
        return;
      }
      _database = next;
      _scope = resolved;
      _ready = true;
      notifyListeners();
    } catch (error) {
      if (_disposed || generation != _generation) return;
      _failure = error;
      _ready = true;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    ++_generation;
    _authChanges.removeListener(_onAuthChanged);
    final db = _database;
    _database = null;
    _scope = null;
    if (db != null) unawaited(db.close());
    super.dispose();
  }
}
