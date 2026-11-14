import 'package:drift/drift.dart';
import 'package:flutter/foundation.dart';

/// D1-P0: defense-in-depth for a patient executor which must never resume
/// SQL access after an auth transition or an AppLock revocation.
///
/// Drift may lazily reopen an executor after close(). Retiring a provider and
/// calling close() is NOT sufficient on its own to protect retained async
/// references. This sticky interceptor checks every supported statement path.
///
/// Candidate only: clinical use also requires authenticated recovery, old PWA
/// fencing, multi-tab serialization, WebKit, and an independent security GO.
final class RevocablePatientQueryGuard extends QueryInterceptor {
  final bool Function() _authorized;
  final Listenable _revocationSignals;
  final Future<void> Function()? _onClosed;
  bool _retired = false;

  RevocablePatientQueryGuard({
    required bool Function() authorized,
    required Listenable revocationSignals,
    Future<void> Function()? onClosed,
  }) : _authorized = authorized,
       _revocationSignals = revocationSignals,
       _onClosed = onClosed {
    _revocationSignals.addListener(revoke);
  }

  bool get isRevoked => _retired;

  void revoke() {
    if (_retired) return;
    _retired = true;
    _revocationSignals.removeListener(revoke);
  }

  void _requireAccess() {
    if (_retired || !_authorized()) {
      throw StateError('web_patient_vault_session_revoked');
    }
  }

  @override
  Future<bool> ensureOpen(QueryExecutor executor, QueryExecutorUser user) async {
    _requireAccess();
    final opened = await super.ensureOpen(executor, user);
    _requireAccess();
    return opened;
  }

  @override
  QueryExecutor beginExclusive(QueryExecutor parent) {
    _requireAccess();
    return super.beginExclusive(parent);
  }

  @override
  TransactionExecutor beginTransaction(QueryExecutor parent) {
    _requireAccess();
    return super.beginTransaction(parent);
  }

  @override
  Future<List<Map<String, Object?>>> runSelect(
      QueryExecutor executor, String statement, List<Object?> args) async {
    _requireAccess();
    final result = await super.runSelect(executor, statement, args);
    _requireAccess(); // Discard a result which completed after logout.
    return result;
  }

  @override
  Future<void> runCustom(
      QueryExecutor executor, String statement, List<Object?> args) async {
    _requireAccess();
    await super.runCustom(executor, statement, args);
    _requireAccess();
  }

  @override
  Future<int> runInsert(
      QueryExecutor executor, String statement, List<Object?> args) async {
    _requireAccess();
    final result = await super.runInsert(executor, statement, args);
    _requireAccess();
    return result;
  }

  @override
  Future<int> runUpdate(
      QueryExecutor executor, String statement, List<Object?> args) async {
    _requireAccess();
    final result = await super.runUpdate(executor, statement, args);
    _requireAccess();
    return result;
  }

  @override
  Future<int> runDelete(
      QueryExecutor executor, String statement, List<Object?> args) async {
    _requireAccess();
    final result = await super.runDelete(executor, statement, args);
    _requireAccess();
    return result;
  }

  @override
  Future<void> runBatched(QueryExecutor executor, BatchedStatements statements) async {
    _requireAccess();
    await super.runBatched(executor, statements);
    _requireAccess();
  }

  @override
  Future<void> commitTransaction(TransactionExecutor inner) async {
    _requireAccess();
    await super.commitTransaction(inner);
    _requireAccess();
  }

  @override
  Future<void> close(QueryExecutor inner) async {
    revoke();
    // Even when revoked, closing must release resources and rollback safely.
    try {
      await super.close(inner);
    } finally {
      final onClosed = _onClosed;
      if (onClosed != null) await onClosed();
    }
  }
}
