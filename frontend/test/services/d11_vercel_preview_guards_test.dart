import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/offline_demo_audit_seed.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('D11: synthetic flags cannot mutate authenticated patient vault', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(734));
    addTearDown(db.close);
    await db.into(db.logEntries).insert(LogEntriesCompanion.insert(
      createdAt: DateTime.utc(2026, 10, 19),
      bloodSugar: 128,
      clientUuid: 'w02-d11-sentinel-patient-a'));
    await seedOfflineDemoAuditData(db, auditAllowed: true, offlineDemo: true);
    final rows = await db.select(db.logEntries).get();
    expect(rows, hasLength(1));
    expect(rows.single.clientUuid, 'w02-d11-sentinel-patient-a');
    await expectLater(db.seedDemoData(), throwsStateError);
    expect(await db.countLogs(), 1);
  });

  test('D11: legacy and local vaults cannot seed', () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    addTearDown(legacy.close);
    await seedOfflineDemoAuditData(legacy, auditAllowed: true, offlineDemo: true);
    await expectLater(legacy.seedDemoData(), throwsStateError);
    expect(await legacy.countLogs(), 0);

    final local = AppDatabase.testPatientVault(
      NativeDatabase.memory(),
      PatientVaultScope.deviceLocal('12345678-1234-4567-8123-123456789abc'));
    addTearDown(local.close);
    await seedOfflineDemoAuditData(local, auditAllowed: true, offlineDemo: true);
    await expectLater(local.seedDemoData(), throwsStateError);
    expect(await local.countLogs(), 0);
  });

  test('D11: audit vault can seed only when both flags allow it', () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly());
    addTearDown(db.close);
    await seedOfflineDemoAuditData(db, auditAllowed: false, offlineDemo: true);
    expect(await db.countLogs(), 0);
    await seedOfflineDemoAuditData(db, auditAllowed: true, offlineDemo: false);
    expect(await db.countLogs(), 0);
    await seedOfflineDemoAuditData(db, auditAllowed: true, offlineDemo: true);
    expect(await db.countLogs(), greaterThan(0));
  });
}
