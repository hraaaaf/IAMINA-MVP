// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
// D18 CI-only synthetic Web persistence probe through the real Drift factory.
// Not a clinical data migration, at-rest encryption test or patient account.
import 'dart:html' as html;
import 'dart:convert';

import 'package:cryptography/cryptography.dart';

import 'package:flutter/widgets.dart';
import 'package:drift/wasm.dart';

import 'data/drift/d18_schema_inventory.dart';
import 'data/drift/d18_migration_source_preflight.dart';
import 'data/drift/d18_vault_key_policy.dart';
import 'data/drift/database.dart';
import 'data/drift/patient_vault_scope.dart';

const _a = '7e0bb410-2c7f-4d3e-9b61-36f092c76210';
const _b = '7e0bb410-2c7f-4d3e-9b61-36f092c76211';
const _table = 'd18_browser_persistence_probe';
const _legacyTable = 'd18_synthetic_legacy_hold';
const _legacySentinel = 'D18_LEGACY_STAYS_UNASSIGNED_20261101';
const _snapshotCopy = 'd18_synthetic_sqlite_snapshot_20261102';
const _cipherKey = 'd18_ci_synthetic_sqlite_ciphertext_only_20261102';
const _passphrase = 'D18-CI-SYNTHETIC-ONLY-BROWSER-PASSPHRASE-2026';
const _aad = 'IAMINA-D18-CI-SYNTHETIC-SQLITE-V1';

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

/// Read the selected storage implementation through Drift's own Web opener.
/// This is a disposable Chromium profile, NOT a production vault migration.
Future<void> _probeBackend() async {
  _stage('probe_backend_open');
  final scope = PatientVaultScope.deviceLocal(_a);
  // Explicitly DISABLE implicit IndexedDB→OPFS relocation in this audit.
  final opened = await WasmDatabase.open(
    databaseName: scope.databaseName,
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs: false,
  );
  final chosen = opened.chosenImplementation.name;
  html.document.documentElement?.dataset['d18Backend'] = chosen;
  _check(const {'sharedIndexedDb', 'opfsShared', 'opfsLocks'}.contains(chosen),
      'Unsafe/ephemeral Drift Web backend: $chosen');
  // Verify this is THE SAME physical synthetic A vault as driftDatabase().
  // An empty probe-only database would fail on the sentinel assertion.
  final db = AppDatabase.testPatientVault(opened.resolvedExecutor, scope);
  try {
    _stage('probe_backend_read_sentinel');
    final row = await db.customSelect(
      'SELECT sentinel FROM "$_table" WHERE id = 1',
    ).getSingle();
    _check(row.read<String>('sentinel') == _sentinel,
        'Probed Drift storage does not contain persisted A sentinel');
    _stage('probe_source_integrity');
    final preflight = await inspectD18MigrationSource(db, expectedScope: scope);
    _check(preflight.tableCount >= 1 && preflight.rowCount >= 1,
        'Source preflight rejected persisted A vault');
  } finally {
    await db.close();
  }
}

/// Demonstrate a WHOLE SQLite byte export of the *current sharedIndexedDb*
/// vault using the pinned Drift 2.31 API. CI-only with synthetic content.
/// Copy is deliberately plaintext and NEVER used as a clinical backup.
Future<void> _probeSnapshotCopy() async {
  final scope = PatientVaultScope.deviceLocal(_a);
  _stage('source_manifest');
  final original = AppDatabase.forPatientVault(scope);
  late final D18MigrationSourcePreflight source;
  try {
    source = await inspectD18MigrationSource(original, expectedScope: scope);
  } finally {
    await original.close();
  }

  _stage('export_original_sqlite_binary');
  final probe = await WasmDatabase.probe(
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    databaseName: scope.databaseName,
  );
  final matching = probe.existingDatabases.where((entry) =>
      entry.$1 == WebStorageApi.indexedDb && entry.$2 == scope.databaseName)
      .toList();
  _check(matching.length == 1, 'Exactly one IndexedDB A source must exist');
  final bytes = await probe.exportDatabase(matching.single);
  _check(bytes != null && bytes.length >= 100 &&
      String.fromCharCodes(bytes.take(15)) == 'SQLite format 3' &&
      bytes[15] == 0, 'Drift export did not produce a complete SQLite file');

  _stage('import_distinct_disposable_sqlite');
  // Strictly a disposable synthetic copy in a new namespace. It is NOT
  // encrypted and MUST NEVER be used for clinical data or product cutover.
  final clone = await WasmDatabase.open(
    databaseName: _snapshotCopy,
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs: false,
    initializeDatabase: () => bytes,
  );
  final copy = AppDatabase(clone.resolvedExecutor);
  try {
    _stage('compare_all_schema_objects_and_counts');
    final rows = await copy.customSelect(
      "SELECT type, name, tbl_name, sql FROM sqlite_master "
      "WHERE name NOT LIKE 'sqlite_%' "
      "AND type IN ('table','index','view','trigger') ORDER BY type, name",
    ).get();
    _check(rows.length == source.inventory.objects.length,
        'Whole-copy schema object count mismatch');
    for (var i = 0; i < rows.length; i++) {
      final actual = rows[i].data;
      final expected = source.inventory.objects[i];
      _check(actual['type'] == expected.type &&
          actual['name'] == expected.name &&
          actual['tbl_name'] == expected.tableName &&
          actual['sql'] == expected.sql, 'Whole-copy SQL/schema mismatch');
      if (expected.type == 'table') {
        final tableName = expected.name.replaceAll('"', '""');
        final row = await copy.customSelect(
          'SELECT COUNT(*) AS n FROM "$tableName"',
        ).getSingle();
        _check(row.read<int>('n') == expected.rowCount,
            'Whole-copy table count mismatch');
      }
    }
    final schemaVersion = await copy.customSelect('PRAGMA user_version').getSingle();
    _check(schemaVersion.read<int>('user_version') == source.inventory.schemaVersion,
        'Whole-copy user_version mismatch');
    final integrity = await copy.customSelect('PRAGMA integrity_check').get();
    _check(integrity.length == 1 && integrity.single.data.values.single == 'ok',
        'Whole-copy integrity check failed');
    final badKeys = await copy.customSelect('PRAGMA foreign_key_check').get();
    _check(badKeys.isEmpty, 'Whole-copy foreign key check failed');
    final sentinel = await copy.customSelect(
      'SELECT sentinel FROM "$_table" WHERE id = 1',
    ).getSingle();
    _check(sentinel.read<String>('sentinel') == _sentinel,
        'Whole-copy dynamic clinical-like row lost');
  } finally {
    await copy.close();
  }
}

/// Reopen the synthetic copy in yet ANOTHER Chromium process to prove durable
/// storage, then independently check the original A and unscoped legacy.
Future<void> _verifySnapshotCopy() async {
  _stage('reopen_disposable_copy');
  final opened = await WasmDatabase.open(
    databaseName: _snapshotCopy,
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    moveExistingIndexedDbToOpfs: false,
  );
  final db = AppDatabase(opened.resolvedExecutor);
  try {
    final row = await db.customSelect(
      'SELECT sentinel FROM "$_table" WHERE id=1',
    ).getSingle();
    _check(row.read<String>('sentinel') == _sentinel,
        'Synthetic complete SQLite copy lost on Chromium restart');
  } finally {
    await db.close();
  }
  _stage('verify_original_unmodified');
  await _verifyA();
  await _verifyLegacy();
}


/// Encrypt the complete original IndexedDB SQLite bytes using Option A's DEK.
/// The only persisted artifact is synthetic AES-GCM ciphertext + public
/// wrappers. This is NOT an integrated encrypted Drift backend.
Future<void> _encryptSnapshot() async {
  _stage('snapshot_export_for_encryption');
  final scope = PatientVaultScope.deviceLocal(_a);
  final probe = await WasmDatabase.probe(
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    databaseName: scope.databaseName,
  );
  final matches = probe.existingDatabases.where((entry) =>
    entry.$1 == WebStorageApi.indexedDb && entry.$2 == scope.databaseName)
    .toList();
  _check(matches.length == 1, 'Missing distinct IndexedDB source');
  final bytes = await probe.exportDatabase(matches.single);
  _check(bytes != null && bytes.length >= 100, 'No complete SQLite bytes');

  _stage('enrol_random_dek');
  final enrollment = await D18VaultKeyPolicy.createForEmptyVault(
    scope: scope, passphrase: _passphrase,
  );
  try {
    _stage('aes_gcm_encrypt_sqlite_bytes');
    final cipher = await AesGcm.with256bits().encrypt(
      bytes!,
      secretKey: enrollment.session.requireUnlockedKey(),
      aad: utf8.encode('$_aad|${scope.databaseName}'),
    );
    final publicRecord = jsonEncode({
      'format': 'iamina-d18-ci-synthetic-encrypted-snapshot-v1',
      'envelope': enrollment.publicEnvelopeJson,
      'cipher': base64Encode(cipher.concatenation()),
    });
    _check(!publicRecord.contains(_sentinel) &&
      !publicRecord.contains('SQLite format 3') &&
      !publicRecord.contains(_passphrase) &&
      !publicRecord.contains(enrollment.offlineRecoveryCode),
      'Synthetic encrypted snapshot leaked plaintext or secrets');
    // Strictly ephemeral disposable browser-profile fixture, never real PHI.
    html.window.localStorage[_cipherKey] = publicRecord;
    // Hand the RANDOM synthetic offline code to the NODE test runner only.
    // This transient DOM property is not local/session storage or telemetry.
    html.document.documentElement?.dataset['d18RecoveryCode'] =
      enrollment.offlineRecoveryCode;
  } finally {
    enrollment.session.lock();
  }
}

bool _sameBytes(List<int> a, List<int> b) {
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

/// In an independent Chromium PROCESS, recover using the original passphrase
/// and the separately-held offline code; wrong key or tag tampering must fail.
/// Never writes a decrypted SQLite copy to browser persistence.
Future<void> _verifyEncryptedSnapshot() async {
  _stage('encrypted_snapshot_read');
  final scope = PatientVaultScope.deviceLocal(_a);
  final raw = html.window.localStorage[_cipherKey];
  _check(raw != null && raw.isNotEmpty, 'Ciphertext not persisted on restart');
  _check(!raw!.contains(_sentinel) && !raw.contains('SQLite format 3'),
    'Stored synthetic ciphertext contains plaintext');
  final parsed = jsonDecode(raw);
  _check(parsed is Map<String, dynamic> &&
    parsed.length == 3 &&
    parsed['format'] == 'iamina-d18-ci-synthetic-encrypted-snapshot-v1' &&
    parsed['envelope'] is String && parsed['cipher'] is String,
    'Malformed synthetic encrypted snapshot');
  final envelope = parsed['envelope'] as String;
  final sealed = base64Decode(parsed['cipher'] as String);
  final box = SecretBox.fromConcatenation(
    sealed, nonceLength: 12, macLength: 16,
  );
  final aad = utf8.encode('$_aad|${scope.databaseName}');

  _stage('wrong_passphrase_must_fail');
  var denied = false;
  try {
    final wrong = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: scope, publicEnvelopeJson: envelope,
      passphrase: 'D18-SYNTHETIC-DELIBERATELY-WRONG-PASSPHRASE',
    );
    wrong.lock();
  } catch (_) { denied = true; }
  _check(denied, 'Wrong passphrase accepted');
  _stage('foreign_patient_must_fail');
  denied = false;
  try {
    final foreign = await D18VaultKeyPolicy.unlockWithPassphrase(
      scope: PatientVaultScope.deviceLocal(_b),
      publicEnvelopeJson: envelope, passphrase: _passphrase,
    );
    foreign.lock();
  } catch (_) { denied = true; }
  _check(denied, 'Foreign patient unlocked synthetic A');

  _stage('passphrase_decrypt');
  final byPassphrase = await D18VaultKeyPolicy.unlockWithPassphrase(
    scope: scope, publicEnvelopeJson: envelope, passphrase: _passphrase,
  );
  late final List<int> recovered;
  try {
    recovered = await AesGcm.with256bits().decrypt(
      box, secretKey: byPassphrase.requireUnlockedKey(), aad: aad,
    );
    _stage('tampered_ciphertext_must_fail');
    final corrupt = List<int>.of(sealed);
    corrupt[corrupt.length - 1] ^= 1;
    denied = false;
    try {
      await AesGcm.with256bits().decrypt(
        SecretBox.fromConcatenation(
          corrupt, nonceLength: 12, macLength: 16,
        ),
        secretKey: byPassphrase.requireUnlockedKey(),
        aad: aad,
      );
    } catch (_) { denied = true; }
    _check(denied, 'Tampered encrypted SQLite snapshot accepted');
  } finally {
    byPassphrase.lock();
  }

  _stage('offline_recovery_decrypt');
  // CI-only synthetic code: injected into this page's transient DOM by
  // Playwright. Never persisted; real patient recovery must use secure UI.
  final recoveryCode =
      html.document.documentElement?.dataset['d18RecoveryInput'];
  _check(recoveryCode is String && recoveryCode.startsWith('IAMINA-R1-'),
    'Independent offline recovery code was not provided');
  final byRecovery = await D18VaultKeyPolicy.unlockWithOfflineRecovery(
    scope: scope, publicEnvelopeJson: envelope,
    offlineRecoveryCode: recoveryCode as String,
  );
  try {
    final secondary = await AesGcm.with256bits().decrypt(
      box, secretKey: byRecovery.requireUnlockedKey(), aad: aad,
    );
    _check(_sameBytes(recovered, secondary),
      'Offline recovery did not restore exact SQLite bytes');
  } finally {
    byRecovery.lock();
  }

  _stage('compare_original_full_sqlite_bytes');
  final probe = await WasmDatabase.probe(
    sqlite3Uri: Uri.parse('sqlite3.wasm'),
    driftWorkerUri: Uri.parse('drift_worker.js'),
    databaseName: scope.databaseName,
  );
  final match = probe.existingDatabases.where((entry) =>
    entry.$1 == WebStorageApi.indexedDb && entry.$2 == scope.databaseName)
    .toList();
  _check(match.length == 1, 'Original A source missing after recovery');
  final original = await probe.exportDatabase(match.single);
  _check(original != null && _sameBytes(recovered, original),
    'Decrypted whole SQLite bytes differ from original on restart');
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
      case 'probe_backend':
        await _probeBackend();
        break;
      case 'probe_export':
        await _probeSnapshotCopy();
        break;
      case 'encrypt_snapshot':
        await _encryptSnapshot();
        break;
      case 'verify_encrypted_snapshot':
        await _verifyEncryptedSnapshot();
        break;
      case 'verify_export':
        await _verifySnapshotCopy();
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
