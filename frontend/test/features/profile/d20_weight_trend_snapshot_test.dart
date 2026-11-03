import 'package:amina/data/drift/patient_weight_history_store.dart';
import 'package:amina/features/profile/weight_trend_snapshot.dart';
import 'package:flutter_test/flutter_test.dart';

const _uuidA = '123e4567-e89b-42d3-a456-426614174000';
const _uuidB = '123e4567-e89b-42d3-a456-426614174001';
const _uuidC = '123e4567-e89b-42d3-a456-426614174002';

LocalWeightObservation _row({
  int owner = 73,
  String uuid = _uuidA,
  int weight = 7000,
  int? value,
  String unit = 'kg',
  DateTime? at,
  String provenance = 'patient_declared',
}) => LocalWeightObservation(
  ownerId: owner,
  clientUuid: uuid,
  valueHundredths: value ?? weight,
  unit: unit,
  kilogramsHundredths: weight,
  measuredAtUtc: at ?? DateTime.utc(2026, 10, 11),
  provenance: provenance,
);

void main() {
  final asOf = DateTime.utc(2026, 10, 16);

  test('D20 missing and single sample have no descriptive trend', () {
    expect(LocalWeightTrendSnapshot.fromObservations(
      const [], asOfUtc: asOf,
    ), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations(
      [_row()], asOfUtc: asOf,
    ), isNull);
  });

  test('D20 pure comparison sorts timestamps and keeps provenance', () {
    final later = _row(uuid: _uuidB, weight: 7150,
        at: DateTime.utc(2026, 10, 15));
    final earlier = _row(uuid: _uuidA, weight: 7000,
        at: DateTime.utc(2026, 10, 11));
    final result = LocalWeightTrendSnapshot.fromObservations(
      [later, earlier], asOfUtc: asOf,
    )!;
    expect(result.ownerId, 73);
    expect(result.baselineKgHundredths, 7000);
    expect(result.latestKgHundredths, 7150);
    expect(result.deltaKgHundredths, 150);
    expect(result.baselineEvidenceId, _uuidA);
    expect(result.latestEvidenceId, _uuidB);
    expect(result.baselineAtUtc, DateTime.utc(2026, 10, 11));
    expect(result.latestAtUtc, DateTime.utc(2026, 10, 15));
  });

  test('D20 never mixes patient vaults or accepts future readings', () {
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(), _row(owner: 74, uuid: _uuidB),
    ], asOfUtc: asOf), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(), _row(uuid: _uuidB, at: DateTime.utc(2026, 10, 17)),
    ], asOfUtc: asOf), isNull);
    expect(() => LocalWeightTrendSnapshot.fromObservations([
      _row(), _row(uuid: _uuidB),
    ], asOfUtc: DateTime(2026, 10, 16)), throwsArgumentError);
  });

  test('D20 ambiguous timestamps or duplicate UUIDs fail closed', () {
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(), _row(uuid: _uuidB, weight: 7200),
    ], asOfUtc: asOf), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(), _row(weight: 7200, at: DateTime.utc(2026, 10, 15)),
    ], asOfUtc: asOf), isNull);
  });

  test('D20 normalizes lb and kg without floating-point unit drift', () {
    final result = LocalWeightTrendSnapshot.fromObservations([
      _row(value: 15500, unit: 'lb', weight: 7031),
      _row(uuid: _uuidB, value: 7200, unit: 'kg', weight: 7200,
          at: DateTime.utc(2026, 10, 15)),
    ], asOfUtc: asOf)!;
    expect(result.deltaKgHundredths, 169);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(value: 15500, unit: 'lb', weight: 7000),
      _row(uuid: _uuidB, at: DateTime.utc(2026, 10, 15)),
    ], asOfUtc: asOf), isNull);
  });

  test('D20 invalid provenance and corrupted data never emit comparison', () {
    final latest = _row(uuid: _uuidB, at: DateTime.utc(2026, 10, 15));
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(provenance: 'external_unknown'), latest,
    ], asOfUtc: asOf), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(weight: 0, value: 0), latest,
    ], asOfUtc: asOf), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(owner: 0), _row(owner: 0, uuid: _uuidB,
          at: DateTime.utc(2026, 10, 15)),
    ], asOfUtc: asOf), isNull);
    expect(LocalWeightTrendSnapshot.fromObservations([
      _row(uuid: _uuidC, at: DateTime(2026, 10, 11)),
      latest,
    ], asOfUtc: asOf), isNull);
  });

  test('D20 negative signed delta stays descriptive, not a diagnosis', () {
    final result = LocalWeightTrendSnapshot.fromObservations([
      _row(weight: 7100),
      _row(uuid: _uuidB, weight: 7000,
          at: DateTime.utc(2026, 10, 15)),
    ], asOfUtc: asOf)!;
    expect(result.deltaKgHundredths, -100);
  });
}
