// D18 PRE-CUTOVER ONLY: a disposable asynchronous session coordinator.
// NOT referenced by PatientVaultSessionController, PatientVaultAppHost or
// AppDatabase.forPatientVault. Never substitute it into production providers
// until full storage, migration, recovery and browser security gates pass.
import 'd18_pre_cutover_cipher_adapter.dart';
import 'd18_vault_key_policy.dart';
import 'patient_vault_scope.dart';

/// Owns an unpublished candidate across asynchronous auth and epoch changes.
/// It publishes ONLY to [activeUnpublished], never to clinical state.
final class D18PreCutoverSessionCoordinator<
    T extends D18UnpublishedVaultLifecycle> {
  final Future<PatientVaultScope?> Function() resolveAuthenticatedScope;
  final int Function() readAuthEpoch;

  T? _active;
  PatientVaultScope? _activeScope;
  int _generation = 0;
  bool _disposed = false;
  Future<void>? _disposeFuture;
  final Set<Future<void>> _inFlight = {};

  D18PreCutoverSessionCoordinator({
    required this.resolveAuthenticatedScope,
    required this.readAuthEpoch,
  });

  T? get activeUnpublished => _disposed ? null : _active;
  PatientVaultScope? get activeUnpublishedScope =>
      _disposed ? null : _activeScope;

  /// Detach the prior candidate synchronously before any async work.
  /// Caller supplies a *guarded* D18 opener and a live session-lock check.
  /// There is NO plaintext fallback, credential retry or auto-enrollment.
  Future<void> stageUnpublished({
    required PatientVaultScope requestedScope,
    required bool Function() isKeyLocked,
    required Future<T> Function() openCandidate,
  }) {
    if (_disposed) {
      return Future<void>.error(StateError('D18 pre-cutover host disposed'));
    }
    final operation = _stage(
      requestedScope: requestedScope,
      isKeyLocked: isKeyLocked,
      openCandidate: openCandidate,
    );
    _inFlight.add(operation);
    // Track completion without creating an unobserved error future.
    operation.then(
      (_) => _inFlight.remove(operation),
      onError: (Object _, StackTrace __) => _inFlight.remove(operation),
    );
    return operation;
  }

  void _assertCurrent(
    int generation, int epoch, bool Function() isKeyLocked,
  ) {
    if (_disposed || generation != _generation ||
        readAuthEpoch() != epoch || isKeyLocked()) {
      throw StateError('D18 unpublished session changed or key locked');
    }
  }

  Future<void> _stage({
    required PatientVaultScope requestedScope,
    required bool Function() isKeyLocked,
    required Future<T> Function() openCandidate,
  }) async {
    final generation = ++_generation;
    final epoch = readAuthEpoch();
    final old = _active;
    _active = null;
    _activeScope = null;
    // The prior physical worker must be closed before a replacement opens.
    if (old != null) await old.close();
    _assertCurrent(generation, epoch, isKeyLocked);

    final name = requestedScope.databaseName;
    if (!name.startsWith('amina_vault_v1_') ||
        name == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D18 pre-cutover patient scope required');
    }
    final before = await resolveAuthenticatedScope();
    _assertCurrent(generation, epoch, isKeyLocked);
    if (before?.databaseName != name) {
      throw StateError('D18 pre-cutover owner mismatch before open');
    }

    T? candidate;
    try {
      candidate = await openCandidate();
      _assertCurrent(generation, epoch, isKeyLocked);
      final after = await resolveAuthenticatedScope();
      _assertCurrent(generation, epoch, isKeyLocked);
      if (after?.databaseName != name) {
        throw StateError('D18 pre-cutover owner mismatch after open');
      }
      _active = candidate;
      _activeScope = requestedScope;
      candidate = null; // Ownership transferred exactly once.
    } finally {
      // Logout, epoch change, late result or incorrect owner must dispose
      // the worker, rather than expose a stale database for one frame.
      if (candidate != null) await candidate.close();
    }
  }

  /// Immediate revocation, even if an opening is still in flight.
  /// Pending stages see a changed generation and dispose their late result.
  Future<void> invalidate() async {
    ++_generation;
    final current = _active;
    _active = null;
    _activeScope = null;
    if (current != null) await current.close();
  }

  /// Waits for outstanding candidate openings to finish and be discarded,
  /// so app shutdown cannot leave an unpublished worker lease abandoned.
  Future<void> dispose() => _disposeFuture ??= _disposeOnce();

  Future<void> _disposeOnce() async {
    _disposed = true;
    try {
      await invalidate();
    } finally {
      final pending = _inFlight.toList();
      await Future.wait(pending.map((operation) async {
        try {
          await operation;
        } on Object {
          // Open errors belong to the caller. Cleanup still completes.
        }
      }));
    }
  }
}

/// Explicit wiring to the existing guarded encrypted adapter. This extension
/// is never called from the clinical patient vault host or its providers.
extension D18PreCutoverCipherStage
    on D18PreCutoverSessionCoordinator<D18UnpublishedCipherVault> {
  Future<void> stageEncryptedCandidate({
    required PatientVaultScope requestedScope,
    required D18VaultKeySession keySession,
    required D18CipherVaultOpenIntent intent,
    required D18PreCutoverCipherAdapter adapter,
  }) => stageUnpublished(
    requestedScope: requestedScope,
    isKeyLocked: () => keySession.isLocked,
    openCandidate: () => adapter.openUnpublished(
      scope: requestedScope,
      keySession: keySession,
      intent: intent,
    ),
  );
}
