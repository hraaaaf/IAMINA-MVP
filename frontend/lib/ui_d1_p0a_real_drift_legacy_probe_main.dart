// IAMINA D1 P0-A. CI-only real drift_flutter/SQLite WASM browser probe.
// Opens only disposable synthetic names within an ephemeral CI Chrome profile.
// NOT old-bundle compatibility, VFS upgrade, encryption or patient migration.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:amina/data/drift/patient_vault_scope.dart';
import 'package:drift/drift.dart';

const _deviceA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const _deviceB = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const _legacyFirst = 'd1-p0a-legacy-synthetic-first';
const _legacyLate = 'd1-p0a-legacy-synthetic-late';
const _historicalV5 = 'd1-p0a-historical-v5-seed';
const _aLog = 'd1-p0a-scope-a-synthetic';
const _bLog = 'd1-p0a-scope-b-synthetic';

Future<void> main() async {
  final phase = Uri.base.queryParameters['phase'] ?? 'invalid';
  html.document.title = 'IAMINA_D1P0A_PENDING';
  AppDatabase? db;
  try {
    const supported = {
      'seed_legacy', 'seed_a', 'late_legacy_write',
      'seed_b', 'verify_a', 'verify_b', 'verify_legacy',
      'verify_historical_v5_upgrade',
    };
    if (!supported.contains(phase)) {
      throw StateError('unsupported synthetic D1 P0-A phase');
    }
    final legacy = {'seed_legacy', 'late_legacy_write', 'verify_legacy',
      'verify_historical_v5_upgrade'}
        .contains(phase);
    final a = {'seed_a', 'verify_a'}.contains(phase);
    db = legacy
        ? AppDatabase.defaults()
        : AppDatabase.forPatientVault(
            PatientVaultScope.deviceLocal(a ? _deviceA : _deviceB),
          );
    final vault = db;
    await vault.customSelect('SELECT 1').getSingle();

    Future<void> absent(String uuid) async {
      final row = await (vault.select(vault.logEntries)
            ..where((entry) => entry.clientUuid.equals(uuid)))
          .getSingleOrNull();
      if (row != null) throw StateError('foreign or unexpected synthetic row');
    }

    Future<void> present(String uuid, double glucose) async {
      final row = await (vault.select(vault.logEntries)
            ..where((entry) => entry.clientUuid.equals(uuid)))
          .getSingleOrNull();
      if (row == null || row.bloodSugar != glucose) {
        throw StateError('synthetic row missing or changed');
      }
    }

    Future<void> insert(String uuid, double glucose) async {
      await absent(uuid);
      await vault.into(vault.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.utc(2026, 11, 10, 12),
          bloodSugar: glucose,
          clientUuid: uuid,
          syncStatus: const Value('pending'),
        ),
      );
      await present(uuid, glucose);
    }

    if (phase == 'verify_historical_v5_upgrade') {
      // This path is only used after an independent build from the real
      // Git revision where AppDatabase.schemaVersion was 5 seeded the DB.
      await present(_historicalV5, 105);
      final historicalRow = await (vault.select(vault.logEntries)
            ..where((t) => t.clientUuid.equals(_historicalV5)))
          .getSingle();
      final historicalProfile = await vault.getProfileForLocalUserId(734);
      if (historicalRow.syncStatus != 'pending' ||
          historicalProfile == null ||
          historicalProfile.diabetesType != 'type1' ||
          historicalProfile.treatment != 'insulin' ||
          historicalProfile.aiConsentGivenAt?.toUtc() !=
              DateTime.utc(2026, 11, 10, 12)) {
        throw StateError('historic v5 clinical fixture changed during upgrade');
      }
      if (await vault.countLogs() != 1) {
        throw StateError('historical log count not preserved');
      }
      await absent(_legacyFirst);
      await absent(_legacyLate);
      await absent(_aLog);
      await absent(_bLog);
      final currentVersion = await vault.customSelect('PRAGMA user_version').getSingle();
      if (currentVersion.data['user_version'] != 12) {
        throw StateError('historical v5-to-v12 upgrade did not commit');
      }
    } else if (phase == 'seed_legacy') {
      await absent(_legacyFirst);
      await absent(_aLog);
      await absent(_bLog);
      await insert(_legacyFirst, 101);
    } else if (phase == 'late_legacy_write') {
      await present(_legacyFirst, 101);
      await absent(_aLog);
      await absent(_bLog);
      // The current unscoped legacy constructor remains writable after A
      // has been created. This does NOT emulate an old cached JS bundle.
      await insert(_legacyLate, 102);
    } else if (phase == 'verify_legacy') {
      await present(_legacyFirst, 101);
      await present(_legacyLate, 102);
      await absent(_aLog);
      await absent(_bLog);
    } else if (phase == 'seed_a') {
      await absent(_legacyFirst);
      await absent(_legacyLate);
      await absent(_bLog);
      await insert(_aLog, 111);
    } else if (phase == 'verify_a') {
      await present(_aLog, 111);
      await absent(_legacyFirst);
      await absent(_legacyLate);
      await absent(_bLog);
    } else if (phase == 'seed_b') {
      await absent(_legacyFirst);
      await absent(_legacyLate);
      await absent(_aLog);
      await insert(_bLog, 222);
    } else if (phase == 'verify_b') {
      await present(_bLog, 222);
      await absent(_legacyFirst);
      await absent(_legacyLate);
      await absent(_aLog);
    }

    // A real SQLite check through the app's actual Drift connection.
    final integrity = await vault.customSelect('PRAGMA integrity_check').getSingle();
    if (integrity.data.values.single != 'ok') {
      throw StateError('physical SQLite integrity check failed');
    }
    await vault.close();
    html.document.title = 'IAMINA_D1P0A_${phase.toUpperCase()}_PASS';
  } catch (error) {
    if (db != null) {
      try {
        await db.close();
      } catch (_) {
        // Keep the original failure.
      }
    }
    html.document.title = 'IAMINA_D1P0A_FAIL:${error.runtimeType}';
  }
}
