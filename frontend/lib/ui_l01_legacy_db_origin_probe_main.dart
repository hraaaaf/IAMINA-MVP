// CI-only L01/D18 legacy DB bootstrap experiment. Never import this entrypoint
// from the patient app. Uses an isolated Chrome profile and synthetic origin.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:drift/drift.dart';
import 'package:flutter/material.dart';

import 'data/drift/database.dart';
import 'services/medical_vault_protected_state.dart';

const _fakeUuid = 'iamina-l01-legacy-v11-synthetic-only';

void _report(String status) => html.document.documentElement
    ?.setAttribute('data-l01-phase-result', status);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Control phase: no database constructor or query of any kind.
  // Legacy phase: reproduce main.dart's default-name SELECT on a clean origin.
  // v11 phases: a deliberately synthetic old schema in THIS disposable Chrome.
  final phase = Uri.base.queryParameters['phase'];
  if (phase == 'control') {
    _report('IAMINA_L01_CONTROL');
  } else if (phase == 'legacy_probe' ||
      phase == 'seed_legacy_v11' ||
      phase == 'probe_legacy_v11') {
    final legacy = AppDatabase.defaults();
    try {
      if (phase == 'seed_legacy_v11') {
        // Build latest schema first, seed a fake clinical row, then downgrade
        // ONLY this CI-only temporary database to the historical v11 shape.
        await legacy.customSelect('SELECT 1').getSingle();
        await legacy.into(legacy.logEntries).insert(
          LogEntriesCompanion.insert(
            createdAt: DateTime.utc(2026, 11, 4),
            bloodSugar: 111.0,
            clientUuid: _fakeUuid,
            syncStatus: const Value('pending'),
          ),
        );
        for (final column in [
          'local_generation',
          'base_server_updated_at',
          'sync_status',
        ]) {
          await legacy.customStatement(
            'ALTER TABLE patient_treatment_declarations_v1 DROP COLUMN $column',
          );
        }
        await legacy.customStatement('PRAGMA user_version = 11');
        _report('IAMINA_L01_V11_SEEDED');
      } else if (phase == 'probe_legacy_v11') {
        // This is intentionally the production presence-only API, which could
        // invoke Drift migrations simply by opening the historical vault.
        final protected = await hasProtectedMedicalVaultRows(legacy);
        final versionRows =
            await legacy.customSelect('PRAGMA user_version').get();
        final version =
            versionRows.single.data['user_version']?.toString() ?? 'unknown';
        final fakeRows = await (legacy.select(legacy.logEntries)
              ..where((row) => row.clientUuid.equals(_fakeUuid)))
            .get();
        _report(
            'IAMINA_L01_PROBED_V${version}_ROWS_${fakeRows.length}_PROTECTED_${protected}');
      } else {
        await hasProtectedMedicalVaultRows(legacy);
        _report('IAMINA_L01_PROBE_DONE');
      }
    } finally {
      await legacy.close();
    }
  } else {
    throw StateError('Unknown CI-only L01 phase; no patient data allowed');
  }

  runApp(const MaterialApp(
    home: Scaffold(
      body: Center(child: Text('IAMINA L01 SYNTHETIC LEGACY DB PROBE')),
    ),
  ));
}
