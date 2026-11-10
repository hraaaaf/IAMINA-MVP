import 'database.dart';
import 'patient_vault_scope.dart';

/// Read-only schema inventory for D18 migration preflight.
/// This is NOT an export, migration, encryption or cutover implementation.
final class D18SchemaInventory {
  final String vaultName;
  final int schemaVersion;
  final List<D18SchemaObject> objects;

  const D18SchemaInventory({
    required this.vaultName,
    required this.schemaVersion,
    required this.objects,
  });
}

final class D18SchemaObject {
  final String type;
  final String name;
  final String tableName;
  final String? sql;
  final int? rowCount;

  const D18SchemaObject({
    required this.type,
    required this.name,
    required this.tableName,
    required this.sql,
    required this.rowCount,
  });
}

/// Inventory every user-defined SQLite schema object, including D18 dynamic
/// tables not represented in Drift's generated schema.
///
/// No data values are exported. Refuses unscoped legacy and audit databases.
/// Caller must independently verify the authenticated principal; a scope name
/// is NOT proof of authorization.
Future<D18SchemaInventory> inspectD18VaultSchema(AppDatabase db) async {
  final scope = db.patientVaultScope;
  if (scope == null ||
      scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
    throw StateError('D18 inventory requires a scoped patient vault');
  }

  return db.transaction(() async {
    final rows = await db.customSelect(
      "SELECT type, name, tbl_name, sql FROM sqlite_master "
      "WHERE name NOT LIKE 'sqlite_%' "
      "AND type IN ('table', 'index', 'view', 'trigger') "
      "ORDER BY type, name",
    ).get();

    final objects = <D18SchemaObject>[];
    for (final row in rows) {
      final data = row.data;
      final type = data['type']! as String;
      final name = data['name']! as String;
      int? count;
      if (type == 'table') {
        // SQLite identifiers must be double-quoted; never interpolate an
        // unescaped sqlite_master name into a SQL statement.
        final quoted = '"${name.replaceAll('"', '""')}"';
        final result = await db.customSelect(
          'SELECT COUNT(*) AS n FROM $quoted',
        ).getSingle();
        count = result.read<int>('n');
      }
      objects.add(D18SchemaObject(
        type: type,
        name: name,
        tableName: data['tbl_name']! as String,
        sql: data['sql'] as String?,
        rowCount: count,
      ));
    }

    final version = await db.customSelect('PRAGMA user_version').getSingle();
    return D18SchemaInventory(
      vaultName: scope.databaseName,
      schemaVersion: version.read<int>('user_version'),
      objects: List.unmodifiable(objects),
    );
  });
}
