import 'package:amina/data/drift/d18_pre_cutover_atomic_promotion.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

final class _SyntheticMarkerStore implements D18CutoverMarkerStore {
  D18CutoverMarker? current;
  bool loseCas = false;
  bool loseAckAfterWrite = false;
  int changes = 0;

  @override
  Future<D18CutoverMarker?> read(PatientVaultScope scope) async => current;

  @override
  Future<bool> compareAndSwap({
    required PatientVaultScope scope,
    required D18CutoverMarker? expected,
    required D18CutoverMarker next,
  }) async {
    if (loseCas || current != expected) return false;
    current = next;
    changes++;
    if (loseAckAfterWrite) {
      loseAckAfterWrite = false;
      throw StateError('D18_TEST_ACK_LOST_AFTER_DURABLE_COMMIT');
    }
    return true;
  }
}

final class _Harness {
  final scope = PatientVaultScope.nativeDjango(734);
  final store = _SyntheticMarkerStore();
  int epoch = 10;
  int owner = 734;
  bool locked = false;
  bool writersStopped = true;
  bool barrierHeld = true;
  bool archiveVerified = true;
  bool sourcePresent = true;
  bool targetPresent = true;
  bool sourceIntegrityOk = true;
  bool targetIntegrityOk = true;
  bool ciphertextReopened = true;
  String logicalSource = List.filled(64, 'a').join();
  String logicalTarget = List.filled(64, 'a').join();
  String physical = List.filled(64, 'b').join();
  void Function()? afterProof;

  D18CutoverProof proof() => D18CutoverProof(
    sourceName: scope.databaseName,
    targetName: scope.databaseName + '_d18_cipher_v1',
    sourceLogicalSha256: logicalSource,
    targetLogicalSha256: logicalTarget,
    persistedCiphertextSha256: physical,
    schemaVersion: 12,
    sourcePresent: sourcePresent,
    targetPresent: targetPresent,
    sourceIntegrityOk: sourceIntegrityOk,
    targetIntegrityOk: targetIntegrityOk,
    sourceForeignKeysOk: true,
    targetForeignKeysOk: true,
    authenticatedCiphertextReopened: ciphertextReopened,
    independentRecoveryArchiveVerified: archiveVerified,
  );

  D18PreCutoverAtomicPromotion makeGate({
    bool allowUnfencedSyntheticFixture = true,
  }) => D18PreCutoverAtomicPromotion(
    // Explicit test-only bypass; never supply this in a clinical runtime.
    allowUnfencedSyntheticFixture: allowUnfencedSyntheticFixture,
    scope: scope,
    resolveAuthenticatedScope: () async => PatientVaultScope.nativeDjango(owner),
    readAuthEpoch: () => epoch,
    isKeyLocked: () => locked,
    allPlaintextWritersQuiesced: () => writersStopped,
    exclusiveOriginBarrierHeld: () => barrierHeld,
    inspectUnderBarrier: () async {
      final snapshot = proof();
      afterProof?.call();
      return snapshot;
    },
    markerStore: store,
  );
}

void main() {
  test('uncertified old clients refuse preparation even when locks appear free',
      () async {
    final h = _Harness();
    // Both old gate callbacks claim success; neither can attest cached tabs.
    expect(h.writersStopped, isTrue);
    expect(h.barrierHeld, isTrue);
    await expectLater(h.makeGate(allowUnfencedSyntheticFixture: false)
        .prepare(), throwsStateError);
    expect(h.store.current, isNull);
    expect(h.store.changes, 0);
  });

  test('prepare is pending and activation requires explicit synthetic flag',
      () async {
    final h = _Harness();
    final gate = h.makeGate();
    final prepared = await gate.prepare();
    expect(prepared.phase, D18CutoverPhase.prepared);
    expect(h.store.current, prepared);
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: false,
    ), throwsStateError);
    expect(h.store.current!.phase, D18CutoverPhase.prepared);
    final active = await gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    );
    expect(active.phase, D18CutoverPhase.ciphertextActive);
    expect(h.store.changes, 2);
  });

  test('legacy unfenced gate refuses activation even with prepared marker',
      () async {
    final h = _Harness();
    final prepared = await h.makeGate().prepare(); // synthetic only
    await expectLater(h.makeGate(allowUnfencedSyntheticFixture: false)
        .activateForSyntheticTest(explicitSyntheticApproval: true),
        throwsStateError);
    expect(h.store.current, prepared);
    expect(h.store.changes, 1);
  });

  test('missing source refuses prepare, without creating marker', () async {
    final h = _Harness()..sourcePresent = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
    expect(h.store.changes, 0);
  });

  test('ciphertext missing or unauthenticated refuses prepare', () async {
    final h = _Harness()..targetPresent = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
    h.targetPresent = true;
    h.ciphertextReopened = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
  });

  test('missing independent recovery archive refuses marker creation',
      () async {
    final h = _Harness()..archiveVerified = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.changes, 0);
  });

  test('schema or physical integrity mismatch rejects preparation',
      () async {
    final h = _Harness()..logicalTarget = List.filled(64, 'c').join();
    await expectLater(h.makeGate().prepare(), throwsStateError);
    h.logicalTarget = h.logicalSource;
    h.sourceIntegrityOk = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    h.sourceIntegrityOk = true;
    h.targetIntegrityOk = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
  });

  test('authenticated patient required, audit / wrong owner denied',
      () async {
    final h = _Harness()..owner = 812;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
    final audit = D18PreCutoverAtomicPromotion(
      scope: PatientVaultScope.auditOnly(),
      resolveAuthenticatedScope: () async => PatientVaultScope.auditOnly(),
      readAuthEpoch: () => 10,
      isKeyLocked: () => false,
      allPlaintextWritersQuiesced: () => true,
      allowUnfencedSyntheticFixture: true, // synthetic audit denial only
      exclusiveOriginBarrierHeld: () => true,
      inspectUnderBarrier: () async => h.proof(),
      markerStore: h.store,
    );
    await expectLater(audit.prepare(), throwsStateError);
    expect(h.store.current, isNull);
  });

  test('key lock and legacy-writer gates refuse all pointer writes', () async {
    final h = _Harness()..locked = true;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    h.locked = false;
    h.writersStopped = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    h.writersStopped = true;
    h.barrierHeld = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
  });

  test('source barrier lost after proof cannot commit prepared marker',
      () async {
    final h = _Harness();
    h.afterProof = () => h.barrierHeld = false;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
    expect(h.store.changes, 0);
    // A verified point-in-time snapshot does not grant a durable write gate.
  });

  test('late plaintext writer after prepared proof blocks activation',
      () async {
    final h = _Harness();
    final gate = h.makeGate();
    final pending = await gate.prepare();
    h.afterProof = () => h.writersStopped = false;
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(h.store.current, pending);
    expect(h.store.current!.phase, D18CutoverPhase.prepared);
    expect(h.store.changes, 1);
  });

  test('epoch change during verification cannot create pending marker',
      () async {
    final h = _Harness();
    h.afterProof = () => h.epoch++;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, isNull);
    expect(h.store.changes, 0);
  });

  test('epoch or patient changes after prepare cannot activate', () async {
    final h = _Harness();
    final gate = h.makeGate();
    await gate.prepare();
    h.epoch++;
    h.locked = true;
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    h.locked = false;
    h.owner = 812;
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(h.store.current!.phase, D18CutoverPhase.prepared);
  });

  test('tampered source or destination after prepare cannot activate',
      () async {
    final h = _Harness();
    final gate = h.makeGate();
    await gate.prepare();
    h.logicalSource = List.filled(64, 'c').join();
    h.logicalTarget = h.logicalSource;
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(h.store.current!.phase, D18CutoverPhase.prepared);
    h.logicalSource = List.filled(64, 'a').join();
    h.logicalTarget = h.logicalSource;
    h.physical = List.filled(64, 'd').join();
    await expectLater(gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(h.store.changes, 1);
  });

  test('CAS conflicts do not overwrite another tab marker', () async {
    final h = _Harness()..store.loseCas = true;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.changes, 0);
    h.store.loseCas = false;
    final original = await h.makeGate().prepare();
    h.store.loseCas = true;
    await expectLater(h.makeGate().activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(h.store.current, original);
  });

  test('crash after prepare may be resumed only after reattestation', () async {
    final h = _Harness();
    await h.makeGate().prepare();
    // Recreated coordinator simulates restart, but marker remains durable in
    // the fake store. This DOES NOT prove IndexedDB persistence.
    final resumed = h.makeGate();
    final active = await resumed.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    );
    expect(active.phase, D18CutoverPhase.ciphertextActive);
    await expectLater(resumed.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError); // Never auto-activate/replay an active marker.
  });

  test('lost CAS acknowledgement cannot silently clear active pointer',
      () async {
    final h = _Harness();
    await h.makeGate().prepare();
    h.store.loseAckAfterWrite = true;
    await expectLater(h.makeGate().activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    final persisted = await h.makeGate().inspectMarker();
    expect(persisted!.phase, D18CutoverPhase.ciphertextActive);
    expect(h.store.changes, 2);
    // Caller must inspect+reauthenticate; never infer failure == rollback.
  });

  test('lost prepare acknowledgement leaves a quarantined prepared marker; '
      'replay never overwrites it', () async {
    final h = _Harness()..store.loseAckAfterWrite = true;
    await expectLater(h.makeGate().prepare(), throwsStateError);
    final persisted = await h.makeGate().inspectMarker();
    expect(persisted, isNotNull);
    expect(persisted!.phase, D18CutoverPhase.prepared);
    expect(h.store.changes, 1);
    await expectLater(h.makeGate().prepare(), throwsStateError);
    expect(h.store.current, same(persisted));
    expect(h.store.changes, 1);
    // In-memory synthetic CAS only: no browser durability claimed.
  });

  test('two synthetic migrators cannot both prepare the same vault', () async {
    final h = _Harness();
    final outcomes = await Future.wait(<Future<bool>>[
      h.makeGate().prepare().then((_) => true,
        onError: (Object _) => false),
      h.makeGate().prepare().then((_) => true,
        onError: (Object _) => false),
    ]);
    expect(outcomes.where((success) => success).length, 1);
    expect(h.store.current!.phase, D18CutoverPhase.prepared);
    expect(h.store.changes, 1);
    // Real IndexedDB atomicity is covered by the separate Web probe.
  });

  test('existing active marker cannot be overwritten by prepare',
      () async {
    final h = _Harness();
    final gate = h.makeGate();
    await gate.prepare();
    await gate.activateForSyntheticTest(explicitSyntheticApproval: true);
    await expectLater(gate.prepare(), throwsStateError);
    expect(h.store.current!.phase, D18CutoverPhase.ciphertextActive);
    expect(h.store.changes, 2);
  });
}
