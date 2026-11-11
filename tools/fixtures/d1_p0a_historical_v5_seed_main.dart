// CI-only synthetic fixture copied into a checkout of IAMINA historical v5.
// This code is NEVER distributed to an app or used on real patient data.
// Historical source is pinned to a1d46f9be5f2190a1e8380f28fe4679954f9863f.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:drift/drift.dart';

const _id = 'd1-p0a-historical-v5-seed';
const _oldTabLateId = 'd1-p0a-real-old-v5-tab-late-write';

Future<void> main() async {
  html.document.title = 'IAMINA_V5_PENDING';
  AppDatabase? db;
  try {
    db = AppDatabase.defaults();
    final vault = db;
    await vault.customSelect('SELECT 1').getSingle();
    // A real historical Flutter/Drift v5 tab stays alive while a separate
    // *current* v12 browser tab opens a new isolated vault A. Message-based
    // test control only, no storage/crypto shims and no clinical data.
    if (Uri.base.queryParameters['phase'] == 'hold_old_tab') {
      final first = await (vault.select(vault.logEntries)
            ..where((row) => row.clientUuid.equals(_id))).getSingleOrNull();
      if (first == null || first.bloodSugar != 105) {
        throw StateError('historical seed missing before old-tab hold');
      }
      html.window.onMessage.listen((event) async {
        if (event.data != 'IAMINA_D1_V5_LATE_WRITE') return;
        try {
          final existing = await (vault.select(vault.logEntries)
                ..where((row) => row.clientUuid.equals(_oldTabLateId)))
              .getSingleOrNull();
          if (existing != null) throw StateError('old-tab fixture reused');
          await vault.into(vault.logEntries).insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime.utc(2026, 11, 10, 12, 1),
              bloodSugar: 106,
              clientUuid: _oldTabLateId,
              syncStatus: const Value('pending'),
            ),
          );
          final late = await (vault.select(vault.logEntries)
                ..where((row) => row.clientUuid.equals(_oldTabLateId)))
              .getSingleOrNull();
          if (late?.bloodSugar != 106) {
            throw StateError('old-tab late write not durable');
          }
          html.document.title = 'IAMINA_V5_LATE_WRITE_AFTER_V12_A_PASS';
        } catch (error) {
          html.document.title = 'IAMINA_V5_LATE_WRITE_FAIL:${error.runtimeType}';
        }
      });
      html.document.title = 'IAMINA_V5_LIVE_OLD_TAB_READY';
      return; // Keep the real v5 SQLite connection alive in this tab.
    }
    final initialVersion = await vault.customSelect('PRAGMA user_version').getSingle();
    if (initialVersion.data['user_version'] != 5) {
      throw StateError('historical database must be at schemaVersion=5');
    }
    final existing = await (vault.select(vault.logEntries)
          ..where((t) => t.clientUuid.equals(_id)))
        .getSingleOrNull();
    if (existing != null) throw StateError('v5 fixture reused unexpectedly');
    await vault.into(vault.patientProfiles).insert(
      PatientProfilesCompanion.insert(
        userId: const Value(734),
        updatedAt: DateTime.utc(2026, 11, 10, 12),
        diabetesType: const Value('type1'),
        treatment: const Value('insulin'),
        aiConsentGivenAt: Value(DateTime.utc(2026, 11, 10, 12)),
      ),
    );
    await vault.into(vault.logEntries).insert(
      LogEntriesCompanion.insert(
        createdAt: DateTime.utc(2026, 11, 10),
        bloodSugar: 105,
        clientUuid: _id,
        syncStatus: const Value('pending'),
      ),
    );
    final stored = await (vault.select(vault.logEntries)
          ..where((t) => t.clientUuid.equals(_id)))
        .getSingleOrNull();
    final check = await vault.customSelect('PRAGMA integrity_check').getSingle();
    final profile = await (vault.select(vault.patientProfiles)
          ..where((t) => t.userId.equals(734)))
        .getSingleOrNull();
    if (stored == null || stored.bloodSugar != 105 ||
        stored.syncStatus != 'pending' || profile == null ||
        profile.diabetesType != 'type1' ||
        profile.treatment != 'insulin' ||
        profile.aiConsentGivenAt?.toUtc() != DateTime.utc(2026, 11, 10, 12) ||
        check.data.values.single != 'ok') {
      throw StateError('historical v5 storage integrity failed');
    }
    await vault.close();
    html.document.title = 'IAMINA_V5_SEED_PASS';
  } catch (error) {
    if (db != null) {
      try {
        await db.close();
      } catch (_) {}
    }
    html.document.title = 'IAMINA_V5_FAIL:${error.runtimeType}';
  }
}
