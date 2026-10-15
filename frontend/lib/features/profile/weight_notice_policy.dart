import 'weight_trend_snapshot.dart';

/// D20-B pure eligibility: it cannot send, schedule or store a notification.
/// All criteria are explicit user choices; the default is always OFF.
final class LocalWeightNoticePolicy {
  final bool enabled;
  final int? minimumAbsoluteChangeKgHundredths;
  final Duration? minimumMeasurementSpan;
  final Duration? maximumLatestReadingAge;
  final Duration? minimumNoticeSpacing;

  const LocalWeightNoticePolicy({
    this.enabled = false,
    this.minimumAbsoluteChangeKgHundredths,
    this.minimumMeasurementSpan,
    this.maximumLatestReadingAge,
    this.minimumNoticeSpacing,
  });
}

/// Descriptive candidate only; no medical-risk score or notification transport.
final class LocalWeightNoticeCandidate {
  final int ownerId;
  final int deltaKgHundredths;
  final DateTime baselineAtUtc;
  final DateTime latestAtUtc;
  final String baselineEvidenceId;
  final String latestEvidenceId;

  LocalWeightNoticeCandidate._(LocalWeightTrendSnapshot trend)
      : ownerId = trend.ownerId,
        deltaKgHundredths = trend.deltaKgHundredths,
        baselineAtUtc = trend.baselineAtUtc,
        latestAtUtc = trend.latestAtUtc,
        baselineEvidenceId = trend.baselineEvidenceId,
        latestEvidenceId = trend.latestEvidenceId;
}

/// Returns null unless every local, consent and frequency gate is satisfied.
///
/// There is deliberately no default trigger threshold, no implicit consent,
/// no OS push call and no patient data sent to a network service.
LocalWeightNoticeCandidate? evaluateLocalWeightNotice({
  required LocalWeightTrendSnapshot? trend,
  required LocalWeightNoticePolicy policy,
  required bool osNotificationPermission,
  required DateTime nowUtc,
  DateTime? lastNoticeAtUtc,
  String? lastNotifiedEvidenceId,
}) {
  if (!nowUtc.isUtc) {
    throw ArgumentError.value(nowUtc, 'nowUtc', 'UTC required');
  }
  if (!policy.enabled || !osNotificationPermission || trend == null) {
    return null;
  }
  final absoluteMin = policy.minimumAbsoluteChangeKgHundredths;
  final minimumSpan = policy.minimumMeasurementSpan;
  final maximumAge = policy.maximumLatestReadingAge;
  final cooldown = policy.minimumNoticeSpacing;
  if (absoluteMin == null ||
      absoluteMin <= 0 ||
      minimumSpan == null ||
      minimumSpan.inMicroseconds <= 0 ||
      maximumAge == null ||
      maximumAge.inMicroseconds <= 0 ||
      cooldown == null ||
      cooldown.inMicroseconds <= 0) {
    return null;
  }

  final measuredSpan = trend.latestAtUtc.difference(trend.baselineAtUtc);
  final age = nowUtc.difference(trend.latestAtUtc);
  if (!trend.latestAtUtc.isUtc ||
      !trend.baselineAtUtc.isUtc ||
      measuredSpan < minimumSpan ||
      age.isNegative ||
      age > maximumAge ||
      trend.deltaKgHundredths.abs() < absoluteMin ||
      lastNotifiedEvidenceId == trend.latestEvidenceId) {
    return null;
  }
  if (lastNoticeAtUtc != null) {
    if (!lastNoticeAtUtc.isUtc ||
        lastNoticeAtUtc.isAfter(nowUtc) ||
        nowUtc.difference(lastNoticeAtUtc) < cooldown) {
      return null;
    }
  }
  return LocalWeightNoticeCandidate._(trend);
}
