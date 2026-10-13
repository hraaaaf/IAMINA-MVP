import 'dart:async';
import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_vault_session_coordinator.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthSignal extends ChangeNotifier {
  void changeOwner() => notifyListeners();
}

void main() {
  test('D7 separate on-disk vaults survive A -> B -> A without exposure', () async {
    final dir = await Directory.systemTemp.createTemp('iamina-d7-vault-');
    addTearDown(() => dir.delete(recursive: true));
    final changes = _AuthSignal();
    addTearDown(changes.dispose);
    var activeId = 734;
    final controller = PatientVaultSessionCoordinator(
      authChanges: changes,
      resolve: () async => PatientVaultScope.nativeDjango(activeId),
      open: (scope) async => AppDatabase.testPatientVault(
        NativeDatabase(File('${dir.path}/${scope.databaseName}.sqlite')),
        scope,
      ),
    );
    addTearDown(controller.dispose);
    await controller.initialize();

    final a = controller.activeDatabase!;
    await a.into(a.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type1'),
      ),
    );
    activeId = 812;
    changes.changeOwner();
    expect(controller.activeDatabase, isNull); // immediate redaction
    await pumpEventQueue();
    final b = controller.activeDatabase!;
    expect(b.patientVaultScope!.nativeDjangoUserId, 812);
    expect(await b.select(b.patientProfiles).get(), isEmpty);
    await b.into(b.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(812),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type2'),
      ),
    );
    activeId = 734;
    changes.changeOwner();
    expect(controller.activeDatabase, isNull);
    await pumpEventQueue();
    final aAgain = controller.activeDatabase!;
    expect((await aAgain.select(aAgain.patientProfiles).getSingle()).userId, 734);
    expect((await aAgain.select(aAgain.patientProfiles).getSingle()).diabetesType,
        'type1');
  });

  test('D7 unresolved owner has no access and never falls back to legacy', () async {
    final changes = _AuthSignal();
    addTearDown(changes.dispose);
    final controller = PatientVaultSessionCoordinator(
      authChanges: changes,
      resolve: () async => null,
      open: (_) => throw StateError('Must not open a vault'),
    );
    addTearDown(controller.dispose);
    await controller.initialize();
    expect(controller.isReady, isTrue);
    expect(controller.hasVault, isFalse);
    expect(controller.activeDatabase, isNull);
  });

  test('D7 stale async identity resolution cannot expose the prior owner', () async {
    final changes = _AuthSignal();
    addTearDown(changes.dispose);
    final first = Completer<PatientVaultScope?>();
    var count = 0;
    final controller = PatientVaultSessionCoordinator(
      authChanges: changes,
      resolve: () {
        count++;
        if (count == 1) return first.future;
        return Future.value(PatientVaultScope.nativeDjango(812));
      },
      open: (scope) async => AppDatabase.testPatientVault(
        NativeDatabase.memory(), scope,
      ),
    );
    addTearDown(controller.dispose);
    final pending = controller.initialize();
    changes.changeOwner();
    expect(controller.activeDatabase, isNull);
    first.complete(PatientVaultScope.nativeDjango(734));
    await pending;
    await pumpEventQueue();
    expect(controller.activeDatabase?.patientVaultScope?.nativeDjangoUserId, 812);
  });
}
