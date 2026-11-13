import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/data/drift/revocable_patient_query_guard.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

class _AuthAndLockSignals extends ChangeNotifier {
  void changed() => notifyListeners();
}

void main() {
  test('D1 retained Drift reference denies SELECT and mutation after lock',
      () async {
    final changes = _AuthAndLockSignals();
    addTearDown(changes.dispose);
    var unlocked = true;
    final guard = RevocablePatientQueryGuard(
      authorized: () => unlocked,
      revocationSignals: changes,
    );
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory().interceptWith(guard),
      PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);

    final initial = await db.customSelect('SELECT 1 AS alive').getSingle();
    expect(initial.read<int>('alive'), 1);
    await db.into(db.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const drift.Value(734),
        updatedAt: DateTime.utc(2026, 11, 13),
        diabetesType: const drift.Value('type2'),
      ),
    );
    expect(await db.select(db.patientProfiles).get(), hasLength(1));

    // App Lock changes before asynchronous provider disposal. The old widget
    // can still have a DB reference; it must have no SQL read/write ability.
    unlocked = false;
    changes.changed();
    expect(guard.isRevoked, isTrue);
    await expectLater(
      db.customSelect('SELECT * FROM patient_profiles').get(),
      throwsA(anything),
    );
    await expectLater(
      db.customStatement('DELETE FROM patient_profiles'),
      throwsA(anything),
    );
    await expectLater(
      db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(812),
          updatedAt: DateTime.utc(2026, 11, 13),
        ),
      ),
      throwsA(anything),
    );

    // A new unlock must NOT rehabilitate the old executor.
    unlocked = true;
    await expectLater(
      db.customSelect('SELECT 1').get(),
      throwsA(anything),
    );
  });

  test('D1 querying after close never reopens retired patient executor',
      () async {
    final changes = _AuthAndLockSignals();
    addTearDown(changes.dispose);
    final guard = RevocablePatientQueryGuard(
      authorized: () => true,
      revocationSignals: changes,
    );
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory().interceptWith(guard),
      PatientVaultScope.nativeDjango(734),
    );
    await db.customSelect('SELECT 1').getSingle();
    await db.close();
    expect(guard.isRevoked, isTrue);
    // NativeDatabase.memory can reconnect after close when unguarded. The
    // interceptor's sticky retirement must reject even that reconnection.
    await expectLater(
      db.customSelect('SELECT 1').getSingle(),
      throwsA(anything),
    );
  });

  test('D1 admission predicate denies SQL without waiting for notifications',
      () async {
    final changes = _AuthAndLockSignals();
    addTearDown(changes.dispose);
    var authorized = false;
    final guard = RevocablePatientQueryGuard(
      authorized: () => authorized,
      revocationSignals: changes,
    );
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory().interceptWith(guard),
      PatientVaultScope.nativeDjango(734),
    );
    addTearDown(db.close);
    await expectLater(
      db.customSelect('SELECT 1').getSingle(),
      throwsA(anything),
    );
    authorized = true;
    // The authorization predicate alone isn't a one-shot grant. The fresh
    // controller must still require explicit recovery and auth epoch checks.
    changes.changed();
    expect(guard.isRevoked, isTrue);
    await expectLater(db.customSelect('SELECT 1').getSingle(), throwsA(anything));
  });
}
