import '../../data/drift/patient_weight_history_store.dart';

/// D20-A: a read-only, descriptive comparison of two patient-declared weights.
///
/// No notifications, user thresholds, BMI, risk labels, advice or model calls.
/// A caller must separately obtain opt-in and approved notification criteria;
/// this type does not expose a method that sends or schedules anything.
final class LocalWeightTrendSnapshot {
  final int ownerId;
  final int baselineKgHundredths;
  final int latestKgHundredths;
  final DateTime baselineAtUtc;
  final DateTime latestAtUtc;
  final String baselineEvidenceId;
  final String latestEvidenceId;

  const LocalWeightTrendSnapshot._({
    required this.ownerId,
    required this.baselineKgHundredths,
    required this.latestKgHundredths,
    required this.baselineAtUtc,
    required this.latestAtUtc,
    required this.baselineEvidenceId,
    required this.latestEvidenceId,
  });

  /// Signed fixed-point change: positive = increased, negative = decreased.
  int get deltaKgHundredths => latestKgHundredths - baselineKgHundredths;

  /// Null means the supplied observations do not justify even a comparison.
  ///
  /// All rows must come from the selected owner, have nonambiguous UTC times,
  /// and be patient declarations. Equal timestamps are ambiguous and fail
  /// closed. No medical or notification sufficiency threshold is inferred.
  static LocalWeightTrendSnapshot? fromObservations(
    List<LocalWeightObservation> rows, {
    required DateTime asOfUtc,
  }) {
    if (!asOfUtc.isUtc) {
      throw ArgumentError.value(asOfUtc, 'asOfUtc', 'UTC required');
    }
    if (rows.length < 2) return null;
    final owner = rows.first.ownerId;
    if (owner <= 0) return null;

    final uniqueIds = <String>{};
    for (final row in rows) {
      if (row.ownerId != owner ||
          !row.measuredAtUtc.isUtc ||
          row.measuredAtUtc.isAfter(asOfUtc) ||
          row.kilogramsHundredths <= 0 ||
          row.valueHundredths <= 0 ||
          (row.unit != 'kg' && row.unit != 'lb') ||
          row.provenance != 'patient_declared' ||
          !uniqueIds.add(row.clientUuid)) {
        return null;
      }
      // Defense in depth against a corrupted/imported normalization.
      final expected = row.unit == 'kg'
          ? row.valueHundredths
          : (row.valueHundredths * 45359237 + 50000000) ~/ 100000000;
      if (row.kilogramsHundredths != expected) return null;
    }

    final chronological = List<LocalWeightObservation>.of(rows)
      ..sort((a, b) => a.measuredAtUtc.compareTo(b.measuredAtUtc));
    for (var i = 1; i < chronological.length; i++) {
      if (!chronological[i].measuredAtUtc.isAfter(
        chronological[i - 1].measuredAtUtc,
      )) {
        return null;
      }
    }

    final baseline = chronological.first;
    final latest = chronological.last;
    return LocalWeightTrendSnapshot._(
      ownerId: owner,
      baselineKgHundredths: baseline.kilogramsHundredths,
      latestKgHundredths: latest.kilogramsHundredths,
      baselineAtUtc: baseline.measuredAtUtc,
      latestAtUtc: latest.measuredAtUtc,
      baselineEvidenceId: baseline.clientUuid,
      latestEvidenceId: latest.clientUuid,
    );
  }
}
