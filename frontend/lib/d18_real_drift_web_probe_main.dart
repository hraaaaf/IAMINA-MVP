// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
// D18 CI-only synthetic Web persistence probe through the real Drift factory.
// Not a clinical data migration, at-rest encryption test or patient account.
import 'dart:html' as html;

import 'package:flutter/widgets.dart';

import 'data/drift/d18_schema_inventory.dart';
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';

const _a = '7e0bb410-2c7f-4d3e-9b61-36f092c76210';
const _b = '7e0bb410-2c7f-4d3e-9b61-36f092c76211';
const _table = 'd18_browser_persistence_probe';
const _legacyTable = 'd18_synthetic_legacy_hold';
const _legacySentinel = 'D18_LEGACY_STAYS_UNASSIGNED_20261101';
const _sentinel = 'D18_SYNTHETIC_A_ONLY_20261101';

void _check(bool ok, String reason) {
  if (!ok) throw StateError(reason);
}

void _stage(String value) {
  html.document.documentElement?.dataset['d18Stage'] = value;
}

// Seed historical unscoped storage BEFORE creating the patient A vault.
// This is a disposable synthetic Chromium browser profile only.
Future<void> _seedLegacy() async {
  _stage('legacy_seed_open');
  final legacy = AppDatabase.defaults();
  try {
    await legacy.customStatement(
      'CREATE TABLE "$_legacyTable" (id INTEGER PRIMARY KEY, sentinel TEXT NOT NULL)',
    );
    await legacy.customStatement(
      'INSERT INTO "$_legacyTable" (id, sentinel) VALUES (?, ?)',
      [1, _legacySentinel],
    );
  } finally {
    await legacy.close();
  }
}

Future<void> _seedA() async {
  _stage('seed_constructor');
  final db = AppDatabase.forPatientVault(PatientVaultScope.deviceLocal(_a));
  try {
    _stage('seed_create_table');
    await db.customStatement(
      'CREATE TABLE "$_table" (id INTEGER PRIMARY KEY, sentinel TEXT NOT NULL)',
    );
    _stage('seed_create_index');
    await db.customStatement(
      'CREATE INDEX d18_browser_probe_sentinel_idx ON "$_table"(sentinel)',
    );
    _stage('seed_insert');
    await db.customStatement(
      'INSERT INTO "$_table" (id, sentinel) VALUES (?, ?)',
      [1, _sentinel],
    );
    _stage('inspect_schema');
    final inventory = await inspectD18VaultSchema(db);
    _check(inventory.vaultName.endsWith(_a.replaceAll('-', '')),
        'Unexpected vault A namespace');
    _check(inventory.objects.singleWhere((o) => o.name == _table).rowCount == 1,
        'Missing synthetic A data in sqlite_master inventory');
    _check(inventory.objects.any((o) => o.name == 'd18_browser_probe_sentinel_idx'),
        'Missing dynamically declared index');
  } finally {
    _stage('closing');
    await db.close();
  }
}

Future<void> _verifyA() async {
  final db = AppDatabase.forPatientVault(PatientVaultScope.deviceLocal(_a));
  try {
    final row = await db.customSelect(
      'SELECT sentinel FROM "$_table" WHERE id = 1',
    ).getSingle();
    _check(row.read<String>('sentinel') == _sentinel,
        'Synthetic A record did not survive independent browser restart');
    final inventory = await inspectD18VaultSchema(db);
    _check(inventory.objects.singleWhere((o) => o.name == _table).rowCount == 1,
        'Dynamic A table lost after Chromium restart');
    _check(inventory.objects.every((o) => o.name != _legacyTable),
        'Historical unscoped data leaked into A vault');
  } finally {
    await db.close();
  }
}

Future<void> _verifyB() async {
  final db = AppDatabase.forPatientVault(PatientVaultScope.deviceLocal(_b));
  try {
    final inventory = await inspectD18VaultSchema(db);
    _check(inventory.objects.every((o) => o.name != _table),
        'Patient B sees synthetic patient A table');
    _check(inventory.objects.every((o) => o.name != _legacyTable),
        'Patient B sees unscoped historical table');
  } finally {
    await db.close();
  }
}

Future<void> _verifyLegacy() async {
  // Opening the legacy database must NOT reassign its contents to A or B.
  final legacy = AppDatabase.defaults();
  try {
    final historical = await legacy.customSelect(
      'SELECT sentinel FROM "$_legacyTable" WHERE id = 1',
    ).getSingle();
    _check(historical.read<String>('sentinel') == _legacySentinel,
        'Original historical data was modified, dropped or migrated');
    final rows = await legacy.customSelect(
      "SELECT COUNT(*) AS n FROM sqlite_master WHERE name = '$_table'",
    ).getSingle();
    _check(rows.read<int>('n') == 0,
        'Historical unscoped database unexpectedly contains A probe');
  } finally {
    await legacy.close();
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const marker = 'D18_DRIFT';
  final phase = Uri.base.queryParameters['phase'] ?? '';
  html.document.title = '${marker}_PENDING';
  _stage('entered_main');
  try {
    switch (phase) {
      case 'seed_legacy':
        await _seedLegacy();
        break;
      case 'seed_a':
        await _seedA();
        break;
      case 'verify_a':
        await _verifyA();
        break;
      case 'verify_b':
        await _verifyB();
        break;
      case 'verify_legacy':
        await _verifyLegacy();
        break;
      default:
        throw StateError('Unknown D18 synthetic phase');
    }
    _stage('passed');
    html.document.title = '${marker}_PASS:$phase';
  } catch (error, stack) {
    _stage('exception');
    html.document.documentElement?.dataset['d18Error'] =
        error.toString().substring(0, error.toString().length.clamp(0, 450));
    html.document.title = '${marker}_FAIL:$phase';
    debugPrint('D18_REAL_DRIFT_SMOKE_ERROR $phase $error');
    debugPrintStack(stackTrace: stack);
  }
}
