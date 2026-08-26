import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
// ignore: depend_on_referenced_packages
import 'package:sqlite3/sqlite3.dart' as sqlite;

void main() {
  test('pilot N-1 Drift v9 to v10 preserves retained local data', () async {
    final dir = await Directory.systemTemp.createTemp('iamina-pilot-v9-');
    final file = File('${dir.path}/amina.sqlite');
    final legacy = sqlite.sqlite3.open(file.path);

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
        ramadan_start_date INTEGER,
        ramadan_end_date INTEGER,
        ai_consent_given_at INTEGER
      );
    ''');
    legacy.execute('''
      INSERT INTO patient_profiles (
        user_id, preferred_language, updated_at, diabetes_type,
        target_range_low, target_range_high, unit_preference, treatment,
        ramadan_start_date, ramadan_end_date
      ) VALUES (
        7, 'fr', 1786406400, 'type2', 82.0, 155.0, 'mg/dL', 'tablets',
        1771372800, 1773964800
      );
    ''');

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
        meal_portions_json TEXT,
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
        created_at, blood_sugar, glycemic_context, meal_type, meal_description,
        source, sync_status, client_uuid, logged_at, sync_attempts, error_sync
      ) VALUES (
        1786406400, 143.0, 'post_meal', 'dinner', 'fixture dinner',
        'manual', 'pending', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        1786406400, 2, 0
      );
    ''');

    legacy.execute('''
      CREATE TABLE chat_messages (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at INTEGER NOT NULL
      );
    ''');
    legacy.execute('''
      INSERT INTO chat_messages (conversation_id, role, message, created_at)
      VALUES ('pilot-fixture', 'user', 'synthetic non-patient fixture', 1786406400);
    ''');

    legacy.execute('PRAGMA user_version = 9;');
    legacy.dispose();

    final db = AppDatabase(NativeDatabase(file));
    try {
      final profile = await db.select(db.patientProfiles).getSingle();
      expect(profile.userId, 7);
      expect(profile.diabetesType, 'type2');
      expect(profile.targetRangeLow, 82);
      expect(profile.targetRangeHigh, 155);
      expect(profile.treatment, 'tablets');

      final log = await db.select(db.logEntries).getSingle();
      expect(log.bloodSugar, 143);
      expect(log.glycemicContext, 'post_meal');
      expect(log.mealDescription, 'fixture dinner');
      expect(log.syncStatus, 'pending');
      expect(log.syncAttempts, 2);
      expect(log.errorSync, isFalse);
      expect(log.clientUuid, 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa');

      final chat = await db.select(db.chatMessages).getSingle();
      expect(chat.conversationId, 'pilot-fixture');
      expect(chat.role, 'user');
      expect(chat.message, 'synthetic non-patient fixture');

      expect(await db.select(db.medicationEvents).get(), isEmpty);
      expect(await db.select(db.reminders).get(), isEmpty);

      final version = await db.customSelect('PRAGMA user_version').getSingle();
      expect(version.data['user_version'], 10);
    } finally {
      await db.close();
      await dir.delete(recursive: true);
    }
  });
}
