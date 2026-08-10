import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
// ignore: depend_on_referenced_packages
import 'package:sqlite3/sqlite3.dart' as sqlite;

void main() {
  test('Drift v5 to latest keeps context and existing logs', () async {
    final dir = await Directory.systemTemp.createTemp('iamina-journal-v5-');
    final file = File('${dir.path}/amina.sqlite');

    final legacy = sqlite.sqlite3.open(file.path);
    legacy.execute('''
      CREATE TABLE log_entries (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        created_at INTEGER NOT NULL,
        blood_sugar REAL NOT NULL,
        insulin_units REAL,
        meal_type TEXT,
        meal_description TEXT,
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
      CREATE TABLE patient_profiles (
        user_id INTEGER NOT NULL PRIMARY KEY,
        preferred_language TEXT NOT NULL DEFAULT 'fr',
        updated_at INTEGER NOT NULL,
        diabetes_type TEXT,
        target_range_low REAL NOT NULL DEFAULT 70.0,
        target_range_high REAL NOT NULL DEFAULT 180.0,
        unit_preference TEXT NOT NULL DEFAULT 'mg/dL',
        treatment TEXT,
        ai_consent_given_at INTEGER
      );
    ''');
    legacy.execute('''
      INSERT INTO patient_profiles (
        user_id, preferred_language, updated_at, diabetes_type, treatment
      ) VALUES (1, 'fr', 1723200000, 'type2', 'lifestyle');
    ''');
    legacy.execute('''
      INSERT INTO log_entries (
        created_at, blood_sugar, meal_type, source, sync_status, client_uuid
      ) VALUES (
        1723200000, 126.0, 'Déjeuner', 'manual', 'pending',
        '55555555-5555-5555-5555-555555555555'
      );
    ''');
    legacy.execute('PRAGMA user_version = 5;');
    legacy.dispose();

    final db = AppDatabase(NativeDatabase(file));
    try {
      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(logs.single.mealType, 'Déjeuner');
      expect(logs.single.glycemicContext, isNull);
      expect(logs.single.mealItemsJson, isNull);
      expect(logs.single.mealPortionsJson, isNull);
      expect(logs.single.clientUuid, '55555555-5555-5555-5555-555555555555');

      final profile = await db.select(db.patientProfiles).getSingle();
      expect(profile.userId, 1);
      expect(profile.diabetesType, 'type2');
      expect(profile.treatment, 'lifestyle');
      expect(profile.ramadanStartDate, isNull);
      expect(profile.ramadanEndDate, isNull);

      final version = await db.customSelect('PRAGMA user_version').getSingle();
      expect(version.data['user_version'], 9);
    } finally {
      await db.close();
      await dir.delete(recursive: true);
    }
  });
}
