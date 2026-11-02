import 'd18_vault_key_policy.dart';
import 'patient_vault_scope.dart';

/// D18 lot 2 — PRE-CUTOVER contract for a future encrypted Web connector.
///
/// The caller MUST supply the scope resolved from the authenticated principal,
/// not merely a string supplied by the browser. This does not perform SQLite
/// migrations or enable encryption in the clinical application.
final class D18KeyedOpenGuard {
  final Future<PatientVaultScope?> Function() resolveAuthenticatedScope;
  final int Function() readAuthEpoch;

  const D18KeyedOpenGuard({
    required this.resolveAuthenticatedScope,
    required this.readAuthEpoch,
  });

  /// A new encrypted executor may only be PUBLISHED after this method returns.
  /// On stale auth, [discardUnpublished] must close any candidate connection.
  /// The transient key copy is overwritten even when open/verification fails.
  Future<T> openUnpublished<T>({
    required PatientVaultScope requestedScope,
    required D18VaultKeySession keySession,
    required Future<T> Function(List<int> ephemeralKey) createUnpublished,
    required Future<void> Function(T) discardUnpublished,
  }) async {
    final scopeName = requestedScope.databaseName;
    if (!scopeName.startsWith('amina_vault_v1_') ||
        scopeName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D18 patient scope required');
    }
    final epoch = readAuthEpoch();
    final verifiedBefore = await resolveAuthenticatedScope();
    if (readAuthEpoch() != epoch ||
        verifiedBefore?.databaseName != scopeName) {
      throw StateError('D18 authentication changed before open');
    }

    final extracted =
        await keySession.requireUnlockedKeyForScope(requestedScope).extractBytes();
    T? candidate;
    var created = false;
    try {
      if (readAuthEpoch() != epoch || keySession.isLocked) {
        throw StateError('D18 session changed while obtaining key');
      }
      candidate = await createUnpublished(extracted);
      created = true;
      final verifiedAfter = await resolveAuthenticatedScope();
      if (readAuthEpoch() != epoch ||
          verifiedAfter?.databaseName != scopeName ||
          keySession.isLocked) {
        throw StateError('D18 authentication changed while opening');
      }
      return candidate as T;
    } catch (_) {
      if (created) await discardUnpublished(candidate as T);
      rethrow;
    } finally {
      extracted.fillRange(0, extracted.length, 0);
    }
  }
}
