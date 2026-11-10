// CI-only synthetic fixture copied into a checkout of IAMINA historical v5.
// This code is NEVER distributed to an app or used on real patient data.
// Historical source is pinned to a1d46f9be5f2190a1e8380f28fe4679954f9863f.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:drift/drift.dart';

const _id = 'd1-p0a-historical-v5-seed';

Future<void> main() async {
  html.document.title = 'IAMINA_V5_PENDING';
  AppDatabase? db;
  try {
    db = AppDatabase.defaults();
    final vault = db;
    await vault.customSelect('SELECT 1').getSingle();
    final initialVersion = await vault.customSelect('PRAGMA user_version').getSingle();
    if (initialVersion.data['user_version'] != 5) {
      throw StateError('historical database must be at schemaVersion=5');
    }
    final existing = await (vault.select(vault.logEntries)
          ..where((t) => t.clientUuid.equals(_id)))
        .getSingleOrNull();
    if (existing != null) throw StateError('v5 fixture reused unexpectedly');
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
    if (stored == null || stored.bloodSugar != 105 ||
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
