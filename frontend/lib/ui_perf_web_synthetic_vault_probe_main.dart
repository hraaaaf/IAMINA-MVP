// PERF-WEB CI-only: real Drift Web database with disposable synthetic records.
// Not a production entrypoint, real account, or clinical use.
// ignore: avoid_web_libraries_in_flutter
import 'dart:convert';
import 'dart:html' as html;
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:amina/services/medical_vault_protected_state.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:drift/drift.dart' as drift;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

const _emptyId = '11111111-1111-4111-8111-111111111111';
const _filledId = '22222222-2222-4222-8222-222222222222';
const _n = 300;
const _key = 'iamina_perf_web_synthetic_v1';
const _progressKey = 'iamina_perf_web_synthetic_progress_v1';
void _stage(String value) {
  // Codes only, never patient data, credentials or error strings.
  html.document.title = 'IAMINA_PERF_WEB_STAGE:' + value;
  html.window.localStorage[_progressKey] = value;
}
PatientVaultScope _scope(bool filled) =>
    PatientVaultScope.deviceLocal(filled ? _filledId : _emptyId);
void _check(bool ok, String reason) {
  if (!ok) throw StateError(reason);
}
double _ms(Stopwatch watch) => watch.elapsedMicroseconds / 1000;
Future<int> _count(AppDatabase db) async {
  final row = await db.customSelect(
    'SELECT COUNT(*) AS n FROM log_entries',
  ).getSingle();
  return row.read<int>('n');
}
Future<Map<String, Object?>> _seed() async {
  _stage('seed_legacy_open');
  final legacy = AppDatabase.defaults();
  try {
    await legacy.customSelect('SELECT 1').getSingle();
    _stage('seed_legacy_guard');
    _check(!await hasProtectedMedicalVaultRows(legacy), 'legacy not empty');
  } finally {
    await legacy.close();
  }
  for (final filled in [false, true]) {
    final label = filled ? 'filled' : 'empty';
    _stage('seed_' + label + '_open');
    final db = AppDatabase.forPatientVault(_scope(filled));
    try {
      await db.customSelect('SELECT 1').getSingle();
      _stage('seed_' + label + '_count');
      _check(await _count(db) == 0, 'nonempty synthetic fixture');
      if (filled) {
        _stage('seed_filled_profile');
        await db.into(db.patientProfiles).insert(
          PatientProfilesCompanion.insert(
            userId: drift.Value(db.activeProfileRowId),
            updatedAt: DateTime.utc(2026, 11, 3),
            diabetesType: const drift.Value('type2'),
          ),
        );
        _stage('seed_filled_batch');
        await db.batch((batch) {
          for (var i = 0; i < _n; i++) {
            batch.insert(db.logEntries, LogEntriesCompanion.insert(
              createdAt: DateTime.utc(2026, 11, 3),
              bloodSugar: 100.0 + (i % 10).toDouble(),
              clientUuid: 'perf-web-synth-$i',
            ));
          }
        });
      }
      _stage('seed_' + label + '_verify');
      _check(await _count(db) == (filled ? _n : 0), 'seed count mismatch');
      _check(await hasProtectedMedicalVaultRows(db) == filled,
          'seed guard mismatch');
    } finally {
      await db.close();
    }
  }
  _stage('seed_done');
  return {'phase':'seed','seeded_rows':_n,'fixture':'synthetic_only'};
}
Future<Map<String, Object?>> _measure(bool filled) async {
  _stage(filled ? 'filled_legacy_probe' : 'empty_legacy_probe');
  final total = Stopwatch()..start();
  final legacyWatch = Stopwatch()..start();
  final legacy = AppDatabase.defaults();
  late final bool legacyProtected;
  try {
    legacyProtected = await hasProtectedMedicalVaultRows(legacy);
  } finally {
    await legacy.close();
    legacyWatch.stop();
  }
  _check(!legacyProtected, 'unexpected legacy protected state');

  final scope = _scope(filled);
  final openWatch = Stopwatch()..start();
  _stage(filled ? 'filled_scoped_open' : 'empty_scoped_open');
  final db = AppDatabase.forPatientVault(scope);
  late final bool protected;
  late final int rows;
  late final double openMs;
  late final double guardMs;
  try {
    await db.customSelect('SELECT 1').getSingle();
    openWatch.stop();
    openMs = _ms(openWatch);
    _stage(filled ? 'filled_protected_scan' : 'empty_protected_scan');
    final guardWatch = Stopwatch()..start();
    protected = await hasProtectedMedicalVaultRows(db);
    guardWatch.stop();
    guardMs = _ms(guardWatch);
    rows = await _count(db);
  } finally {
    await db.close();
  }
  _check(protected == filled, 'synthetic guard mismatched');
  _check(rows == (filled ? _n : 0), 'synthetic rows not persisted');

  // Real controller with a fake, isolated principal only. No AuthService.
  final notifier = ChangeNotifier();
  final controllerWatch = Stopwatch()..start();
  _stage(filled ? 'filled_controller' : 'empty_controller');
  final controller = PatientVaultSessionController(
    authChanges: notifier, resolveScope: () async => scope,
  );
  late final bool hasVault;
  try {
    // Mirrors main.dart explicit await after constructor unawaited reconcile.
    await controller.reconcile();
    controllerWatch.stop();
    hasVault = controller.hasVault;
    _check(hasVault, 'synthetic controller could not open vault');
  } finally {
    controller.dispose();
    notifier.dispose();
  }
  total.stop();
  return {
    'phase':filled ? 'populated' : 'empty',
    'fixture':'synthetic_only','rows':rows,'protected':protected,
    'legacy_protected':legacyProtected,'controller_has_vault':hasVault,
    'legacy_probe_ms':_ms(legacyWatch),
    'scoped_db_open_ms':openMs,'protected_scan_ms':guardMs,
    'controller_reconcile_ms':_ms(controllerWatch),
    'local_startup_subset_ms':_ms(total),
  };
}
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final phase = Uri.base.queryParameters['phase'] ?? '';
  _stage('entry');
  try {
    if (!{'seed','empty','populated'}.contains(phase)) {
      throw StateError('unknown synthetic phase');
    }
    final data = phase == 'seed'
        ? await _seed() : await _measure(phase == 'populated');
    html.window.localStorage[_key] = jsonEncode(data);
    html.document.title = 'IAMINA_PERF_WEB_' + phase.toUpperCase() + '_PASS';
    runApp(const MaterialApp(
      home: Scaffold(body: Center(
        child: Text('PERF-WEB — synthetic database only'),
      )),
    ));
  } catch (error) {
    // MaterialApp can overwrite document.title after runApp. A structured,
    // synthetic-only status survives Flutter's document metadata updates.
    final failingStage = html.window.localStorage[_progressKey] ?? 'unknown';
    // Only bounded allowlisted synthetic test assertions, never raw exception
    // messages/clinical data/SQL contents are exposed in proof files.
    final knownMessages = <String, String>{
      'synthetic guard mismatched': 'guard_presence_mismatch',
      'synthetic rows not persisted': 'row_persistence_mismatch',
      'unexpected legacy protected state': 'legacy_guard_unexpected',
      'synthetic controller could not open vault': 'controller_missing_vault',
      'seed count mismatch': 'seed_count_mismatch',
      'seed guard mismatch': 'seed_guard_mismatch',
      'nonempty synthetic fixture': 'nonempty_seed_fixture',
      'legacy not empty': 'legacy_not_empty',
    };
    final name = error.toString();
    final reason = knownMessages.entries
        .where((entry) => name.contains(entry.key))
        .map((entry) => entry.value)
        .firstOrNull ?? 'other_error';
    html.window.localStorage[_key] = jsonEncode({
      'phase': phase,
      'status': 'FAIL',
      'error_type': error.runtimeType.toString(),
      'failure_stage': failingStage,
      'failure_reason': reason,
      'fixture': 'synthetic_only',
    });
    _stage('failure');
    html.document.title = 'IAMINA_PERF_WEB_FAIL:' + error.runtimeType.toString();
    runApp(const MaterialApp(
      home: Scaffold(body: Text('Synthetic probe failed')),
    ));
  }
}
