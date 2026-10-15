import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_vault_scope.dart';
import '../../features/profile/weight_notice_policy.dart';

/// D20-C: consent recorded ONLY by an explicit local patient interaction.
/// This store never requests OS permission, sends/schedules notifications,
/// makes HTTP/LLM calls, or decides whether a weight change is dangerous.
final class LocalWeightNoticePreferences {
  final bool enabled;
  final int? minimumChangeKgHundredths;
  final Duration? minimumSpan;
  final Duration? maximumLatestAge;
  final Duration? minimumSpacing;
  final DateTime? consentedAtUtc;

  const LocalWeightNoticePreferences.disabled()
      : enabled = false,
        minimumChangeKgHundredths = null,
        minimumSpan = null,
        maximumLatestAge = null,
        minimumSpacing = null,
        consentedAtUtc = null;

  const LocalWeightNoticePreferences._({
    required this.minimumChangeKgHundredths,
    required this.minimumSpan,
    required this.maximumLatestAge,
    required this.minimumSpacing,
    required this.consentedAtUtc,
  }) : enabled = true;

  LocalWeightNoticePolicy get policy => LocalWeightNoticePolicy(
    enabled: enabled,
    minimumAbsoluteChangeKgHundredths: minimumChangeKgHundredths,
    minimumMeasurementSpan: minimumSpan,
    maximumLatestReadingAge: maximumLatestAge,
    minimumNoticeSpacing: minimumSpacing,
  );
}

/// Opt-in belongs to the *physically selected* native patient SQLite vault,
/// not a caller-supplied user ID or a global preference store.
final class PatientWeightNoticePreferencesStore {
  final AppDatabase db;

  PatientWeightNoticePreferencesStore(this.db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D20 preferences require a real patient vault');
    }
  }

  int get _owner => db.activeProfileRowId;

  Future<void> _ensureTable() async {
    await db.customStatement('''
      CREATE TABLE IF NOT EXISTS patient_weight_notice_preferences_v1 (
        user_id INTEGER NOT NULL PRIMARY KEY,
        enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
        min_change_kg_hundredths INTEGER NOT NULL
          CHECK (min_change_kg_hundredths > 0),
        min_span_seconds INTEGER NOT NULL CHECK (min_span_seconds > 0),
        max_age_seconds INTEGER NOT NULL CHECK (max_age_seconds > 0),
        min_spacing_seconds INTEGER NOT NULL CHECK (min_spacing_seconds > 0),
        consented_at_utc TEXT NOT NULL
      )
    ''');
  }

  Future<void> _checkOwner() async {
    if (_owner <= 0 || await db.getProfileForLocalUserId(_owner) == null) {
      throw StateError('Active patient profile required');
    }
    final foreign = await db.customSelect('''
      SELECT user_id FROM patient_weight_notice_preferences_v1
      WHERE user_id <> ? LIMIT 1
    ''', variables: [Variable<int>(_owner)]).get();
    if (foreign.isNotEmpty) {
      throw StateError('Foreign patient notification consent in local vault');
    }
  }

  /// No row is equivalent to explicit OFF; permissions are never inferred from
  /// the operating system or from the existence of a weight history.
  Future<LocalWeightNoticePreferences> read() async {
    await _ensureTable();
    await _checkOwner();
    final rows = await db.customSelect('''
      SELECT enabled, min_change_kg_hundredths, min_span_seconds,
             max_age_seconds, min_spacing_seconds, consented_at_utc
      FROM patient_weight_notice_preferences_v1
      WHERE user_id = ?
    ''', variables: [Variable<int>(_owner)]).get();
    if (rows.isEmpty) return const LocalWeightNoticePreferences.disabled();
    if (rows.length != 1) throw StateError('Ambiguous D20 preference rows');
    final m = rows.single.data;
    if (m['enabled'] != 1) {
      return const LocalWeightNoticePreferences.disabled();
    }
    final threshold = m['min_change_kg_hundredths'];
    final span = m['min_span_seconds'];
    final age = m['max_age_seconds'];
    final spacing = m['min_spacing_seconds'];
    final rawTime = m['consented_at_utc'];
    if (threshold is! int || threshold <= 0 || threshold > 999999 ||
        span is! int || span <= 0 || age is! int || age <= 0 ||
        spacing is! int || spacing <= 0 || rawTime is! String) {
      throw StateError('Corrupt D20 consent preference');
    }
    final consentAt = DateTime.tryParse(rawTime);
    if (consentAt == null || !consentAt.isUtc) {
      throw StateError('D20 consent timestamp not UTC');
    }
    return LocalWeightNoticePreferences._(
      minimumChangeKgHundredths: threshold,
      minimumSpan: Duration(seconds: span),
      maximumLatestAge: Duration(seconds: age),
      minimumSpacing: Duration(seconds: spacing),
      consentedAtUtc: consentAt,
    );
  }

  static int _positiveSeconds(Duration? duration) {
    if (duration == null ||
        duration.inMicroseconds <= 0 ||
        duration.inMicroseconds % Duration.microsecondsPerSecond != 0) {
      throw ArgumentError.value(duration, 'duration',
          'Explicit positive whole-second duration required');
    }
    return duration.inSeconds;
  }

  /// Only an explicit user gesture with a complete user-chosen policy can
  /// persist ON. This does not substitute for a separate OS permission grant.
  Future<void> optIn({
    required bool confirmedByUser,
    required LocalWeightNoticePolicy policy,
    required DateTime consentedAtUtc,
    required DateTime nowUtc,
  }) async {
    if (!confirmedByUser || !policy.enabled ||
        !consentedAtUtc.isUtc || !nowUtc.isUtc ||
        consentedAtUtc.isAfter(nowUtc) ||
        (policy.minimumAbsoluteChangeKgHundredths ?? 0) <= 0 ||
        (policy.minimumAbsoluteChangeKgHundredths ?? 0) > 999999) {
      throw ArgumentError('Explicit consent and complete valid policy required');
    }
    final span = _positiveSeconds(policy.minimumMeasurementSpan);
    final age = _positiveSeconds(policy.maximumLatestReadingAge);
    final spacing = _positiveSeconds(policy.minimumNoticeSpacing);
    await _ensureTable();
    await db.transaction(() async {
      await _checkOwner();
      await db.customStatement('''
        INSERT INTO patient_weight_notice_preferences_v1
          (user_id, enabled, min_change_kg_hundredths, min_span_seconds,
           max_age_seconds, min_spacing_seconds, consented_at_utc)
        VALUES (?, 1, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
          enabled=excluded.enabled,
          min_change_kg_hundredths=excluded.min_change_kg_hundredths,
          min_span_seconds=excluded.min_span_seconds,
          max_age_seconds=excluded.max_age_seconds,
          min_spacing_seconds=excluded.min_spacing_seconds,
          consented_at_utc=excluded.consented_at_utc
      ''', [
        _owner, policy.minimumAbsoluteChangeKgHundredths,
        span, age, spacing, consentedAtUtc.toIso8601String(),
      ]);
    });
  }

  /// Revoke consent locally and erase all configured criteria. An opt-in
  /// cannot be reconstituted from persisted weight rows after a revocation.
  Future<void> optOut() async {
    await _ensureTable();
    await db.transaction(() async {
      await _checkOwner();
      await db.customStatement('''
        DELETE FROM patient_weight_notice_preferences_v1 WHERE user_id = ?
      ''', [_owner]);
    });
  }
}
