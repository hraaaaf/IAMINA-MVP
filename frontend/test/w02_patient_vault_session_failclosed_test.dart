import 'dart:async';

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

/// W02 synthetic behavioral tests: session-generation publication boundary.
//// No browser/login API, real patient, database file or encryption certification.
void main() {
  final scopeA = PatientVaultScope.deviceLocal(
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  );
  final scopeB = PatientVaultScope.deviceLocal(
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
  );

  AppDatabase freshVault(PatientVaultScope scope) =>
      AppDatabase.testPatientVault(NativeDatabase.memory(), scope);

  test('switch A→B→A unpublishes the previous vault immediately', () async {
    final changes = ValueNotifier<int>(0);
    var current = scopeA;
    final controller = PatientVaultSessionController(
      authChanges: changes,
      resolveScope: () async => current,
      openDatabase: freshVault,
    );
    addTearDown(() {
      controller.dispose();
      changes.dispose();
    });

    await controller.reconcile();
    expect(controller.activeScope?.databaseName, scopeA.databaseName);
    expect(controller.hasVault, isTrue);

    current = scopeB;
    changes.value++;
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, scopeB.databaseName);

    current = scopeA;
    changes.value++;
    expect(controller.activeDatabase, isNull);
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, scopeA.databaseName);
  });

  test('unresolved old principal can never publish after a new epoch', () async {
    final changes = ValueNotifier<int>(0);
    final staleA = Completer<PatientVaultScope?>();
    var calls = 0;
    final controller = PatientVaultSessionController(
      authChanges: changes,
      resolveScope: () {
        calls++;
        return calls == 1 ? staleA.future : Future.value(scopeB);
      },
      openDatabase: freshVault,
    );
    addTearDown(() {
      controller.dispose();
      changes.dispose();
    });

    // The constructor started resolving A. A new auth transition supersedes it.
    changes.value++;
    await controller.reconcile();
    expect(controller.activeScope?.databaseName, scopeB.databaseName);

    staleA.complete(scopeA);
    await Future<void>.delayed(Duration.zero);
    expect(controller.activeScope?.databaseName, scopeB.databaseName);
  });

  test('null principal never exposes a fallback legacy vault', () async {
    final changes = ValueNotifier<int>(0);
    final controller = PatientVaultSessionController(
      authChanges: changes,
      resolveScope: () async => null,
      openDatabase: freshVault,
    );
    addTearDown(() {
      controller.dispose();
      changes.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNull);
    expect(controller.activeScope, isNull);
    expect(controller.hasVault, isFalse);
  });

  test('resolver exception fails closed, without a guessed patient', () async {
    final changes = ValueNotifier<int>(0);
    final controller = PatientVaultSessionController(
      authChanges: changes,
      resolveScope: () async => throw StateError('synthetic unavailable auth'),
      openDatabase: freshVault,
    );
    addTearDown(() {
      controller.dispose();
      changes.dispose();
    });
    await controller.reconcile();
    expect(controller.activeDatabase, isNull);
    expect(controller.activeScope, isNull);
  });
}
