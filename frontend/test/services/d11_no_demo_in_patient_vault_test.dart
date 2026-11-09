import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/offline_demo_audit_seed.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D11 demo seeding requires both audit mode and explicit audit vault',
      () {
    final audit = PatientVaultScope.auditOnly();
    final local = PatientVaultScope.deviceLocal(
      '123e4567-e89b-42d3-a456-426614174000',
    );
    final remote = PatientVaultScope.nativeDjango(42);

    expect(
      canSeedOfflineDemoAuditVault(
        auditAllowed: true, offlineDemo: true, scope: audit,
      ),
      isTrue,
    );
    for (final scope in [null, local, remote]) {
      expect(
        canSeedOfflineDemoAuditVault(
          auditAllowed: true, offlineDemo: true, scope: scope,
        ),
        isFalse,
        reason: 'Only audit-only vault may contain fabricated measurements',
      );
    }
    expect(
      canSeedOfflineDemoAuditVault(
        auditAllowed: false, offlineDemo: true, scope: audit,
      ),
      isFalse,
    );
    expect(
      canSeedOfflineDemoAuditVault(
        auditAllowed: true, offlineDemo: false, scope: audit,
      ),
      isFalse,
    );
  });

  test('D11 no demo entries or profile in any patient vault despite audit flags',
      () async {
    final scopes = [
      PatientVaultScope.deviceLocal('123e4567-e89b-42d3-a456-426614174000'),
      PatientVaultScope.nativeDjango(42),
    ];
    for (final scope in scopes) {
      final db = AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
      try {
        await seedOfflineDemoAuditData(
          db, auditAllowed: true, offlineDemo: true,
        );
        // Even a future caller bypassing the audit helper cannot overwrite
        // an actual medical vault with generated demo measurements.
        await expectLater(db.seedDemoData(), throwsStateError);
        expect(await db.countLogs(), 0, reason: scope.databaseName);
        expect(
          await db.getProfileForLocalUserId(db.activeProfileRowId),
          isNull,
          reason: scope.databaseName,
        );
      } finally {
        await db.close();
      }
    }
  });

  test('D11 direct fixture attempt preserves an existing real reading', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(84),
    );
    try {
      final id = await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.now(),
          bloodSugar: 126.0,
          clientUuid: 'd11-synthetic-existing-real-reading',
        ),
      );
      await expectLater(db.seedDemoData(), throwsStateError);
      expect(await db.countLogs(), 1);
      final original = await db.getLogById(id);
      expect(original, isNotNull);
      expect(original!.bloodSugar, 126.0);
      expect(original.syncStatus, 'pending');
    } finally {
      await db.close();
    }
  });

  test('D11 synthetic audit-only vault still supports visual demo fixtures',
      () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    try {
      await seedOfflineDemoAuditData(
        db, auditAllowed: true, offlineDemo: true,
      );
      expect(await db.countLogs(), greaterThan(0));
      final profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
      expect(profile, isNotNull);
    } finally {
      await db.close();
    }
  });
}
