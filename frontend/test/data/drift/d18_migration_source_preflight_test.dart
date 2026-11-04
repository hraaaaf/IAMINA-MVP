import 'package:amina/data/drift/d18_migration_source_preflight.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('source preflight is read-only and inventories dynamic tables, triggers',
      () async {
    final scope = PatientVaultScope.nativeDjango(735);
    final db = AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
    addTearDown(db.close);
    await db.customStatement(
      'CREATE TABLE d18_dynamic (id INTEGER PRIMARY KEY, v TEXT)');
    await db.customStatement(
      "INSERT INTO d18_dynamic (id, v) VALUES (1, 'SENTINEL')");
    await db.customStatement(
      'CREATE INDEX d18_dynamic_v_idx ON d18_dynamic(v)');
    await db.customStatement('''
      CREATE TRIGGER d18_no_delete BEFORE DELETE ON d18_dynamic
      BEGIN SELECT RAISE(ABORT, 'no delete'); END
    ''');
    final a = await inspectD18MigrationSource(db, expectedScope: scope);
    final b = await inspectD18MigrationSource(db, expectedScope: scope);
    expect(a.tableCount, greaterThan(0));
    expect(a.rowCount, greaterThanOrEqualTo(1));
    expect(b.rowCount, a.rowCount);
    expect(a.inventory.objects.any((o) => o.name == 'd18_dynamic'), isTrue);
    expect(a.inventory.objects.any((o) => o.name == 'd18_dynamic_v_idx'), isTrue);
    expect(a.inventory.objects.any((o) => o.name == 'd18_no_delete'), isTrue);
    final record = await db.customSelect(
      'SELECT v FROM d18_dynamic WHERE id=1').getSingle();
    expect(record.read<String>('v'), 'SENTINEL');
  });

  test('legacy, audit and foreign patient scopes are rejected', () async {
    final a = PatientVaultScope.nativeDjango(735);
    final db = AppDatabase.testPatientVault(NativeDatabase.memory(), a);
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly());
    addTearDown(db.close);
    addTearDown(legacy.close);
    addTearDown(audit.close);
    await expectLater(inspectD18MigrationSource(db,
      expectedScope: PatientVaultScope.nativeDjango(736)), throwsStateError);
    await expectLater(inspectD18MigrationSource(legacy,
      expectedScope: a), throwsStateError);
    await expectLater(inspectD18MigrationSource(audit,
      expectedScope: PatientVaultScope.auditOnly()), throwsStateError);
  });

  test('orphan FK rejects migration without deleting original row', () async {
    final scope = PatientVaultScope.nativeDjango(737);
    final db = AppDatabase.testPatientVault(NativeDatabase.memory(), scope);
    addTearDown(db.close);
    await db.customStatement('PRAGMA foreign_keys=OFF');
    await db.customStatement('CREATE TABLE d18_parent (id INTEGER PRIMARY KEY)');
    await db.customStatement('''
      CREATE TABLE d18_child (
        id INTEGER PRIMARY KEY,
        parent_id INTEGER NOT NULL REFERENCES d18_parent(id))
    ''');
    await db.customStatement(
      'INSERT INTO d18_child (id, parent_id) VALUES (1, 999)');
    expect(await db.customSelect('PRAGMA foreign_key_check').get(), isNotEmpty,
      reason:'Test must contain real orphan row');
    await expectLater(inspectD18MigrationSource(db, expectedScope: scope),
        throwsStateError);
    final row = await db.customSelect(
      'SELECT parent_id FROM d18_child WHERE id=1').getSingle();
    expect(row.read<int>('parent_id'), 999);
  });
}
