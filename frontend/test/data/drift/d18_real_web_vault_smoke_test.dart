import 'package:amina/data/drift/d18_schema_inventory.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

/// Integration smoke for the REAL drift_flutter web factory and worker.
///
/// Run on Chrome with the app's sqlite3.wasm and drift_worker.js served at
/// the root. A browser test runner that does not serve those assets must fail,
/// not silently fall back to NativeDatabase or claim persistence.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('real Drift Web vault A/B persistence and legacy quarantine', () async {
    expect(kIsWeb, isTrue, reason: 'Browser only; native is not evidence');
    final suffix = DateTime.now().microsecondsSinceEpoch;
    final a = PatientVaultScope.deviceLocal(
      'aaaaaaaa-aaaa-4aaa-8aaa-${suffix.toRadixString(16).padLeft(12, '0').substring(0, 12)}',
    );
    final b = PatientVaultScope.nativeDjango(900000001);
    final dbA = AppDatabase.forPatientVault(a);
    try {
      await dbA.customStatement(
        'CREATE TABLE IF NOT EXISTS d18_browser_probe '
        '(id INTEGER PRIMARY KEY, sentinel TEXT NOT NULL)',
      );
      await dbA.customStatement(
        "INSERT INTO d18_browser_probe (id, sentinel) VALUES (1, 'A_ONLY')",
      );
      final inventory = await inspectD18VaultSchema(dbA);
      expect(inventory.objects.singleWhere(
        (o) => o.name == 'd18_browser_probe',
      ).rowCount, 1);
    } finally {
      await dbA.close();
    }

    final reopened = AppDatabase.forPatientVault(a);
    try {
      final row = await reopened.customSelect(
        'SELECT sentinel FROM d18_browser_probe WHERE id = 1',
      ).getSingle();
      expect(row.read<String>('sentinel'), 'A_ONLY');
    } finally {
      await reopened.close();
    }

    final dbB = AppDatabase.forPatientVault(b);
    try {
      final objects = await inspectD18VaultSchema(dbB);
      expect(objects.objects.any((o) => o.name == 'd18_browser_probe'), isFalse);
    } finally {
      await dbB.close();
    }
  });
}
