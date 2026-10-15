import 'package:drift/drift.dart';

import 'database.dart';
import 'patient_vault_scope.dart';
import 'patient_weight_history_store.dart';
import 'patient_weight_notice_delivery_ledger.dart';
import 'patient_weight_notice_preferences_store.dart';
import '../../features/profile/weight_notice_policy.dart';
import '../../features/profile/weight_trend_snapshot.dart';

/// D20-G: a *local preflight* for a previously reserved descriptive notice.
///
/// No scheduler, OS transport, in-app bell, send or network calls. A successful
/// result is NOT evidence of delivery, and is not permission to ship notices.
/// When an approved OS adapter exists it must check its current OS permission,
/// selected patient-vault identity and this preflight immediately at dispatch.
final class PatientWeightNoticeDispatchPreflight {
  final AppDatabase db;

  PatientWeightNoticeDispatchPreflight(this.db) {
    final scope = db.patientVaultScope;
    if (scope == null ||
        scope.databaseName == PatientVaultScope.auditOnly().databaseName) {
      throw StateError('D20 dispatch preflight requires a patient vault');
    }
  }

  /// False on revoked/replaced consent, another patient, stale/replaced
  /// measurements, missing/changed reservation, denied OS permission,
  /// unconfigured policy, or invalid time bounds.
  ///
  /// All reads are performed against the *selected vault* in one SQLite
  /// transaction, to avoid accidentally mixing source and consent snapshots.
  /// This cannot eliminate a race with a future OS send outside this method.
  Future<bool> check({
    required LocalWeightNoticeReservation reservation,
    required bool osNotificationPermission,
    required DateTime nowUtc,
  }) async {
    if (!nowUtc.isUtc) {
      throw ArgumentError.value(nowUtc, 'nowUtc', 'UTC required');
    }
    if (!osNotificationPermission ||
        reservation.ownerId != db.activeProfileRowId ||
        !reservation.reservedAtUtc.isUtc ||
        reservation.reservedAtUtc.isAfter(nowUtc)) {
      return false;
    }

    return db.transaction(() async {
      final owner = db.activeProfileRowId;
      if (owner <= 0 || owner != reservation.ownerId ||
          await db.getProfileForLocalUserId(owner) == null) {
        return false;
      }

      final consent = await PatientWeightNoticePreferencesStore(db).read();
      final consentTime = consent.consentedAtUtc;
      if (!consent.enabled || consentTime == null ||
          !consentTime.isUtc ||
          consentTime.isAfter(reservation.reservedAtUtc) ||
          consentTime.isAfter(nowUtc)) {
        return false;
      }

      final rows = await db.customSelect('''
        SELECT latest_evidence_id, baseline_evidence_id,
               delta_kg_hundredths, baseline_at_utc, latest_at_utc,
               reserved_at_utc
        FROM patient_weight_notice_reservations_v1
        WHERE user_id = ? AND latest_evidence_id = ?
      ''', variables: [
        Variable<int>(owner),
        Variable<String>(reservation.latestEvidenceId),
      ]).get();
      if (rows.length != 1) return false;
      final data = rows.single.data;
      if (data['baseline_evidence_id'] != reservation.baselineEvidenceId ||
          data['delta_kg_hundredths'] != reservation.deltaKgHundredths ||
          data['baseline_at_utc'] != reservation.baselineAtUtc.toIso8601String() ||
          data['latest_at_utc'] != reservation.latestAtUtc.toIso8601String() ||
          data['reserved_at_utc'] != reservation.reservedAtUtc.toIso8601String()) {
        return false;
      }

      final history = await PatientWeightHistoryStore(db).recent(limit: 200);
      final current = LocalWeightTrendSnapshot.fromObservations(
        history, asOfUtc: nowUtc,
      );
      if (current == null ||
          current.ownerId != owner ||
          current.latestEvidenceId != reservation.latestEvidenceId ||
          current.baselineEvidenceId != reservation.baselineEvidenceId ||
          current.deltaKgHundredths != reservation.deltaKgHundredths ||
          current.latestAtUtc != reservation.latestAtUtc ||
          current.baselineAtUtc != reservation.baselineAtUtc) {
        return false;
      }
      if (current.latestAtUtc.isBefore(consentTime)) return false;

      // Re-check today's policy and freshness, but not previous-reservation
      // dedup, since the candidate being checked *is* that reservation.
      final eligible = evaluateLocalWeightNotice(
        trend: current,
        policy: consent.policy,
        osNotificationPermission: osNotificationPermission,
        nowUtc: nowUtc,
      );
      return eligible != null &&
          eligible.latestEvidenceId == reservation.latestEvidenceId;
    });
  }
}
