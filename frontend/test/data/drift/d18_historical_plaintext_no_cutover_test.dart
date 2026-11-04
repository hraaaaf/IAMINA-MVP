// IAMINA D18 P0-A. Test-only: historical plaintext sources have no
// certified writer fencing. A complete *claim* of crypto/source integrity,
// Web Locks, app consent and user presence must not bypass default NO-CUTOVER.
// Never used to access real patient data.
import 'package:amina/data/drift/d18_pre_cutover_atomic_promotion.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

final class _MarkerStore implements D18CutoverMarkerStore {
  D18CutoverMarker? existing;
  int reads = 0;
  int writes = 0;

  @override
  Future<D18CutoverMarker?> read(PatientVaultScope scope) async {
    reads++;
    return existing;
  }

  @override
  Future<bool> compareAndSwap({
    required PatientVaultScope scope,
    required D18CutoverMarker? expected,
    required D18CutoverMarker next,
  }) async {
    writes++;
    throw StateError('D18_PRODUCTION_MARKER_MUTATION_FORBIDDEN');
  }
}

final class _Fixture {
  final scope = PatientVaultScope.nativeDjango(734);
  final store = _MarkerStore();
  int authChecks = 0;
  int physicalInspections = 0;
  bool barrierHeld = true;
  bool activeWritersAppearQuiescent = true;
  int authEpoch = 4;

  D18PreCutoverAtomicPromotion get gate => D18PreCutoverAtomicPromotion(
    // Deliberately omit allowUnfencedSyntheticFixture:
    // default must NEVER permit a historical clinical cutover.
    scope: scope,
    resolveAuthenticatedScope: () async {
      authChecks++;
      return scope;
    },
    readAuthEpoch: () => authEpoch,
    isKeyLocked: () => false,
    allPlaintextWritersQuiesced: () => activeWritersAppearQuiescent,
    exclusiveOriginBarrierHeld: () => barrierHeld,
    inspectUnderBarrier: () async {
      physicalInspections++;
      throw StateError('D18_UNSAFE_INSPECTION_SHOULD_NOT_RUN');
    },
    markerStore: store,
  );

  void expectNoSideEffects() {
    expect(authChecks, 0);
    expect(physicalInspections, 0);
    expect(store.writes, 0);
  }
}

void main() {
  test('legacy plaintext: apparent good locks and quiet writers still NO-GO',
      () async {
    final fixture = _Fixture();
    await expectLater(
      fixture.gate.prepare(),
      throwsA(isA<StateError>().having(
        (e) => e.message,
        'code',
        'D18_OLD_CACHED_TABS_UNFENCED_NO_CUTOVER',
      )),
    );
    fixture.expectNoSideEffects();
    expect(fixture.store.reads, 0);
  });

  test('legacy plaintext: unknown writer and no lock also NO-GO',
      () async {
    final fixture = _Fixture()
      ..barrierHeld = false
      ..activeWritersAppearQuiescent = false;
    await expectLater(fixture.gate.prepare(), throwsStateError);
    fixture.expectNoSideEffects();
    expect(fixture.store.reads, 0);
  });

  test('legacy plaintext: stale prepared marker and explicit test approval'
      ' still cannot activate', () async {
    final fixture = _Fixture();
    final marker = D18CutoverMarker(
      sourceName: fixture.scope.databaseName,
      targetName: fixture.scope.databaseName + '_d18_cipher_v1',
      logicalSha256: List.filled(64, 'a').join(),
      ciphertextSha256: List.filled(64, 'b').join(),
      schemaVersion: 12,
      phase: D18CutoverPhase.prepared,
    );
    fixture.store.existing = marker;
    await expectLater(
      fixture.gate.activateForSyntheticTest(
        explicitSyntheticApproval: true,
      ),
      throwsA(isA<StateError>().having(
        (e) => e.message,
        'code',
        'D18_OLD_CACHED_TABS_UNFENCED_NO_CUTOVER',
      )),
    );
    expect(fixture.store.existing, same(marker));
    fixture.expectNoSideEffects();
    expect(fixture.store.reads, 0);
  });

  test('legacy plaintext: active marker cannot be promoted or overwritten',
      () async {
    final fixture = _Fixture();
    final marker = D18CutoverMarker(
      sourceName: fixture.scope.databaseName,
      targetName: fixture.scope.databaseName + '_d18_cipher_v1',
      logicalSha256: List.filled(64, 'c').join(),
      ciphertextSha256: List.filled(64, 'd').join(),
      schemaVersion: 12,
      phase: D18CutoverPhase.ciphertextActive,
    );
    fixture.store.existing = marker;
    await expectLater(fixture.gate.prepare(), throwsStateError);
    await expectLater(fixture.gate.activateForSyntheticTest(
      explicitSyntheticApproval: true,
    ), throwsStateError);
    expect(fixture.store.existing, same(marker));
    fixture.expectNoSideEffects();
    expect(fixture.store.reads, 0);
  });
}
