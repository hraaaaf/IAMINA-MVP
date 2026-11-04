// D18 WEB — PRE-CUTOVER ATOMIC PROMOTION CONTRACT, SYNTHETIC ONLY.
// Not a production marker store, data migration, key policy or runtime vault.
// NEVER wire into AppDatabase.forPatientVault or patient providers without
// independent storage durability, crypto, AuthEpoch and migration validation.
import 'patient_vault_scope.dart';

enum D18CutoverPhase { prepared, ciphertextActive }

/// Durable pointer *contract*. A production adapter would need a genuinely
/// atomic compare-and-swap across tabs, with crash-safe persistence. A
/// read-modify-write localStorage, plain IndexedDB read+put across transactions,
/// or an in-memory fake is NOT a production implementation.
abstract interface class D18CutoverMarkerStore {
  Future<D18CutoverMarker?> read(PatientVaultScope scope);
  Future<bool> compareAndSwap({
    required PatientVaultScope scope,
    required D18CutoverMarker? expected,
    required D18CutoverMarker next,
  });
}

/// No key, patient content, SQL or passphrase is retained in this pointer.
/// A hash is only as reliable as the trusted verifier that produced it.
final class D18CutoverMarker {
  final String sourceName;
  final String targetName;
  final String logicalSha256;
  final String ciphertextSha256;
  final int schemaVersion;
  final D18CutoverPhase phase;

  const D18CutoverMarker({
    required this.sourceName,
    required this.targetName,
    required this.logicalSha256,
    required this.ciphertextSha256,
    required this.schemaVersion,
    required this.phase,
  });

  D18CutoverMarker withPhase(D18CutoverPhase next) => D18CutoverMarker(
    sourceName: sourceName,
    targetName: targetName,
    logicalSha256: logicalSha256,
    ciphertextSha256: ciphertextSha256,
    schemaVersion: schemaVersion,
    phase: next,
  );

  @override
  bool operator ==(Object other) =>
      other is D18CutoverMarker &&
      other.sourceName == sourceName &&
      other.targetName == targetName &&
      other.logicalSha256 == logicalSha256 &&
      other.ciphertextSha256 == ciphertextSha256 &&
      other.schemaVersion == schemaVersion &&
      other.phase == phase;

  @override
  int get hashCode => Object.hash(
    sourceName, targetName, logicalSha256, ciphertextSha256,
    schemaVersion, phase,
  );
}

/// Assertions FROM an independently trusted physical/sqlite3mc verifier.
/// This object is NOT itself cryptographic attestation. The eventual verifier
/// must inventory every table, view, index, trigger, sequence, row, BLOB and FK
/// and hash a stable canonical snapshot under an origin-wide writers barrier.
/// Its ciphertext hash must refer to physically persisted, closed-and-reopened
/// SQLite3MC bytes, not plaintext / synthetic memory.
final class D18CutoverProof {
  final String sourceName;
  final String targetName;
  final String sourceLogicalSha256;
  final String targetLogicalSha256;
  final String persistedCiphertextSha256;
  final int schemaVersion;
  final bool sourcePresent;
  final bool targetPresent;
  final bool sourceIntegrityOk;
  final bool targetIntegrityOk;
  final bool sourceForeignKeysOk;
  final bool targetForeignKeysOk;
  final bool authenticatedCiphertextReopened;
  final bool independentRecoveryArchiveVerified;

  const D18CutoverProof({
    required this.sourceName,
    required this.targetName,
    required this.sourceLogicalSha256,
    required this.targetLogicalSha256,
    required this.persistedCiphertextSha256,
    required this.schemaVersion,
    required this.sourcePresent,
    required this.targetPresent,
    required this.sourceIntegrityOk,
    required this.targetIntegrityOk,
    required this.sourceForeignKeysOk,
    required this.targetForeignKeysOk,
    required this.authenticatedCiphertextReopened,
    required this.independentRecoveryArchiveVerified,
  });
}

/// Does NOT open, delete, migrate, activate or publish any clinical database.
/// PRE-CUTOVER only: produces a two-stage marker for external offline testing.
/// A pending marker MUST be treated as NO-GO by any future runtime reader.
/// The actual clinical runtime MUST never use this class as an authorization
/// decision or permit a marker to substitute for fresh scope/key verification.
final class D18PreCutoverAtomicPromotion {
  final PatientVaultScope scope;
  final Future<PatientVaultScope?> Function() resolveAuthenticatedScope;
  final int Function() readAuthEpoch;
  final bool Function() isKeyLocked;
  final bool Function() allPlaintextWritersQuiesced;
  // No browser code can prove a pre-D18 cached tab is absent merely by
  // acquiring Web Locks. The explicit override below is for synthetic tests
  // ONLY; leaving it false rejects all promotion, even if locks look free.
  final bool allowUnfencedSyntheticFixture;
  final bool Function() exclusiveOriginBarrierHeld;
  final Future<D18CutoverProof> Function() inspectUnderBarrier;
  final D18CutoverMarkerStore markerStore;

  const D18PreCutoverAtomicPromotion({
    required this.scope,
    required this.resolveAuthenticatedScope,
    required this.readAuthEpoch,
    required this.isKeyLocked,
    required this.allPlaintextWritersQuiesced,
    this.allowUnfencedSyntheticFixture = false,
    required this.exclusiveOriginBarrierHeld,
    required this.inspectUnderBarrier,
    required this.markerStore,
  });

  void _checkImmediate(int epoch) {
    if (!allowUnfencedSyntheticFixture) {
      throw StateError('D18_OLD_CACHED_TABS_UNFENCED_NO_CUTOVER');
    }
    if (readAuthEpoch() != epoch || isKeyLocked() ||
        !allPlaintextWritersQuiesced() || !exclusiveOriginBarrierHeld()) {
      throw StateError('D18_CUTOVER_AUTH_OR_WRITER_GATE_CLOSED');
    }
  }

  Future<void> _checkAuthenticated(int epoch) async {
    _checkImmediate(epoch);
    final verified = await resolveAuthenticatedScope();
    _checkImmediate(epoch);
    if (scope.databaseName == PatientVaultScope.auditOnly().databaseName ||
        !scope.databaseName.startsWith('amina_vault_v1_') ||
        verified?.databaseName != scope.databaseName) {
      throw StateError('D18_CUTOVER_WRONG_PATIENT_SCOPE');
    }
  }

  D18CutoverMarker _validateProof(D18CutoverProof p) {
    final source = scope.databaseName;
    final destination = source + '_d18_cipher_v1';
    final digest = RegExp(r'^[a-f0-9]{64}$');
    if (p.sourceName != source || p.targetName != destination ||
        p.sourceName == p.targetName ||
        p.schemaVersion != 12 ||
        !p.sourcePresent || !p.targetPresent ||
        !p.sourceIntegrityOk || !p.targetIntegrityOk ||
        !p.sourceForeignKeysOk || !p.targetForeignKeysOk ||
        !p.authenticatedCiphertextReopened ||
        !p.independentRecoveryArchiveVerified ||
        !digest.hasMatch(p.sourceLogicalSha256) ||
        !digest.hasMatch(p.targetLogicalSha256) ||
        !digest.hasMatch(p.persistedCiphertextSha256) ||
        p.sourceLogicalSha256 != p.targetLogicalSha256) {
      throw StateError('D18_CUTOVER_PROOF_INCOMPLETE_OR_MISMATCHED');
    }
    return D18CutoverMarker(
      sourceName: source,
      targetName: destination,
      logicalSha256: p.sourceLogicalSha256,
      ciphertextSha256: p.persistedCiphertextSha256,
      schemaVersion: p.schemaVersion,
      phase: D18CutoverPhase.prepared,
    );
  }

  /// Persist only a PREPARED marker; it is never a publishable patient vault.
  /// On post-CAS failure a prepared marker may remain. Do not auto-delete it.
  Future<D18CutoverMarker> prepare() async {
    final epoch = readAuthEpoch();
    await _checkAuthenticated(epoch);
    final old = await markerStore.read(scope);
    await _checkAuthenticated(epoch);
    if (old != null) {
      throw StateError('D18_CUTOVER_MARKER_ALREADY_PRESENT');
    }
    final marker = _validateProof(await inspectUnderBarrier());
    await _checkAuthenticated(epoch);
    if (!await markerStore.compareAndSwap(
      scope: scope, expected: null, next: marker,
    )) {
      throw StateError('D18_CUTOVER_PREPARE_CAS_CONFLICT');
    }
    await _checkAuthenticated(epoch);
    if (await markerStore.read(scope) != marker) {
      throw StateError('D18_CUTOVER_PREPARED_MARKER_NOT_DURABLE');
    }
    await _checkAuthenticated(epoch);
    return marker;
  }

  /// Test-only synthetic approval flag is NOT clinical/operator authorization.
  /// A *future, separately audited* runtime would require an independent
  /// human approval and verified durable atomic marker transaction.
  /// If CAS commits but acknowledgement is lost, DO NOT rollback blindly:
  /// inspect the durable marker and re-attest before any further action.
  Future<D18CutoverMarker> activateForSyntheticTest({
    required bool explicitSyntheticApproval,
  }) async {
    if (!explicitSyntheticApproval) {
      throw StateError('D18_CUTOVER_SYNTHETIC_APPROVAL_MISSING');
    }
    final epoch = readAuthEpoch();
    await _checkAuthenticated(epoch);
    final pending = await markerStore.read(scope);
    await _checkAuthenticated(epoch);
    if (pending == null || pending.phase != D18CutoverPhase.prepared ||
        pending.sourceName != scope.databaseName ||
        pending.targetName != scope.databaseName + '_d18_cipher_v1') {
      throw StateError('D18_CUTOVER_NO_MATCHING_PENDING_MARKER');
    }
    final current = _validateProof(await inspectUnderBarrier());
    await _checkAuthenticated(epoch);
    if (current != pending) {
      throw StateError('D18_CUTOVER_SOURCE_OR_CIPHER_CHANGED');
    }
    final active = pending.withPhase(D18CutoverPhase.ciphertextActive);
    if (!await markerStore.compareAndSwap(
      scope: scope, expected: pending, next: active,
    )) {
      throw StateError('D18_CUTOVER_ACTIVATE_CAS_CONFLICT');
    }
    await _checkAuthenticated(epoch);
    if (await markerStore.read(scope) != active) {
      throw StateError('D18_CUTOVER_ACTIVE_MARKER_NOT_DURABLE');
    }
    await _checkAuthenticated(epoch);
    return active;
  }

  /// Observation only. NEVER automatically promote pending to active or
  /// infer an authorized clinical session from an active marker.
  Future<D18CutoverMarker?> inspectMarker() => markerStore.read(scope);
}
