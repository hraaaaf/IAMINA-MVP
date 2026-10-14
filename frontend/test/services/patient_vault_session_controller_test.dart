import 'dart:async';
import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/patient_treatment_declaration_store.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthTestNotifier extends ChangeNotifier {
  void changed() => notifyListeners();
}

void main() {
  test('D7 local runtime cannot publish any database without a scope', () async {
    final auth = _AuthTestNotifier();
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => null,
      openDatabase: (scope) => fail('Null owner must never open a vault'),
    );
    addTearDown(controller.dispose);
    addTearDown(auth.dispose);
    await controller.reconcile();
    expect(controller.hasVault, isFalse);
    expect(controller.activeDatabase, isNull);
    expect(controller.activeScope, isNull);
  });

  test('D7 delayed account A resolution cannot expose A after switch to B',
      () async {
    final auth = _AuthTestNotifier();
    final first = Completer<PatientVaultScope?>();
    PatientVaultScope? active = PatientVaultScope.nativeDjango(812);
    var calls = 0;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () {
        calls++;
        if (calls == 1) return first.future;
        return Future.value(active);
      },
      openDatabase: (scope) => AppDatabase.testPatientVault(
        NativeDatabase.memory(), scope,
      ),
    );
    addTearDown(controller.dispose);
    addTearDown(auth.dispose);
    expect(controller.activeDatabase, isNull);
    AuthEpoch.advance();
    auth.changed();
    await controller.reconcile();
    first.complete(PatientVaultScope.nativeDjango(734));
    await Future<void>.delayed(Duration.zero);
    expect(controller.activeScope?.databaseName, 'amina_vault_v1_native_812');
    expect(controller.activeScope?.databaseName, isNot('amina_vault_v1_native_734'));
  });

  test('D7 changing epoch retires already visible patient vault', () async {
    final auth = _AuthTestNotifier();
    final waitB = Completer<PatientVaultScope?>();
    var useB = false;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () => useB
          ? waitB.future
          : Future.value(PatientVaultScope.nativeDjango(734)),
      openDatabase: (scope) => AppDatabase.testPatientVault(
        NativeDatabase.memory(), scope,
      ),
    );
    addTearDown(controller.dispose);
    addTearDown(auth.dispose);
    await controller.reconcile();
    expect(controller.activeScope?.nativeDjangoUserId, 734);
    useB = true;
    AuthEpoch.advance();
    auth.changed();
    expect(controller.activeDatabase, isNull);
    waitB.complete(PatientVaultScope.nativeDjango(812));
    await controller.reconcile();
    expect(controller.activeScope?.nativeDjangoUserId, 812);
  });

  test('D7 on-disk A B A vaults preserve only the matching owner records', () async {
    final folder = await Directory.systemTemp.createTemp('iamina-d7-ab-a-');
    addTearDown(() => folder.delete(recursive: true));
    final auth = _AuthTestNotifier();
    addTearDown(auth.dispose);
    var selected = 734;
    final controller = PatientVaultSessionController(
      authChanges: auth,
      resolveScope: () async => PatientVaultScope.nativeDjango(selected),
      openDatabase: (scope) => AppDatabase.testPatientVault(
        NativeDatabase(File('${folder.path}/${scope.databaseName}.sqlite')),
        scope,
      ),
    );
    addTearDown(controller.dispose);
    await controller.reconcile();
    final dbA = controller.activeDatabase!;
    await dbA.into(dbA.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type1'),
      ),
    );

    final storeA = PatientTreatmentDeclarationStore(dbA);
    await storeA.write(
      state: 'declared', codes: ['oral_meds', 'lifestyle'],
    );
    expect((await storeA.read())?.syncStatus, 'pending');

    selected = 812;
    AuthEpoch.advance();
    auth.changed();
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    final dbB = controller.activeDatabase!;
    expect(await dbB.select(dbB.patientProfiles).get(), isEmpty);
    final storeB = PatientTreatmentDeclarationStore(dbB);
    expect(await storeB.read(), isNull);
    await dbB.into(dbB.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(812),
        updatedAt: DateTime.utc(2026, 10, 13),
        diabetesType: const drift.Value('type2'),
      ),
    );

    await storeB.write(state: 'declared', codes: ['insulin']);
    expect((await storeB.read())?.codes, ['insulin']);

    selected = 734;
    AuthEpoch.advance();
    auth.changed();
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    final again = controller.activeDatabase!;
    final rows = await again.select(again.patientProfiles).get();
    expect(rows, hasLength(1));
    expect(rows.single.userId, 734);
    expect(rows.single.diabetesType, 'type1');
    final recoveredA = (await PatientTreatmentDeclarationStore(again).read())!;
    expect(recoveredA.codes, ['oral_meds', 'lifestyle']);
    expect(recoveredA.syncStatus, 'pending');
    expect(recoveredA.localGeneration, 1);
    // A never inherited B's insulin declaration when switching back.
    expect(recoveredA.codes, isNot(contains('insulin')));
  });

}
