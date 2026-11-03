import 'dart:async';

import 'package:amina/data/drift/d18_pre_cutover_cipher_adapter.dart';
import 'package:amina/data/drift/d18_pre_cutover_session_coordinator.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter_test/flutter_test.dart';

final class _FakeVault implements D18UnpublishedVaultLifecycle {
  final String id;
  int closed = 0;

  _FakeVault(this.id);

  @override
  Future<void> close() async { closed++; }
}

void main() {
  final a = PatientVaultScope.nativeDjango(734);
  final b = PatientVaultScope.nativeDjango(812);

  test('A to B to A: detach prior candidate before opening another', () async {
    var owner = a;
    var epoch = 1;
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => owner,
      readAuthEpoch: () => epoch,
    );
    addTearDown(host.dispose);
    final a1 = _FakeVault('A1'), b1 = _FakeVault('B1');
    final a2 = _FakeVault('A2');
    await host.stageUnpublished(
      requestedScope: a,
      isKeyLocked: () => false,
      openCandidate: () async => a1,
    );
    expect(host.activeUnpublished, same(a1));
    owner = b; epoch++;
    final waiting = Completer<_FakeVault>();
    final started = Completer<void>();
    final switchToB = host.stageUnpublished(
      requestedScope: b,
      isKeyLocked: () => false,
      openCandidate: () {
        started.complete();
        return waiting.future;
      },
    );
    await started.future;
    expect(host.activeUnpublished, isNull,
      reason: 'A must disappear before B awaits its worker');
    expect(a1.closed, 1);
    waiting.complete(b1);
    await switchToB;
    expect(host.activeUnpublished, same(b1));
    owner = a; epoch++;
    await host.stageUnpublished(
      requestedScope: a,
      isKeyLocked: () => false,
      openCandidate: () async => a2,
    );
    expect(host.activeUnpublished, same(a2));
    expect(b1.closed, 1);
    await host.dispose();
    expect(a2.closed, 1);
  });

  test('logout during slow worker opening discards late candidate', () async {
    var epoch = 10;
    final opening = Completer<_FakeVault>();
    final started = Completer<void>();
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => epoch,
    );
    addTearDown(host.dispose);
    final operation = host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => false,
      openCandidate: () {
        started.complete();
        return opening.future;
      },
    );
    final rejected = expectLater(operation, throwsStateError);
    await started.future;
    epoch++;
    await host.invalidate();
    expect(host.activeUnpublished, isNull);
    final late = _FakeVault('A stale');
    opening.complete(late);
    await rejected;
    expect(late.closed, 1);
    expect(host.activeUnpublished, isNull);
  });

  test('scope changed during authentication recheck disposes worker', () async {
    var owner = a;
    final candidate = _FakeVault('unpublished');
    var checks = 0;
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async {
        checks++;
        return checks == 1 ? owner : b;
      },
      readAuthEpoch: () => 5,
    );
    addTearDown(host.dispose);
    await expectLater(host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => false,
      openCandidate: () async => candidate,
    ), throwsStateError);
    expect(candidate.closed, 1);
    expect(host.activeUnpublished, isNull);
    owner = b;
  });

  test('locked key before and during open denies publication', () async {
    var locked = true;
    var opened = 0;
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 1,
    );
    addTearDown(host.dispose);
    await expectLater(host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => locked,
      openCandidate: () async { opened++; return _FakeVault('forbidden'); },
    ), throwsStateError);
    expect(opened, 0);
    locked = false;
    final candidate = _FakeVault('late locked');
    await expectLater(host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => locked,
      openCandidate: () async {locked = true; return candidate;},
    ), throwsStateError);
    expect(candidate.closed, 1);
    expect(host.activeUnpublished, isNull);
  });

  test('wrong key / worker exception never falls back to plaintext', () async {
    var calls = 0;
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 1,
    );
    addTearDown(host.dispose);
    await expectLater(host.stageUnpublished(
      requestedScope: a,
      isKeyLocked: () => false,
      openCandidate: () async {
        calls++;
        throw StateError('D18_WORKER_KEY_REJECTED');
      },
    ), throwsStateError);
    expect(calls, 1);
    expect(host.activeUnpublished, isNull);
    expect(host.activeUnpublishedScope, isNull);
  });

  test('audit or foreign scope must never invoke worker', () async {
    var opens = 0;
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 1,
    );
    addTearDown(host.dispose);
    Future<_FakeVault> forbidden() async {
      opens++; return _FakeVault('forbidden');
    }
    await expectLater(host.stageUnpublished(
      requestedScope: PatientVaultScope.auditOnly(),
      isKeyLocked: () => false, openCandidate: forbidden,
    ), throwsStateError);
    await expectLater(host.stageUnpublished(
      requestedScope: b, isKeyLocked: () => false,
      openCandidate: forbidden,
    ), throwsStateError);
    expect(opens, 0);
    expect(host.activeUnpublished, isNull);
  });

  test('invalidate and dispose are idempotent on an active worker', () async {
    final active = _FakeVault('single');
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 1,
    );
    await host.stageUnpublished(
      requestedScope: a,
      isKeyLocked: () => false,
      openCandidate: () async => active,
    );
    await Future.wait([host.invalidate(), host.invalidate()]);
    expect(active.closed, 1);
    await Future.wait([host.dispose(), host.dispose()]);
    expect(active.closed, 1);
    await expectLater(host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => false,
      openCandidate: () async => _FakeVault('too late'),
    ), throwsStateError);
  });


  test('epoch bump masks active candidate immediately, before invalidation', () async {
    var epoch = 10;
    final candidate = _FakeVault('epoch A');
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => epoch,
    );
    await host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => false,
      openCandidate: () async => candidate,
    );
    expect(host.activeUnpublished, same(candidate));
    epoch++; // Simulate auth transition BEFORE the observer callback runs.
    expect(host.activeUnpublished, isNull);
    expect(host.activeUnpublishedScope, isNull);
    await host.invalidate();
    expect(candidate.closed, 1);
    await host.dispose();
  });

  test('key locked while active masks candidate without a host event', () async {
    var locked = false;
    final candidate = _FakeVault('locked A');
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 10,
    );
    await host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => locked,
      openCandidate: () async => candidate,
    );
    expect(host.activeUnpublished, same(candidate));
    locked = true;
    expect(host.activeUnpublished, isNull);
    expect(host.activeUnpublishedScope, isNull);
    await host.invalidate();
    expect(candidate.closed, 1);
    await host.dispose();
  });

  test('dispose awaits in-flight closure after an unfinished open', () async {
    final opened = Completer<_FakeVault>();
    final started = Completer<void>();
    final host = D18PreCutoverSessionCoordinator<_FakeVault>(
      resolveAuthenticatedScope: () async => a,
      readAuthEpoch: () => 1,
    );
    final operation = host.stageUnpublished(
      requestedScope: a, isKeyLocked: () => false,
      openCandidate: () {
        started.complete(); return opened.future;
      },
    );
    final rejected = expectLater(operation, throwsStateError);
    await started.future;
    final disposing = host.dispose();
    final candidate = _FakeVault('late shutdown');
    opened.complete(candidate);
    await rejected;
    await disposing;
    expect(candidate.closed, 1);
    expect(host.activeUnpublished, isNull);
  });
}
