import 'dart:convert';

import 'package:drift/drift.dart';

import 'database.dart';

/// Versioned local-first backup/restore for IAMINA's Drift-owned pilot data.
///
/// The payload contains only rows already present in the local database. It does
/// not upload, transmit, encrypt, or otherwise move data by itself.
final class LocalBackup {
  static const int formatVersion = 1;

  static Future<String> exportJson(AppDatabase db) async {
    final logs = await db.select(db.logEntries).get();
    final profiles = await db.select(db.patientProfiles).get();
    final chats = await db.select(db.chatMessages).get();
    final medications = await db.select(db.medicationEvents).get();
    final reminders = await db.select(db.reminders).get();

    return jsonEncode(<String, dynamic>{
      'formatVersion': formatVersion,
      'schemaVersion': db.schemaVersion,
      'createdAtUtc': DateTime.now().toUtc().toIso8601String(),
      'logEntries': logs.map((row) => row.toJson()).toList(),
      'patientProfiles': profiles.map((row) => row.toJson()).toList(),
      'chatMessages': chats.map((row) => row.toJson()).toList(),
      'medicationEvents': medications.map((row) => row.toJson()).toList(),
      'reminders': reminders.map((row) => row.toJson()).toList(),
    });
  }

  static Future<void> restoreJson(AppDatabase db, String rawBackup) async {
    final root = _asMap(jsonDecode(rawBackup), 'backup root');

    if (root['formatVersion'] != formatVersion) {
      throw FormatException(
        'Unsupported backup formatVersion: ${root['formatVersion']}',
      );
    }
    if (root['schemaVersion'] != db.schemaVersion) {
      throw FormatException(
        'Backup schemaVersion ${root['schemaVersion']} does not match '
        'database schemaVersion ${db.schemaVersion}',
      );
    }

    // Decode every row before opening the destructive transaction. A malformed
    // payload therefore cannot clear a healthy local database.
    final logs = _rows(root, 'logEntries')
        .map(LogEntryData.fromJson)
        .toList(growable: false);
    final profiles = _rows(root, 'patientProfiles')
        .map(PatientProfileData.fromJson)
        .toList(growable: false);
    final chats = _rows(root, 'chatMessages')
        .map(ChatMessageData.fromJson)
        .toList(growable: false);
    final medications = _rows(root, 'medicationEvents')
        .map(MedicationEventData.fromJson)
        .toList(growable: false);
    final reminders = _rows(root, 'reminders')
        .map(ReminderData.fromJson)
        .toList(growable: false);

    await db.transaction(() async {
      await db.delete(db.logEntries).go();
      await db.delete(db.patientProfiles).go();
      await db.delete(db.chatMessages).go();
      await db.delete(db.medicationEvents).go();
      await db.delete(db.reminders).go();

      for (final row in logs) {
        await db.into(db.logEntries).insert(row);
      }
      for (final row in profiles) {
        await db.into(db.patientProfiles).insert(row);
      }
      for (final row in chats) {
        await db.into(db.chatMessages).insert(row);
      }
      for (final row in medications) {
        await db.into(db.medicationEvents).insert(row);
      }
      for (final row in reminders) {
        await db.into(db.reminders).insert(row);
      }

      await _requireCount(
        'logEntries',
        logs.length,
        db.logEntries.count().getSingle(),
      );
      await _requireCount(
        'patientProfiles',
        profiles.length,
        db.patientProfiles.count().getSingle(),
      );
      await _requireCount(
        'chatMessages',
        chats.length,
        db.chatMessages.count().getSingle(),
      );
      await _requireCount(
        'medicationEvents',
        medications.length,
        db.medicationEvents.count().getSingle(),
      );
      await _requireCount(
        'reminders',
        reminders.length,
        db.reminders.count().getSingle(),
      );
    });
  }

  static Map<String, dynamic> _asMap(dynamic value, String label) {
    if (value is! Map) {
      throw FormatException('$label must be a JSON object');
    }
    return Map<String, dynamic>.from(value);
  }

  static List<Map<String, dynamic>> _rows(
    Map<String, dynamic> root,
    String key,
  ) {
    final value = root[key];
    if (value is! List) {
      throw FormatException('$key must be a JSON array');
    }
    return value
        .map((row) => _asMap(row, '$key row'))
        .toList(growable: false);
  }

  static Future<void> _requireCount(
    String table,
    int expected,
    Future<int> actualFuture,
  ) async {
    final actual = await actualFuture;
    if (actual != expected) {
      throw StateError(
        'Backup restore count mismatch for $table: expected $expected, got $actual',
      );
    }
  }
}
