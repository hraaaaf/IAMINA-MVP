import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

final class _FakeAuth extends ChangeNotifier {
  void changed() => notifyListeners();
}

PatientVaultDbLease syntheticLease(
  PatientVaultScope scope, {
  Future<void> Function()? releaseWorker,
  bool Function()? locked,
}) => PatientVaultDbLease(
  scope: scope,
  database: AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
  releaseWorker: releaseWorker,
  isKeyLocked: locked,
);

void main() {
  final a = PatientVaultScope.nativeDjango(734);
  final b = PatientVaultScope.nativeDjango(812);

  test('D18 opt-in async lease A to B to A closes physical workers in order',
      () async {
    final auth = _FakeAuth();
    var owner = a;
    final events = <String>[];
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => owner,
      openVaultLease: (scope) async {
        final name = scope.databaseName;
        events.add('open:' + name);
        return syntheticLease(scope, releaseWorker: () async {
          events.add('release:' + name);
        });
      },
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, a.databaseName);
    owner = b;
    AuthEpoch.advance();
    auth.changed();
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, b.databaseName);
    owner = a;
    AuthEpoch.advance();
    auth.changed();
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, a.databaseName);
    expect(events, containsAllInOrder([
      'open:' + a.databaseName, 'release:' + a.databaseName,
      'open:' + b.databaseName, 'release:' + b.databaseName,
      'open:' + a.databaseName,
    ]));
  });

  test('late A worker closes before asynchronous B opens', () async {
    final auth = _FakeAuth();
    var owner = a;
    final started = Completer<void>();
    final openingA = Completer<PatientVaultDbLease>();
    final events = <String>[];
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => owner,
      openVaultLease: (scope) async {
        if (scope.databaseName == a.databaseName) {
          started.complete();
          return openingA.future;
        }
        events.add('openB');
        return syntheticLease(scope, releaseWorker: () async {
          events.add('closeB');
        });
      },
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await started.future;
    owner = b;
    AuthEpoch.advance();
    auth.changed();
    final bReady = controller.reconcile();
    expect(controller.activeDatabase, isNull);
    expect(events, isEmpty);
    openingA.complete(syntheticLease(a, releaseWorker: () async {
      events.add('closeA');
    }));
    await bReady;
    expect(controller.activeScope?.databaseName, b.databaseName);
    expect(events, containsAllInOrder(['closeA', 'openB']));
  });

  test('wrong-owner async DB rejected and worker released', () async {
    final auth = _FakeAuth();
    var releases = 0;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => a,
      openVaultLease: (scope) async => PatientVaultDbLease(
        scope: scope,
        database: AppDatabase.testPatientVault(NativeDatabase.memory(), b),
        releaseWorker: () async { releases++; },
      ),
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNull);
    expect(controller.hasVault, isFalse);
    expect(releases, 1);
  });

  test('key lock immediately masks active DB and rejects next opening',
      () async {
    final auth = _FakeAuth();
    var locked = false;
    var releases = 0;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => a,
      openVaultLease: (scope) async => syntheticLease(
        scope, locked: () => locked,
        releaseWorker: () async { releases++; },
      ),
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNotNull);
    locked = true;
    expect(controller.activeDatabase, isNull);
    await controller.reconcile(); // Future key-lock observer must call this.
    expect(controller.activeDatabase, isNull);
    expect(releases, 2);
  });

  test('worker close failure forbids a subsequent patient open', () async {
    final auth = _FakeAuth();
    var owner = a;
    var attemptedB = 0;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => owner,
      openVaultLease: (scope) async {
        if (scope.databaseName == b.databaseName) attemptedB++;
        return syntheticLease(scope, releaseWorker: () async {
          if (scope.databaseName == a.databaseName) {
            throw StateError('D18_WORKER_CLOSE_FAILED');
          }
        });
      },
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNotNull);
    owner = b;
    AuthEpoch.advance();
    auth.changed();
    await controller.reconcile();
    await controller.reconcile();
    expect(attemptedB, 0);
    expect(controller.activeDatabase, isNull);
  });

  test('concurrent close calls free a worker exactly once', () async {
    final tracker = <String>[];
    final lease = syntheticLease(b, releaseWorker: () async {
      tracker.add('release');
    });
    await Future.wait([lease.close(), lease.close()]);
    expect(tracker, ['release']);
  });

  test('sync and async factories cannot both be configured', () {
    final auth = _FakeAuth();
    addTearDown(auth.dispose);
    expect(() => PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => a,
      openDatabase: (scope) =>
          AppDatabase.testPatientVault(NativeDatabase.memory(), scope),
      openVaultLease: (scope) async => syntheticLease(scope),
    ), throwsArgumentError);
  });

  test('reentrant notifier cannot open B before releasing A worker',
      () async {
    final auth = _FakeAuth();
    var owner = a;
    final events = <String>[];
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => owner,
      openVaultLease: (scope) async {
        events.add('open:' + scope.databaseName);
        return syntheticLease(scope, releaseWorker: () async {
          events.add('close:' + scope.databaseName);
        });
      },
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNotNull);

    var reenterOnce = true;
    controller.addListener(() {
      if (reenterOnce && controller.isResolving) {
        reenterOnce = false;
        unawaited(controller.reconcile());
      }
    });
    owner = b;
    AuthEpoch.advance();
    auth.changed();
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, b.databaseName);
    expect(events, containsAllInOrder([
      'open:' + a.databaseName,
      'close:' + a.databaseName,
      'open:' + b.databaseName,
    ]));
  });


  test('unresolved stale A identity does not hold B physical open queue',
      () async {
    final auth = _FakeAuth();
    final firstResolver = Completer<PatientVaultScope?>();
    var resolved = 0;
    final opened = <String>[];
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () {
        resolved++;
        if (resolved == 1) return firstResolver.future;
        return Future.value(b);
      },
      openVaultLease: (scope) async {
        opened.add(scope.databaseName);
        return syntheticLease(scope);
      },
    );
    addTearDown(() async {
      controller.dispose();
      await controller.physicalShutdownComplete;
      auth.dispose();
    });

    // Deliberately leave the first identity request unresolved. No timeout
    // or retry is allowed to paper over a serialized resolver deadlock.
    AuthEpoch.advance();
    auth.changed();
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, b.databaseName);
    expect(opened, [b.databaseName]);

    // A's delayed answer must be ignored after B is already active.
    firstResolver.complete(a);
    await Future<void>.delayed(Duration.zero);
    expect(controller.activeScope?.databaseName, b.databaseName);
    expect(opened, [b.databaseName]);
  });

}
