import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
// ignore: depend_on_referenced_packages
import 'package:sqlite3/sqlite3.dart' as sqlite;

void main() {
  test(
    'Drift v7 to v8 adds meal_portions_json without rewriting existing logs',
    () async {
      final dir = await Directory.systemTemp.createTemp('iamina-journal-v7-');
      final file = File('${dir.path}/amina.sqlite');
      final legacy = sqlite.sqlite3.open(file.path);
      legacy.execute('''
      CREATE TABLE log_entries (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        created_at INTEGER NOT NULL,
        blood_sugar REAL NOT NULL,
        insulin_units REAL,
        glycemic_context TEXT,
        meal_type TEXT,
        meal_description TEXT,
        meal_items_json TEXT,
        source TEXT NOT NULL DEFAULT 'manual',
        sync_status TEXT NOT NULL DEFAULT 'pending',
        client_uuid TEXT NOT NULL UNIQUE,
        logged_at INTEGER,
        fatigue_level INTEGER,
        is_sick INTEGER NOT NULL DEFAULT 0 CHECK (is_sick IN (0, 1)),
        is_stressed INTEGER NOT NULL DEFAULT 0 CHECK (is_stressed IN (0, 1)),
        is_tired INTEGER NOT NULL DEFAULT 0 CHECK (is_tired IN (0, 1)),
        is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
        ramadan_mode INTEGER NOT NULL DEFAULT 0 CHECK (ramadan_mode IN (0, 1)),
        sleep_quality TEXT,
        sync_attempts INTEGER NOT NULL DEFAULT 0,
        error_sync INTEGER NOT NULL DEFAULT 0 CHECK (error_sync IN (0, 1))
      );
    ''');
      legacy.execute('''
      INSERT INTO log_entries (
        created_at, blood_sugar, glycemic_context, meal_type,
        meal_description, meal_items_json, source, sync_status, client_uuid
      ) VALUES (
        1723200000, 126.0, 'pre_meal', 'lunch', 'ancienne note',
        '["couscous"]', 'manual', 'pending',
        '88888888-8888-8888-8888-888888888888'
      );
    ''');
      legacy.execute('PRAGMA user_version = 7;');
      legacy.dispose();

      final db = AppDatabase(NativeDatabase(file));
      try {
        final logs = await db.select(db.logEntries).get();
        expect(logs, hasLength(1));
        expect(logs.single.mealDescription, 'ancienne note');
        expect(logs.single.glycemicContext, 'pre_meal');
        expect(logs.single.mealItemsJson, '["couscous"]');
        expect(logs.single.mealPortionsJson, isNull);
        expect(logs.single.clientUuid, '88888888-8888-8888-8888-888888888888');
        final version = await db.customSelect('PRAGMA user_version').getSingle();
        expect(version.data['user_version'], 8);
      } finally {
        await db.close();
        await dir.delete(recursive: true);
      }
    },
  );
}
