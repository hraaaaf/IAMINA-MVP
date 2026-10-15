import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_vault_scope.dart';
import 'patient_weight_history_store.dart';
import 'patient_weight_notice_preferences_store.dart';
import '../../features/profile/weight_notice_policy.dart';
import '../../features/profile/weight_trend_snapshot.dart';

/// A durable local *reservation*, not a sent, scheduled or delivered notice.
/// A later OS transport adapter must be certified separately; no such adapter
/// exists here. Reserving before transport prevents duplicate attempts.
final class LocalWeightNoticeReservation {
  final int ownerId;
  final String baselineEvidenceId;
  final String latestEvidenceId;
  final int deltaKgHundredths;
  final DateTime baselineAtUtc;
  final DateTime latestAtUtc;
  final DateTime reservedAtUtc;

  const LocalWeightNoticeReservation._({
    required this.ownerId,
    required this.baselineEvidenceId,
    required this.latestEvidenceId,
    required this.deltaKgHundredths,
    required this.baselineAtUtc,
    required this.latestAtUtc,
    required this.reservedAtUtc,
  });
}

/// D20-D: atomic, per-vault duplicate protection for an eligible candidate.
///
/// Source facts come from the active patient SQLite weight history; opt-in is
/// fetched from the same vault. The ledger NEVER calls OS notifications, HTTP
/// or an LLM. Pending reservations are intentionally not retried after a
/// crash; fail-closed is preferable to repeating health-related notices.
final class PatientWeightNoticeDeliveryLedger {
  final AppDatabase db;

  PatientWeightNoticeDeliveryLedger(this.db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D20 ledger requires a real patient vault');
    }
  }

  int get _owner => db.activeProfileRowId;

  Future<void> _ensureTable() => db.customStatement('''
    CREATE TABLE IF NOT EXISTS patient_weight_notice_reservations_v1 (
      user_id INTEGER NOT NULL,
      latest_evidence_id TEXT NOT NULL,
      baseline_evidence_id TEXT NOT NULL,
      delta_kg_hundredths INTEGER NOT NULL,
      baseline_at_utc TEXT NOT NULL,
      latest_at_utc TEXT NOT NULL,
      reserved_at_utc TEXT NOT NULL,
      PRIMARY KEY (user_id, latest_evidence_id)
    )
  ''');

  Future<void> _assertOwner() async {
    if (_owner <= 0 || await db.getProfileForLocalUserId(_owner) == null) {
      throw StateError('Active patient profile required');
    }
    final foreign = await db.customSelect('''
      SELECT user_id FROM patient_weight_notice_reservations_v1
      WHERE user_id <> ? LIMIT 1
    ''', variables: [Variable<int>(_owner)]).get();
    if (foreign.isNotEmpty) {
      throw StateError('Foreign weight notice reservation in patient vault');
    }
  }

  /// Creates a durable reservation only when *current* local evidence, current
  /// explicit opt-in, OS permission and user criteria all agree. The time
  /// spacing is measured from prior reservations (conservative), not from a
  /// spoofable caller-provided "last notice" time.
  Future<LocalWeightNoticeReservation?> reserveIfEligible({
    required bool osNotificationPermission,
    required DateTime nowUtc,
  }) async {
    if (!nowUtc.isUtc) {
      throw ArgumentError.value(nowUtc, 'nowUtc', 'UTC required');
    }
    if (!osNotificationPermission) return null;
    await _ensureTable();

    return db.transaction(() async {
      await _assertOwner();
      final preference = await PatientWeightNoticePreferencesStore(db).read();
      if (!preference.enabled ||
          preference.consentedAtUtc == null ||
          preference.consentedAtUtc!.isAfter(nowUtc)) {
        return null;
      }

      final readings = await PatientWeightHistoryStore(db).recent(limit: 200);
      final trend = LocalWeightTrendSnapshot.fromObservations(
        readings, asOfUtc: nowUtc,
      );
      if (trend == null || trend.ownerId != _owner) return null;
      // Consent is prospective: an old measurement must not create a
      // newly eligible notice simply because the patient turns the switch ON.
      if (trend.latestAtUtc.isBefore(preference.consentedAtUtc!)) {
        return null;
      }

      final recent = await db.customSelect('''
        SELECT latest_evidence_id, reserved_at_utc
        FROM patient_weight_notice_reservations_v1 WHERE user_id = ?
        ORDER BY reserved_at_utc DESC LIMIT 1
      ''', variables: [Variable<int>(_owner)]).get();
      String? lastEvidence;
      DateTime? lastAt;
      if (recent.isNotEmpty) {
        lastEvidence = recent.single.read<String>('latest_evidence_id');
        lastAt = DateTime.tryParse(
          recent.single.read<String>('reserved_at_utc'),
        );
        if (lastAt == null || !lastAt.isUtc) {
          throw StateError('Corrupt D20 reservation time');
        }
      }

      final candidate = evaluateLocalWeightNotice(
        trend: trend,
        policy: preference.policy,
        osNotificationPermission: osNotificationPermission,
        nowUtc: nowUtc,
        lastNoticeAtUtc: lastAt,
        lastNotifiedEvidenceId: lastEvidence,
      );
      if (candidate == null) return null;

      // Retain uniqueness for every historical evidence ID, not just the
      // immediately previous one; a stale retry never creates another claim.
      final existing = await db.customSelect('''
        SELECT latest_evidence_id FROM patient_weight_notice_reservations_v1
        WHERE user_id = ? AND latest_evidence_id = ?
      ''', variables: [
        Variable<int>(_owner), Variable<String>(candidate.latestEvidenceId),
      ]).get();
      if (existing.isNotEmpty) return null;

      await db.customStatement('''
        INSERT INTO patient_weight_notice_reservations_v1
          (user_id, latest_evidence_id, baseline_evidence_id,
           delta_kg_hundredths, baseline_at_utc, latest_at_utc,
           reserved_at_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      ''', [
        _owner, candidate.latestEvidenceId, candidate.baselineEvidenceId,
        candidate.deltaKgHundredths,
        candidate.baselineAtUtc.toIso8601String(),
        candidate.latestAtUtc.toIso8601String(),
        nowUtc.toIso8601String(),
      ]);
      return LocalWeightNoticeReservation._(
        ownerId: _owner,
        baselineEvidenceId: candidate.baselineEvidenceId,
        latestEvidenceId: candidate.latestEvidenceId,
        deltaKgHundredths: candidate.deltaKgHundredths,
        baselineAtUtc: candidate.baselineAtUtc,
        latestAtUtc: candidate.latestAtUtc,
        reservedAtUtc: nowUtc,
      );
    });
  }

  /// The count is only reservations, never a count of delivered notifications.
  Future<int> reservationCount() async {
    await _ensureTable();
    await _assertOwner();
    final row = await db.customSelect('''
      SELECT COUNT(*) AS n FROM patient_weight_notice_reservations_v1
      WHERE user_id = ?
    ''', variables: [Variable<int>(_owner)]).getSingle();
    return row.read<int>('n');
  }
}
