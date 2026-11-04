import 'package:amina/data/drift/d18_schema_inventory.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('preflight inventories dynamic tables and rows without changing data',
      () async {
    final db = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.nativeDjango(735),
    );
    addTearDown(db.close);
    await db.customStatement(
      'CREATE TABLE "d18_dynamic" ("id" INTEGER PRIMARY KEY, "v" TEXT)',
    );
    await db.customStatement(
      "INSERT INTO d18_dynamic (id, v) VALUES (1, 'SENTINEL')",
    );
    await db.customStatement(
      'CREATE INDEX d18_dynamic_v_idx ON d18_dynamic(v)',
    );

    final first = await inspectD18VaultSchema(db);
    final second = await inspectD18VaultSchema(db);
    final dynamicTable = first.objects.singleWhere(
      (object) => object.name == 'd18_dynamic',
    );
    expect(first.vaultName, 'amina_vault_v1_native_735');
    expect(dynamicTable.type, 'table');
    expect(dynamicTable.rowCount, 1);
    expect(first.objects.any((o) => o.name == 'd18_dynamic_v_idx'), isTrue);
    expect(second.objects.length, first.objects.length);
    final row = await db.customSelect(
      'SELECT v FROM d18_dynamic WHERE id = 1',
    ).getSingle();
    expect(row.read<String>('v'), 'SENTINEL');
  });

  test('preflight rejects legacy and audit databases', () async {
    final legacy = AppDatabase(NativeDatabase.memory());
    final audit = AppDatabase.testPatientVault(
      NativeDatabase.memory(), PatientVaultScope.auditOnly(),
    );
    addTearDown(legacy.close);
    addTearDown(audit.close);
    await expectLater(
      inspectD18VaultSchema(legacy), throwsStateError,
    );
    await expectLater(
      inspectD18VaultSchema(audit), throwsStateError,
    );
  });
}
