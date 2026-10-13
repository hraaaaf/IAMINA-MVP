import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/auth_epoch.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 local runtime cannot publish any database without a scope', () async {
    final auth = ChangeNotifier();
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
    final auth = ChangeNotifier();
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
    auth.notifyListeners();
    await controller.reconcile();
    first.complete(PatientVaultScope.nativeDjango(734));
    await Future<void>.delayed(Duration.zero);
    expect(controller.activeScope?.databaseName, 'amina_vault_v1_native_812');
    expect(controller.activeScope?.databaseName, isNot('amina_vault_v1_native_734'));
  });

  test('D7 changing epoch retires already visible patient vault', () async {
    final auth = ChangeNotifier();
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
    auth.notifyListeners();
    expect(controller.activeDatabase, isNull);
    waitB.complete(PatientVaultScope.nativeDjango(812));
    await controller.reconcile();
    expect(controller.activeScope?.nativeDjangoUserId, 812);
  });
}
