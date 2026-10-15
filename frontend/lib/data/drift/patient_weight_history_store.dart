import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_vault_scope.dart';

/// D18-B local-first observations. Pure local SQLite: no API calls, no
/// implicit synchronisation, no legacy dataset migration or inferred facts.
final class LocalWeightObservation {
  final int ownerId;
  final String clientUuid;
  final int valueHundredths;
  final String unit;
  final int kilogramsHundredths;
  final DateTime measuredAtUtc;
  final String provenance;

  const LocalWeightObservation({
    required this.ownerId,
    required this.clientUuid,
    required this.valueHundredths,
    required this.unit,
    required this.kilogramsHundredths,
    required this.measuredAtUtc,
    required this.provenance,
  });
}

/// Never accept a UUID, email, bearer or patient ID from a caller as an owner.
/// The owning row ID comes only from the physically selected scoped vault.
final class PatientWeightHistoryStore {
  final AppDatabase db;

  PatientWeightHistoryStore(this.db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('Clinical weight history requires a real patient vault');
    }
  }

  int get _owner => db.activeProfileRowId;

  static const _uuidV4 = r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$';

  static int _parseHundredths(String input) {
    final v = input.trim();
    if (!RegExp(r'^\d{1,4}(?:\.\d{1,2})?$').hasMatch(v)) {
      throw ArgumentError.value(input, 'value', 'Expected up to two decimals');
    }
    final parts = v.split('.');
    final whole = int.parse(parts[0]);
    final fraction = parts.length == 1
        ? 0
        : int.parse(parts[1].padRight(2, '0'));
    final result = whole * 100 + fraction;
    if (result <= 0 || result > 999999) {
      throw ArgumentError.value(input, 'value', 'Invalid measurement amount');
    }
    return result;
  }

  /// Exact fixed-point conversion, half-up to 0.01 kg, matching Django D18-A.
  static int _toKilogramsHundredths(int value, String unit) {
    if (unit == 'kg') return value;
    if (unit != 'lb') {
      throw ArgumentError.value(unit, 'unit', 'Expected kg or lb');
    }
    final result = (value * 45359237 + 50000000) ~/ 100000000;
    if (result <= 0) {
      throw ArgumentError('Weight rounds to zero kg');
    }
    return result;
  }

  Future<void> _ensureTable() async {
    await db.customStatement('''
      CREATE TABLE IF NOT EXISTS patient_weight_observations_v1 (
        user_id INTEGER NOT NULL,
        client_uuid TEXT NOT NULL,
        value_hundredths INTEGER NOT NULL CHECK (value_hundredths > 0),
        unit TEXT NOT NULL CHECK (unit IN ('kg', 'lb')),
        kilograms_hundredths INTEGER NOT NULL
          CHECK (kilograms_hundredths > 0),
        measured_at_utc TEXT NOT NULL,
        provenance TEXT NOT NULL CHECK (provenance = 'patient_declared'),
        PRIMARY KEY (user_id, client_uuid)
      )
    ''');
    await db.customStatement('''
      CREATE INDEX IF NOT EXISTS patient_weight_obs_owner_time_v1
      ON patient_weight_observations_v1 (user_id, measured_at_utc DESC)
    ''');
  }

  LocalWeightObservation _fromData(Map<String, Object?> row) {
    final at = DateTime.parse(row['measured_at_utc']! as String);
    if (!at.isUtc) throw StateError('Invalid stored weight time zone');
    return LocalWeightObservation(
      ownerId: row['user_id']! as int,
      clientUuid: row['client_uuid']! as String,
      valueHundredths: row['value_hundredths']! as int,
      unit: row['unit']! as String,
      kilogramsHundredths: row['kilograms_hundredths']! as int,
      measuredAtUtc: at,
      provenance: row['provenance']! as String,
    );
  }

  Future<LocalWeightObservation> append({
    required String clientUuid,
    required String value,
    required String unit,
    required DateTime measuredAtUtc,
  }) async {
    final id = clientUuid.toLowerCase();
    if (!RegExp(_uuidV4).hasMatch(id)) {
      throw ArgumentError.value(clientUuid, 'clientUuid', 'UUIDv4 required');
    }
    if (!measuredAtUtc.isUtc ||
        measuredAtUtc.isAfter(
          DateTime.now().toUtc().add(const Duration(minutes: 5)),
        )) {
      throw ArgumentError.value(measuredAtUtc, 'measuredAtUtc',
          'UTC timestamp cannot be in the future');
    }
    final original = _parseHundredths(value);
    final metric = _toKilogramsHundredths(original, unit);
    await _ensureTable();
    return db.transaction(() async {
      final owner = _owner;
      if (await db.getProfileForLocalUserId(owner) == null) {
        throw StateError('No patient-owned profile in selected vault');
      }
      await db.customStatement('''
        INSERT INTO patient_weight_observations_v1
          (user_id, client_uuid, value_hundredths, unit,
           kilograms_hundredths, measured_at_utc, provenance)
        VALUES (?, ?, ?, ?, ?, ?, 'patient_declared')
        ON CONFLICT(user_id, client_uuid) DO NOTHING
      ''', [
        owner, id, original, unit, metric, measuredAtUtc.toIso8601String(),
      ]);
      final rows = await db.customSelect('''
        SELECT user_id, client_uuid, value_hundredths, unit,
               kilograms_hundredths, measured_at_utc, provenance
        FROM patient_weight_observations_v1
        WHERE user_id = ? AND client_uuid = ?
      ''', variables: [Variable<int>(owner), Variable<String>(id)]).get();
      if (rows.length != 1) throw StateError('Failed to persist weight');
      final existing = _fromData(rows.single.data);
      if (existing.valueHundredths != original ||
          existing.unit != unit ||
          existing.kilogramsHundredths != metric ||
          existing.measuredAtUtc != measuredAtUtc ||
          existing.provenance != 'patient_declared') {
        throw StateError('D18 weight UUID conflict; history not overwritten');
      }
      return existing;
    });
  }

  Future<List<LocalWeightObservation>> recent({int limit = 100}) async {
    if (limit < 1 || limit > 200) throw ArgumentError.value(limit, 'limit');
    await _ensureTable();
    final rows = await db.customSelect('''
      SELECT user_id, client_uuid, value_hundredths, unit,
             kilograms_hundredths, measured_at_utc, provenance
      FROM patient_weight_observations_v1
      WHERE user_id = ?
      ORDER BY measured_at_utc DESC, client_uuid DESC LIMIT ?
    ''', variables: [Variable<int>(_owner), Variable<int>(limit)]).get();
    return rows.map((row) => _fromData(row.data)).toList(growable: false);
  }

  /// A read-only export for a later versioned, owner-verified local backup.
  /// Nothing is automatically uploaded or copied out of the selected vault.
  Future<void> prepareBackupTable() => _ensureTable();

  /// Fail closed if a damaged physical vault holds an additional owner's
  /// rows; filtering the export query alone would hide that contamination.
  Future<List<Map<String, Object?>>> exportOwnedRows() async {
    await _ensureTable();
    final foreign = await db.customSelect('''
      SELECT user_id FROM patient_weight_observations_v1
      WHERE user_id <> ? LIMIT 1
    ''', variables: [Variable<int>(_owner)]).get();
    if (foreign.isNotEmpty) {
      throw StateError('Foreign weight data inside patient vault');
    }
    final rows = await db.customSelect('''
      SELECT user_id, client_uuid, value_hundredths, unit,
             kilograms_hundredths, measured_at_utc, provenance
      FROM patient_weight_observations_v1 WHERE user_id = ?
      ORDER BY measured_at_utc DESC, client_uuid DESC
    ''', variables: [Variable<int>(_owner)]).get();
    return [for (final row in rows) Map<String, Object?>.from(row.data)];
  }

  /// Validate the complete untrusted backup row BEFORE destructive restore.
  static void validateBackupRow(Map<String, dynamic> row, int owner) {
    const fields = {
      'user_id', 'client_uuid', 'value_hundredths', 'unit',
      'kilograms_hundredths', 'measured_at_utc', 'provenance',
    };
    if (row.keys.toSet().difference(fields).isNotEmpty ||
        fields.difference(row.keys.toSet()).isNotEmpty ||
        row['user_id'] != owner ||
        row['client_uuid'] is! String ||
        !RegExp(_uuidV4).hasMatch(row['client_uuid'] as String) ||
        row['value_hundredths'] is! int ||
        row['kilograms_hundredths'] is! int ||
        row['unit'] is! String ||
        row['measured_at_utc'] is! String ||
        row['provenance'] != 'patient_declared') {
      throw const FormatException('Invalid D18 weight backup row');
    }
    try {
      final hundredths = row['value_hundredths'] as int;
      if (hundredths <= 0 || hundredths > 999999 ||
          _toKilogramsHundredths(hundredths, row['unit'] as String) !=
              row['kilograms_hundredths']) {
        throw const FormatException('Inconsistent D18 weight units');
      }
      final at = DateTime.parse(row['measured_at_utc'] as String);
      if (!at.isUtc) throw const FormatException('Non-UTC D18 measurement');
    } catch (_) {
      throw const FormatException('Invalid D18 measurement backup');
    }
  }
}
