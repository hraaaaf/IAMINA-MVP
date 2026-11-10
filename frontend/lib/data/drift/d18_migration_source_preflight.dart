import 'database.dart';
import 'd18_schema_inventory.dart';
import 'patient_vault_scope.dart';

/// Read-only SOURCE qualification. Not export, encryption or migration.
final class D18MigrationSourcePreflight {
  final D18SchemaInventory inventory;
  final int tableCount;
  final int rowCount;

  const D18MigrationSourcePreflight._(
    this.inventory, this.tableCount, this.rowCount,
  );
}

/// Fail-closed: independently authenticate patient BEFORE choosing scope.
/// No clinical values, row ids or query results must be logged from this gate.
Future<D18MigrationSourcePreflight> inspectD18MigrationSource(
  AppDatabase db, {
  required PatientVaultScope expectedScope,
}) async {
  final actual = db.patientVaultScope;
  if (actual == null ||
      actual.databaseName != expectedScope.databaseName ||
      actual.databaseName == PatientVaultScope.auditOnly().databaseName) {
    throw StateError('D18 source requires exact patient scope');
  }
  return db.transaction(() async {
    // SQLite integrity_check does NOT include foreign key checks.
    final integrity = await db.customSelect('PRAGMA integrity_check').get();
    if (integrity.length != 1 ||
        integrity.single.data.values.single != 'ok') {
      throw StateError('D18 source integrity check failed');
    }
    final violations = await db.customSelect('PRAGMA foreign_key_check').get();
    if (violations.isNotEmpty) {
      throw StateError('D18 source foreign-key check failed');
    }
    final inventory = await inspectD18VaultSchema(db);
    final tables = inventory.objects.where((o) => o.type == 'table').toList();
    if (tables.isEmpty) {
      throw StateError('D18 source has no inventoried tables');
    }
    var rows = 0;
    for (final table in tables) {
      if (table.rowCount == null || table.rowCount! < 0) {
        throw StateError('D18 source table row count invalid');
      }
      rows += table.rowCount!;
    }
    return D18MigrationSourcePreflight._(inventory, tables.length, rows);
  });
}
