import 'package:amina/core/utils/glucose_formatter.dart';
import 'package:flutter_test/flutter_test.dart';

/// D22 — NON-PRODUCTION / NON-CLINICAL candidate acceptance oracle only.
///
/// It models the *proposed* fail-closed data contract while D19 G1–G7 are
/// PENDING. No patient-facing code imports these helpers. Passing this test
/// does NOT imply the existing onboarding/profile/dashboard is safe.
enum _ReviewStatus { legacyUnknown, explicitlyVerified }

bool _supported(String unit) => unit == 'mg/dL' || unit == 'mmol/L';

/// A typed, explicitly-reviewed synthetic quantity. No medical threshold
/// is suggested. The authority and source of real targets are D19 decisions.
final class _CandidateRange {
  const _CandidateRange({
    required this.ownerId,
    required this.status,
    required this.sourceUnit,
    required this.lowerMgDl,
    required this.upperMgDl,
    required this.sourceReference,
  });

  final int ownerId;
  final _ReviewStatus status;
  final String? sourceUnit;
  final double? lowerMgDl;
  final double? upperMgDl;
  final String? sourceReference;

  bool get hasAuthority =>
      ownerId > 0 &&
      status == _ReviewStatus.explicitlyVerified &&
      sourceReference != null &&
      sourceReference!.trim().isNotEmpty &&
      sourceUnit != null &&
      _supported(sourceUnit!) &&
      lowerMgDl != null &&
      upperMgDl != null &&
      lowerMgDl!.isFinite &&
      upperMgDl!.isFinite &&
      lowerMgDl! > 0 &&
      upperMgDl! > lowerMgDl!;

  /// This permits *consideration*, not clinical classification. D19 G5
  /// must separately authorize any target relation, boundary inclusivity,
  /// metric or patient-facing label. The oracle never computes in/out target.
  bool canEvaluateForOwner(int owner, double measurementMgDl) =>
      hasAuthority && owner == ownerId && measurementMgDl.isFinite;

  _CandidateRange withDisplayPreference(String requestedUnit) {
    if (!_supported(requestedUnit)) throw ArgumentError.value(requestedUnit);
    // Display preferences must never rewrite a stored target or its evidence.
    return this;
  }
}

void main() {
  group('D22 candidate safety contract — test-only, G1–G7 still pending', () {
    const legacy = _CandidateRange(
      ownerId: 1001,
      status: _ReviewStatus.legacyUnknown,
      sourceUnit: null,
      lowerMgDl: 70,
      upperMgDl: 180,
      sourceReference: null,
    );

    const candidate = _CandidateRange(
      ownerId: 1001,
      status: _ReviewStatus.explicitlyVerified,
      sourceUnit: 'mg/dL',
      lowerMgDl: 91,
      upperMgDl: 147,
      sourceReference: 'synthetic-test-only-authority',
    );

    test('D22 G3: legacy numeric 70/180 is not proof of any target', () {
      expect(legacy.hasAuthority, isFalse);
      expect(legacy.canEvaluateForOwner(1001, 100), isFalse);
      expect(legacy.canEvaluateForOwner(1002, 100), isFalse);
    });

    test('D22 G2: no fabricated authority from unit preference alone', () {
      final preference = legacy.withDisplayPreference('mmol/L');
      expect(preference, same(legacy));
      expect(preference.canEvaluateForOwner(1001, 100), isFalse);
    });

    test('D22 G1/G4: presentation-only conversion leaves raw values alone', () {
      final rawMgDl = <double>[91, 147];
      final original = List<double>.from(rawMgDl);
      final displayed = rawMgDl
          .map((value) => GlucoseFormatter.format(value, 'mmol/L'))
          .toList();
      expect(displayed, everyElement(endsWith(' mmol/L')));
      expect(rawMgDl, original);
      expect(candidate.withDisplayPreference('mmol/L'), same(candidate));
      expect(candidate.lowerMgDl, 91);
      expect(candidate.upperMgDl, 147);
    });

    test('D22 G1: unknown source/display unit cannot silently fall back', () {
      expect(() => candidate.withDisplayPreference('glucose'), throwsArgumentError);
      final unknownSource = _CandidateRange(
        ownerId: 1001,
        status: _ReviewStatus.explicitlyVerified,
        sourceUnit: 'unknown',
        lowerMgDl: 91,
        upperMgDl: 147,
        sourceReference: 'synthetic-test-only-authority',
      );
      expect(unknownSource.canEvaluateForOwner(1001, 100), isFalse);
    });

    test('D22 G7: evidence for A must never classify B', () {
      expect(candidate.canEvaluateForOwner(1002, 100), isFalse);
      expect(candidate.canEvaluateForOwner(1001, 100), isTrue);
      expect(candidate.canEvaluateForOwner(1001, 200), isTrue); // No clinical comparison is performed.
      expect(candidate.canEvaluateForOwner(1001, double.nan), isFalse);
    });

    test('D22 G2/G3: missing provenance or invalid bounds stay unknown', () {
      for (final bad in [
        _CandidateRange(
          ownerId: 1001,
          status: _ReviewStatus.explicitlyVerified,
          sourceUnit: 'mg/dL',
          lowerMgDl: 91,
          upperMgDl: 147,
          sourceReference: null,
        ),
        _CandidateRange(
          ownerId: 1001,
          status: _ReviewStatus.explicitlyVerified,
          sourceUnit: 'mg/dL',
          lowerMgDl: 147,
          upperMgDl: 91,
          sourceReference: 'synthetic',
        ),
        _CandidateRange(
          ownerId: 1001,
          status: _ReviewStatus.explicitlyVerified,
          sourceUnit: 'mg/dL',
          lowerMgDl: double.infinity,
          upperMgDl: 147,
          sourceReference: 'synthetic',
        ),
      ]) {
        expect(bad.hasAuthority, isFalse);
        expect(bad.canEvaluateForOwner(1001, 100), isFalse);
      }
    });
  });
}
