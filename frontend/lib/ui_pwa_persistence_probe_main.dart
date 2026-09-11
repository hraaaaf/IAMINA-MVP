// CI-only synthetic browser probe for P5-4A. Never used by the production entrypoint.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:amina/data/drift/database.dart';
import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

const _fixtureUuid = 'p5-4a-pwa-persistence-synthetic-fixture';

Future<void> main() async {
  var storage = 'unknown';
  final connection = driftDatabase(
    name: 'iamina_pwa_probe',
    web: DriftWebOptions(
      sqlite3Wasm: Uri.parse('sqlite3.wasm'),
      driftWorker: Uri.parse('drift_worker.js'),
      onResult: (result) {
        storage = result.chosenImplementation.name;
      },
    ),
  );
  final db = AppDatabase(connection);
  final phase = Uri.base.queryParameters['phase'] ?? 'seed';

  try {
    if (phase == 'seed') {
      await (db.delete(
        db.logEntries,
      )..where((row) => row.clientUuid.equals(_fixtureUuid))).go();
      await db.into(db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: DateTime.utc(2026, 9, 11, 12),
          bloodSugar: 137.0,
          clientUuid: _fixtureUuid,
          syncStatus: const Value('pending'),
          syncAttempts: const Value(2),
        ),
      );
      await db.close();
      html.document.title = 'IAMINA_PWA_SEEDED:$storage';
      return;
    }

    if (phase == 'verify') {
      final row = await (db.select(
        db.logEntries,
      )..where((entry) => entry.clientUuid.equals(_fixtureUuid))).getSingleOrNull();
      if (row == null) {
        throw StateError('synthetic fixture missing after browser navigation/reload');
      }
      if (row.bloodSugar != 137.0 ||
          row.syncStatus != 'pending' ||
          row.syncAttempts != 2) {
        throw StateError('synthetic fixture changed after browser navigation/reload');
      }
      await db.close();
      html.document.title = 'IAMINA_PWA_RESTORED:$storage';
      return;
    }

    throw ArgumentError.value(phase, 'phase', 'expected seed or verify');
  } catch (error) {
    try {
      await db.close();
    } catch (_) {
      // Preserve the original probe failure.
    }
    html.document.title = 'IAMINA_PWA_ERROR:${error.runtimeType}';
  }
}
