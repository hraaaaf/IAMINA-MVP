import 'dart:convert';

import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_treatment_declaration_store.dart';
import 'patient_vault_scope.dart';
import 'patient_weight_history_store.dart';

/// Versioned local-first backup/restore for IAMINA's Drift-owned pilot data.
///
/// The payload contains only rows already present in the local database. It does
/// not upload, transmit, encrypt, or otherwise move data by itself.
final class LocalBackup {
  static const int formatVersion = 1;
  static const int scopedFormatVersion = 2;

  // Version 1 applies only to the historical unscoped "amina" database.
  // It cannot be imported into an authenticated patient vault without review.
  static Future<String> exportJson(AppDatabase db) async {
    if (db.patientVaultScope != null) {
      throw StateError('Use the patient-vault backup protocol.');
    }
    return _exportRows(db);
  }

  static Future<String> exportVaultJson(AppDatabase db) async {
    final scope = db.patientVaultScope;
    if (scope == null) {
      throw StateError('Cannot claim legacy mixed data as a patient vault.');
    }
    await _assertExportOwnerScope(db);
    final envelope = _asMap(jsonDecode(await _exportRows(db)), 'backup');
    envelope['formatVersion'] = scopedFormatVersion;
    envelope['vaultName'] = scope.databaseName;
    final declaredRows = await db.customSelect(
      '''SELECT user_id, declaration_state, codes_json, declaration_version,
         provenance, updated_at_utc, sync_status,
         base_server_updated_at, local_generation
         FROM patient_treatment_declarations_v1''',
    ).get();
    envelope['treatmentDeclarations'] = [
      for (final row in declaredRows) Map<String, dynamic>.from(row.data),
    ];
    // D18: make every explicit weight observation part of scoped backup.
    // Never backfill or manufacture timestamps from legacy profile.weight.
    final store = scope.databaseName ==
            PatientVaultScope.auditOnly().databaseName
        ? null
        : PatientWeightHistoryStore(db);
    envelope['weightHistoryFormatVersion'] = 1;
    envelope['weightObservations'] = store == null
        ? <Map<String, Object?>>[]
        : await store.exportOwnedRows();
    return jsonEncode(envelope);
  }

  static Future<String> _exportRows(AppDatabase db) async {
    final logs = await db.select(db.logEntries).get();
    final profiles = await db.select(db.patientProfiles).get();
    if (db.patientVaultScope == null && profiles.length > 1) {
      throw StateError('Ambiguous legacy backup: multiple patient profiles.');
    }
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
    if (db.patientVaultScope != null) {
      throw StateError('Legacy restore cannot overwrite a patient vault.');
    }
    final root = _asMap(jsonDecode(rawBackup), 'backup root');
    if (root['vaultName'] != null) {
      throw FormatException('Scoped data cannot be imported as legacy data');
    }
    final existingDeclarations = await db.customSelect(
      'SELECT user_id FROM patient_treatment_declarations_v1 LIMIT 1',
    ).get();
    if (existingDeclarations.isNotEmpty) {
      throw StateError('Legacy format cannot overwrite D7 declarations.');
    }
    return _restoreRows(db, root);
  }

  static Future<void> restoreVaultJson(
    AppDatabase db,
    String rawBackup,
  ) async {
    final scope = db.patientVaultScope;
    if (scope == null) {
      throw StateError('A scoped backup requires a scoped destination.');
    }
    final root = _asMap(jsonDecode(rawBackup), 'backup root');
    if (root['formatVersion'] != scopedFormatVersion ||
        root['vaultName'] != scope.databaseName) {
      throw FormatException('Backup vault identity mismatch');
    }
    // Check owner before touching even a single destination row. Restoring
    // old unscoped backup requires an explicit, separate recovery flow.
    final owner = db.activeProfileRowId;
    final profiles = _rows(root, 'patientProfiles');
    if (profiles.length > 1 ||
        profiles.any((row) => row['userId'] != owner) ||
        (profiles.isEmpty && _hasUnownedClinicalRows(root))) {
      throw FormatException('Backup does not match its patient vault owner');
    }
    final legacyV10 = root['schemaVersion'] == 10 &&
        db.schemaVersion == 11 && root['treatmentDeclarations'] == null;
    // V11 scoped exports contain the patient's statements but no CAS receipt.
    // Import them into v12 as PENDING: never invent server confirmation.
    final olderV11 = root['schemaVersion'] == 11 &&
        db.schemaVersion == 12;
    if (!legacyV10 && root['schemaVersion'] == 11 &&
        root['treatmentDeclarations'] == null) {
      throw FormatException('D7 declarations missing from patient backup');
    }
    if (legacyV10 || olderV11) {
      final existingDeclarations = await db.customSelect(
        'SELECT user_id FROM patient_treatment_declarations_v1 LIMIT 1',
      ).get();
      if (existingDeclarations.isNotEmpty) {
        throw StateError('Old backup cannot overwrite newer D7 declarations.');
      }
    }
    final declarations = legacyV10
        ? <Map<String, dynamic>>[]
        : [
            for (final row in _rows(root, 'treatmentDeclarations'))
              if (olderV11)
                {
                  ...row,
                  'sync_status': 'pending',
                  'base_server_updated_at': null,
                  'local_generation': 1,
                }
              else
                row,
          ];
    for (final row in declarations) {
      if (row['user_id'] != owner || profiles.isEmpty) {
        throw FormatException('Foreign patient treatment declaration');
      }
      _validatedTreatmentDeclarationRow(row);
    }

    // Older scoped-v2 backups predate D18 and contain no weight observations.
    // They may restore ONLY when no newer local weight data could be lost.
    final hasWeights = root.containsKey('weightObservations');
    if (hasWeights != root.containsKey('weightHistoryFormatVersion')) {
      throw const FormatException('Incomplete D18 backup section');
    }
    if (hasWeights && root['weightHistoryFormatVersion'] != 1) {
      throw const FormatException('Unsupported D18 backup format');
    }
    final weightRows = hasWeights
        ? _rows(root, 'weightObservations')
        : <Map<String, dynamic>>[];
    if (scope.databaseName == PatientVaultScope.auditOnly().databaseName &&
        weightRows.isNotEmpty) {
      throw const FormatException('Audit vault cannot import patient weights');
    }
    for (final row in weightRows) {
      if (profiles.isEmpty) {
        throw const FormatException('Weight backup requires owned profile');
      }
      PatientWeightHistoryStore.validateBackupRow(row, owner);
    }
    final store = scope.databaseName ==
            PatientVaultScope.auditOnly().databaseName
        ? null
        : PatientWeightHistoryStore(db);
    if (store != null) {
      final localRows = await store.exportOwnedRows();
      if (!hasWeights && localRows.isNotEmpty) {
        throw StateError(
          'Legacy scoped backup cannot overwrite newer D18 weight history',
        );
      }
    }
    root['formatVersion'] = formatVersion;
    return _restoreRows(
      db, root, declarations: declarations,
      weightRows: weightRows, restoreWeights: store != null,
    );
  }

  static Future<void> _restoreRows(
    AppDatabase db,
    Map<String, dynamic> root, {
    List<Map<String, dynamic>> declarations = const [],
    List<Map<String, dynamic>> weightRows = const [],
    bool restoreWeights = false,
  }) async {

    if (root['formatVersion'] != formatVersion) {
      throw FormatException(
        'Unsupported backup formatVersion: ${root['formatVersion']}',
      );
    }
    final legacyV10 = db.patientVaultScope == null &&
        root['schemaVersion'] == 10 && db.schemaVersion == 11;
    final scopedV10 = db.patientVaultScope != null &&
        root['schemaVersion'] == 10 && db.schemaVersion == 11 &&
        declarations.isEmpty;
    final scopedV11 = db.patientVaultScope != null &&
        root['schemaVersion'] == 11 && db.schemaVersion == 12;
    if (root['schemaVersion'] != db.schemaVersion &&
        !legacyV10 && !scopedV10 && !scopedV11) {
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

    if (profiles.length > 1) {
      throw StateError('Backup contains ambiguous multiple patient profiles.');
    }
    // Old restore must not erase data belonging to another recorded owner.
    final existing = await db.select(db.patientProfiles).get();
    if (existing.length > 1 ||
        (existing.isNotEmpty &&
            (profiles.isEmpty ||
                existing.single.userId != profiles.single.userId))) {
      throw StateError('Restore owner mismatch; original data preserved.');
    }

    await db.transaction(() async {
      await db.customStatement('DELETE FROM patient_treatment_declarations_v1');
      if (restoreWeights) {
        await db.customStatement('DELETE FROM patient_weight_observations_v1');
      }
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
      for (final row in declarations) {
        await db.customStatement('''
          INSERT INTO patient_treatment_declarations_v1
            (user_id, declaration_state, codes_json,
             declaration_version, provenance, updated_at_utc,
             sync_status, base_server_updated_at, local_generation)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
          row['user_id'], row['declaration_state'], row['codes_json'],
          row['declaration_version'], row['provenance'], row['updated_at_utc'],
          row['sync_status'], row['base_server_updated_at'],
          row['local_generation'],
        ]);
      }
      for (final row in weightRows) {
        await db.customStatement('''
          INSERT INTO patient_weight_observations_v1
            (user_id, client_uuid, value_hundredths, unit,
             kilograms_hundredths, measured_at_utc, provenance)
          VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
          row['user_id'], row['client_uuid'], row['value_hundredths'],
          row['unit'], row['kilograms_hundredths'], row['measured_at_utc'],
          row['provenance'],
        ]);
      }
      if (restoreWeights) {
        final restored = await db.customSelect('''
          SELECT COUNT(*) AS total FROM patient_weight_observations_v1
        ''').getSingle();
        if (restored.data['total'] != weightRows.length) {
          throw StateError('D18 restored weight count mismatch');
        }
      }

      final newDeclarations = await db.customSelect(
        'SELECT user_id FROM patient_treatment_declarations_v1',
      ).get();
      if (newDeclarations.length != declarations.length) {
        throw StateError('D7 backup declaration row count mismatch');
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

  static void _validatedTreatmentDeclarationRow(Map<String, dynamic> row) {
    try {
      if (row['user_id'] is! int || (row['user_id'] as int) <= 0 ||
          row['declaration_version'] != 1 ||
          row['provenance'] != 'patient_declared' ||
          row['updated_at_utc'] is! String ||
          !const {'pending', 'confirmed', 'conflict'}
              .contains(row['sync_status']) ||
          row['local_generation'] is! int ||
          (row['local_generation'] as int) < 1) {
        throw const FormatException('Invalid D7 declaration metadata');
      }
      DateTime.parse(row['updated_at_utc'] as String);
      final serverRevision = row['base_server_updated_at'];
      if (serverRevision != null) {
        if (serverRevision is! String ||
            !RegExp(r'(Z|[+-][0-9]{2}:[0-9]{2})$')
                .hasMatch(serverRevision)) {
          throw const FormatException('Invalid D7 CAS revision');
        }
        DateTime.parse(serverRevision);
      }
      if (row['sync_status'] == 'confirmed' && serverRevision == null) {
        throw const FormatException('Confirmed D7 declaration lacks receipt');
      }
      final codes = jsonDecode(row['codes_json'] as String);
      if (codes is! List || codes.any((code) => code is! String)) {
        throw const FormatException('Invalid D7 codes array');
      }
      validatePatientTreatmentDeclarationV1(
        state: row['declaration_state'] as String,
        codes: codes.cast<String>().toList(growable: false),
      );
    } catch (_) {
      throw const FormatException('Invalid D7 declaration record');
    }
  }

  static bool _hasUnownedClinicalRows(Map<String, dynamic> root) =>
      ['logEntries', 'chatMessages', 'medicationEvents', 'reminders']
          .any((table) => _rows(root, table).isNotEmpty);

  static Future<void> _assertExportOwnerScope(AppDatabase db) async {
    if (db.patientVaultScope == null) return;
    final expected = db.activeProfileRowId;
    final profiles = await db.select(db.patientProfiles).get();
    if (profiles.length > 1 ||
        profiles.any((p) => p.userId != expected)) {
      throw StateError('Native vault contains a foreign patient profile');
    }
    if (profiles.isEmpty) {
      final counts = await Future.wait([
        db.select(db.logEntries).get(),
        db.select(db.chatMessages).get(),
        db.select(db.medicationEvents).get(),
        db.select(db.reminders).get(),
      ]);
      if (counts.any((rows) => rows.isNotEmpty)) {
        throw StateError('Unattributed clinical rows cannot be exported');
      }
    }
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
