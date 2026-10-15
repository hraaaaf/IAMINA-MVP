import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_vault_scope.dart';

const d18GenderIdentityCodes = {
  'woman', 'man', 'non_binary', 'another_identity', 'prefer_not_to_say',
};

/// Optional self-reported facts only. NULL means not declared or cleared.
/// A birth year never implies a specific day/month of birth or an age today.
final class LocalProgressiveDemographics {
  final int ownerId;
  final int? birthYear;
  final String? genderIdentity;
  final String provenance;
  final DateTime updatedAtUtc;

  const LocalProgressiveDemographics({
    required this.ownerId,
    required this.birthYear,
    required this.genderIdentity,
    required this.provenance,
    required this.updatedAtUtc,
  });
}

final class PatientProgressiveDemographicsStore {
  final AppDatabase db;

  PatientProgressiveDemographicsStore(this.db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D18 demographics require a real patient vault');
    }
  }

  int get _owner => db.activeProfileRowId;

  static void _validateYear(int? year) {
    if (year != null && (year < 1900 || year > DateTime.now().toUtc().year)) {
      throw ArgumentError.value(year, 'birthYear', 'Year outside supported range');
    }
  }

  static void _validateIdentity(String? identity) {
    if (identity != null && !d18GenderIdentityCodes.contains(identity)) {
      throw ArgumentError.value(identity, 'genderIdentity', 'Unknown declaration');
    }
  }

  Future<void> _ensureTable() async {
    await db.customStatement('''
      CREATE TABLE IF NOT EXISTS patient_progressive_demographics_v1 (
        user_id INTEGER NOT NULL PRIMARY KEY,
        birth_year INTEGER CHECK (birth_year IS NULL
          OR (birth_year >= 1900 AND birth_year <= 9999)),
        gender_identity TEXT CHECK (gender_identity IS NULL
          OR gender_identity IN
            ('woman', 'man', 'non_binary', 'another_identity', 'prefer_not_to_say')),
        provenance TEXT NOT NULL CHECK (provenance = 'patient_declared'),
        updated_at_utc TEXT NOT NULL
      )
    ''');
  }

  Future<void> prepareBackupTable() => _ensureTable();

  LocalProgressiveDemographics _fromRow(Map<String, Object?> data) {
    final at = DateTime.parse(data['updated_at_utc']! as String);
    if (!at.isUtc) throw StateError('Stored profile timestamp must be UTC');
    return LocalProgressiveDemographics(
      ownerId: data['user_id']! as int,
      birthYear: data['birth_year'] as int?,
      genderIdentity: data['gender_identity'] as String?,
      provenance: data['provenance']! as String,
      updatedAtUtc: at,
    );
  }

  Future<LocalProgressiveDemographics?> read() async {
    await _ensureTable();
    final rows = await db.customSelect('''
      SELECT user_id, birth_year, gender_identity, provenance, updated_at_utc
      FROM patient_progressive_demographics_v1 WHERE user_id = ?
    ''', variables: [Variable<int>(_owner)]).get();
    if (rows.isEmpty) return null;
    if (rows.length != 1) throw StateError('Ambiguous D18 demographics');
    return _fromRow(rows.single.data);
  }

  /// Explicitly mark each field being edited. A missing field must never
  /// overwrite an already saved answer with null.
  Future<LocalProgressiveDemographics> update({
    bool updateBirthYear = false,
    int? birthYear,
    bool updateGenderIdentity = false,
    String? genderIdentity,
  }) async {
    if (!updateBirthYear && !updateGenderIdentity) {
      throw ArgumentError('At least one explicit patient update is required');
    }
    if (updateBirthYear) _validateYear(birthYear);
    if (updateGenderIdentity) _validateIdentity(genderIdentity);
    await _ensureTable();
    return db.transaction(() async {
      final owner = _owner;
      if (await db.getProfileForLocalUserId(owner) == null) {
        throw StateError('No patient-owned profile in selected vault');
      }
      final previous = await read();
      final year = updateBirthYear ? birthYear : previous?.birthYear;
      final identity =
          updateGenderIdentity ? genderIdentity : previous?.genderIdentity;
      final now = DateTime.now().toUtc().toIso8601String();
      await db.customStatement('''
        INSERT INTO patient_progressive_demographics_v1
          (user_id, birth_year, gender_identity, provenance, updated_at_utc)
        VALUES (?, ?, ?, 'patient_declared', ?)
        ON CONFLICT(user_id) DO UPDATE SET
          birth_year = excluded.birth_year,
          gender_identity = excluded.gender_identity,
          provenance = excluded.provenance,
          updated_at_utc = excluded.updated_at_utc
      ''', [owner, year, identity, now]);
      final result = await read();
      if (result == null) throw StateError('D18 demographics not persisted');
      return result;
    });
  }

  Future<List<Map<String, Object?>>> exportOwnedRows() async {
    await _ensureTable();
    final foreign = await db.customSelect('''
      SELECT user_id FROM patient_progressive_demographics_v1
      WHERE user_id <> ? LIMIT 1
    ''', variables: [Variable<int>(_owner)]).get();
    if (foreign.isNotEmpty) {
      throw StateError('Foreign demographics inside patient vault');
    }
    final rows = await db.customSelect('''
      SELECT user_id, birth_year, gender_identity, provenance, updated_at_utc
      FROM patient_progressive_demographics_v1 WHERE user_id = ?
    ''', variables: [Variable<int>(_owner)]).get();
    return [for (final row in rows) Map<String, Object?>.from(row.data)];
  }

  static void validateBackupRow(Map<String, dynamic> row, int owner) {
    const fields = {
      'user_id', 'birth_year', 'gender_identity', 'provenance', 'updated_at_utc',
    };
    if (row.keys.toSet().difference(fields).isNotEmpty ||
        fields.difference(row.keys.toSet()).isNotEmpty ||
        row['user_id'] != owner ||
        row['provenance'] != 'patient_declared' ||
        row['updated_at_utc'] is! String ||
        (row['birth_year'] != null && row['birth_year'] is! int) ||
        (row['gender_identity'] != null && row['gender_identity'] is! String)) {
      throw const FormatException('Invalid D18 demographics backup');
    }
    try {
      _validateYear(row['birth_year'] as int?);
      _validateIdentity(row['gender_identity'] as String?);
      final updatedAt = DateTime.parse(row['updated_at_utc'] as String);
      if (!updatedAt.isUtc) throw const FormatException('Non-UTC D18 profile');
    } catch (_) {
      throw const FormatException('Invalid D18 patient declaration');
    }
  }
}
