import 'package:amina/features/profile/d22_glucose_quantity_candidate.dart';
import 'package:flutter_test/flutter_test.dart';

/// D22-B staging contract, SYNTHETIC ONLY. Passing does not mean that
/// the app onboarding, DB, dashboard or CGM classifications are fixed.
void main() {
  group('D22-B G1/G4 staged typed source contract (non-clinical)', () {
    test('parses only the exact supported source units, no silent fallback', () {
      expect(d22ParseGlucoseUnit('mg/dL'), D22GlucoseUnit.mgDl);
      expect(d22ParseGlucoseUnit('mmol/L'), D22GlucoseUnit.mmolL);
      for (final invalid in <String?>[
        null, '', 'unknown', 'mgdl', 'mmol', 'MG/DL', ' mg/dL',
        'mmol/L ', 'g/L',
      ]) {
        expect(d22ParseGlucoseUnit(invalid), isNull);
      }
    });

    test('keeps the source text and unit unchanged during display switches', () {
      const source = D22CapturedGlucoseCandidate(
        rawInput: '90.000', sourceUnit: 'mg/dL', ownerId: 2001,
      );
      final before = source.rawInput;
      expect(source.valueForDisplay(D22GlucoseUnit.mmolL),
          closeTo(90 / d22CandidateMgDlPerMmolL, 0.000000001));
      expect(source.valueForDisplay(D22GlucoseUnit.mgDl), 90);
      expect(source.rawInput, before);
      expect(source.sourceUnit, 'mg/dL');
    });

    test('converts candidate mmol/L to mg/dL without rounding the source', () {
      const source = D22CapturedGlucoseCandidate(
        rawInput: '5.000', sourceUnit: 'mmol/L', ownerId: 2001,
      );
      expect(source.valueForDisplay(D22GlucoseUnit.mgDl),
          closeTo(5 * d22CandidateMgDlPerMmolL, 0.000000001));
      expect(source.rawInput, '5.000');
    });

    test('display rounding never becomes a new stored value', () {
      const original = D22CapturedGlucoseCandidate(
        rawInput: '90', sourceUnit: 'mg/dL', ownerId: 2001,
      );
      final unrounded = original.valueForDisplay(D22GlucoseUnit.mmolL)!;
      expect(unrounded.toStringAsFixed(1), '5.0');
      expect(unrounded, isNot(5.0));
      expect(original.valueForDisplay(D22GlucoseUnit.mgDl), 90);
    });

    test('legacy 70/180 with unknown unit is preserved but not converted', () {
      const legacy = D22CapturedGlucoseCandidate(
        rawInput: '70', sourceUnit: null, ownerId: 2001,
      );
      expect(legacy.rawInput, '70');
      expect(legacy.valueForDisplay(D22GlucoseUnit.mgDl), isNull);
      expect(legacy.valueForDisplay(D22GlucoseUnit.mmolL), isNull);
    });

    test('invalid numeric quantities fail closed with no false output', () {
      for (final raw in ['NaN', 'Infinity', '-1', '0', 'abc', '1e9999']) {
        final candidate = D22CapturedGlucoseCandidate(
          rawInput: raw, sourceUnit: 'mg/dL', ownerId: 2001,
        );
        expect(candidate.valueForDisplay(D22GlucoseUnit.mgDl), isNull);
      }
      const invalidOwner = D22CapturedGlucoseCandidate(
        rawInput: '90', sourceUnit: 'mg/dL', ownerId: 0,
      );
      expect(invalidOwner.valueForDisplay(D22GlucoseUnit.mmolL), isNull);
    });

    test('never claims authority from legacy target values or missing source', () {
      const low = D22CapturedGlucoseCandidate(
        rawInput: '70', sourceUnit: null, ownerId: 2001,
      );
      const high = D22CapturedGlucoseCandidate(
        rawInput: '180', sourceUnit: null, ownerId: 2001,
      );
      const legacy = D22UnapprovedTargetCandidate(
        ownerId: 2001, sourceReference: null, lower: low, upper: high,
      );
      expect(legacy.canBeSubmittedForReview(2001), isFalse);
    });

    test('cannot consider another owner, invalid bounds or absent provenance', () {
      const low = D22CapturedGlucoseCandidate(
        rawInput: '5', sourceUnit: 'mmol/L', ownerId: 2001,
      );
      const high = D22CapturedGlucoseCandidate(
        rawInput: '100', sourceUnit: 'mg/dL', ownerId: 2001,
      );
      const review = D22UnapprovedTargetCandidate(
        ownerId: 2001, sourceReference: 'synthetic-reference', lower: low,
        upper: high,
      );
      expect(review.canBeSubmittedForReview(2002), isFalse);
      expect(review.canBeSubmittedForReview(2001), isTrue);
      // Reviewability is not medical signoff; in/out-target is absent.
      const noSource = D22UnapprovedTargetCandidate(
        ownerId: 2001, sourceReference: '', lower: low, upper: high,
      );
      expect(noSource.canBeSubmittedForReview(2001), isFalse);
      const wrongOrder = D22UnapprovedTargetCandidate(
        ownerId: 2001, sourceReference: 'synthetic-reference',
        lower: high, upper: low,
      );
      expect(wrongOrder.canBeSubmittedForReview(2001), isFalse);
    });

    test('rejects overflow instead of returning Infinity or making a target', () {
      const extreme = D22CapturedGlucoseCandidate(
        rawInput: '1e308', sourceUnit: 'mmol/L', ownerId: 2001,
      );
      expect(extreme.valueForDisplay(D22GlucoseUnit.mgDl), isNull);
      expect(extreme.rawInput, '1e308');
    });
  });
}
