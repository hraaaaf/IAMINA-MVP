import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/weight_notice_policy.dart';
import 'package:amina/features/profile/weight_trend_snapshot.dart';
import 'package:flutter_test/flutter_test.dart';

const _firstId = '123e4567-e89b-42d3-a456-426614174000';
const _lastId = '123e4567-e89b-42d3-a456-426614174001';

LocalWeightTrendSnapshot _trend() {
  final rows = [
    LocalWeightObservation(
      ownerId: 41, clientUuid: _firstId, valueHundredths: 7000,
      unit: 'kg', kilogramsHundredths: 7000,
      measuredAtUtc: DateTime.utc(2026, 10, 1),
      provenance: 'patient_declared',
    ),
    LocalWeightObservation(
      ownerId: 41, clientUuid: _lastId, valueHundredths: 7150,
      unit: 'kg', kilogramsHundredths: 7150,
      measuredAtUtc: DateTime.utc(2026, 10, 14),
      provenance: 'patient_declared',
    ),
  ];
  return LocalWeightTrendSnapshot.fromObservations(
    rows, asOfUtc: DateTime.utc(2026, 10, 15),
  )!;
}

const policy = LocalWeightNoticePolicy(
  enabled: true,
  minimumAbsoluteChangeKgHundredths: 100,
  minimumMeasurementSpan: Duration(days: 7),
  maximumLatestReadingAge: Duration(days: 7),
  minimumNoticeSpacing: Duration(days: 4),
);

void main() {
  final now = DateTime.utc(2026, 10, 15);
  test('D20-B default is OFF, even with weight change', () {
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: const LocalWeightNoticePolicy(),
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: false, nowUtc: now,
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: null, policy: policy,
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
  });

  test('D20-B missing user criteria fail closed', () {
    const partial = LocalWeightNoticePolicy(
      enabled: true, minimumAbsoluteChangeKgHundredths: 100,
    );
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: partial,
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
    const zero = LocalWeightNoticePolicy(
      enabled: true,
      minimumAbsoluteChangeKgHundredths: 0,
      minimumMeasurementSpan: Duration(days: 7),
      maximumLatestReadingAge: Duration(days: 7),
      minimumNoticeSpacing: Duration(days: 4),
    );
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: zero,
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
  });

  test('D20-B explicit configured comparison returns source-bound candidate', () {
    final result = evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
    )!;
    expect(result.ownerId, 41);
    expect(result.deltaKgHundredths, 150);
    expect(result.baselineEvidenceId, _firstId);
    expect(result.latestEvidenceId, _lastId);
    expect(result.baselineAtUtc, DateTime.utc(2026, 10, 1));
    expect(result.latestAtUtc, DateTime.utc(2026, 10, 14));
  });

  test('D20-B customizable magnitude and history span are strict gates', () {
    const more = LocalWeightNoticePolicy(
      enabled: true, minimumAbsoluteChangeKgHundredths: 151,
      minimumMeasurementSpan: Duration(days: 7),
      maximumLatestReadingAge: Duration(days: 7),
      minimumNoticeSpacing: Duration(days: 4),
    );
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: more,
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
    const longer = LocalWeightNoticePolicy(
      enabled: true, minimumAbsoluteChangeKgHundredths: 100,
      minimumMeasurementSpan: Duration(days: 14),
      maximumLatestReadingAge: Duration(days: 7),
      minimumNoticeSpacing: Duration(days: 4),
    );
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: longer,
      osNotificationPermission: true, nowUtc: now,
    ), isNull);
  });

  test('D20-B stale or future time prevents candidate', () {
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 11, 1),
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true,
      nowUtc: DateTime.utc(2026, 10, 13),
    ), isNull);
    expect(() => evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true,
      nowUtc: DateTime(2026, 10, 15),
    ), throwsArgumentError);
  });

  test('D20-B evidence de-duplication and notice cooldown fail closed', () {
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
      lastNotifiedEvidenceId: _lastId,
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
      lastNoticeAtUtc: DateTime.utc(2026, 10, 14),
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
      lastNoticeAtUtc: DateTime.utc(2026, 10, 16),
    ), isNull);
    expect(evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
      lastNoticeAtUtc: DateTime(2026, 10, 8),
    ), isNull);
  });

  test('D20-B cooldown completion allows only a descriptive candidate', () {
    final candidate = evaluateLocalWeightNotice(
      trend: _trend(), policy: policy,
      osNotificationPermission: true, nowUtc: now,
      lastNoticeAtUtc: DateTime.utc(2026, 10, 10),
      lastNotifiedEvidenceId: _firstId,
    );
    expect(candidate, isNotNull);
    expect(candidate!.latestEvidenceId, _lastId);
  });
}
