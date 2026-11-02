import 'package:amina/core/domain/glucose_quantity_evidence.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('D22 G1 source-unit authority (STAGED ONLY)', () {
    test('UCUM codes are explicit, not inferred from display preferences', () {
      expect(
        GlucoseSourceUnit.fromExplicitUcumCode('mg/dL'),
        GlucoseSourceUnit.mgDl,
      );
      expect(
        GlucoseSourceUnit.fromExplicitUcumCode('mmol/L'),
        GlucoseSourceUnit.mmolL,
      );
      for (final unknown in <String?>[
        null, '', 'mgdl', 'MMOL/L', 'mg/dl', 'mg%', 'g/L',
      ]) {
        expect(
          GlucoseSourceUnit.fromExplicitUcumCode(unknown),
          isNull,
          reason: 'Undeclared alias must not silently normalize',
        );
      }
    });

    test('declared manual source value/unit preserved across toggles', () {
      final source = GlucoseQuantityEvidence.userEntry(
        originalValue: 140.0,
        declaredUnit: GlucoseSourceUnit.mgDl,
      );

      expect(source.provenance, GlucoseValueProvenance.userEntered);
      expect(source.hasExplicitSourceUnit, isTrue);
      expect(source.originalRawValue, 140.0);
      expect(source.originalUnit, GlucoseSourceUnit.mgDl);
      expect(source.canonicalMgDl, 140.0);
      final mmol = source.displayValue(GlucoseSourceUnit.mmolL)!;
      expect(mmol, closeTo(7.771, .002));
      expect(mmol.toStringAsFixed(1), '7.8');
      expect(source.displayValue(GlucoseSourceUnit.mgDl), 140.0);
      expect(source.originalRawValue, 140.0);
    });

    test('original mmol/L input not replaced by rounded mg/dL', () {
      final source = GlucoseQuantityEvidence.userEntry(
        originalValue: 7.83,
        declaredUnit: GlucoseSourceUnit.mmolL,
      );
      expect(source.originalRawValue, 7.83);
      expect(source.originalUnit, GlucoseSourceUnit.mmolL);
      expect(source.displayValue(GlucoseSourceUnit.mmolL), 7.83);
      expect(
        source.canonicalMgDl,
        closeTo(7.83 * 18.01559, .000000001),
      );
      expect(source.displayValue(GlucoseSourceUnit.mgDl),
          closeTo(141.0620697, .0001));
      expect(source.originalRawValue, 7.83);
    });

    test('invalid manually entered readings fail closed', () {
      for (final n in <double>[
        0.0, -5.0, double.nan, double.infinity,
        double.negativeInfinity,
      ]) {
        expect(
          () => GlucoseQuantityEvidence.userEntry(
            originalValue: n, declaredUnit: GlucoseSourceUnit.mgDl,
          ),
          throwsArgumentError,
        );
      }
    });
  });

  group('D22 G4 conversion factor (NOT active in app)', () {
    test('NIST-derived glucose mass conversion is numerically consistent', () {
      expect(GlucoseConversionContract.mgDlPerMmolL, 18.01559);
      expect(
        GlucoseConversionContract.toMgDl(10, GlucoseSourceUnit.mmolL),
        closeTo(180.1559, .0000001),
      );
      expect(
        GlucoseConversionContract.convert(
          180.1559,
          GlucoseSourceUnit.mmolL,
        ),
        closeTo(10.0, .0000001),
      );
    });
    test('conversion is a read-only projection, never a persistence write', () {
      final source = GlucoseQuantityEvidence.userEntry(
        originalValue: 180.1559, declaredUnit: GlucoseSourceUnit.mgDl,
      );
      final mmolDisplay = source.displayValue(GlucoseSourceUnit.mmolL);
      expect(mmolDisplay, closeTo(10.0, .0000001));
      expect(source.originalRawValue, 180.1559);
      expect(source.originalUnit, GlucoseSourceUnit.mgDl);
    });
  });

  group('D22 G7 legacy no-guess guarantee (NO schema migration)', () {
    test('unknown historic 70/180 are NOT source-authorized quantities', () {
      for (final raw in <double>[70, 180, 7.0, 10, 140]) {
        final source =
            GlucoseQuantityEvidence.unknownLegacy(storedValue: raw);
        expect(source.originalRawValue, raw);
        expect(source.originalUnit, isNull);
        expect(source.provenance, GlucoseValueProvenance.legacyUnknown);
        expect(source.hasExplicitSourceUnit, isFalse);
        expect(source.canonicalMgDl, isNull);
        expect(source.displayValue(GlucoseSourceUnit.mgDl), isNull);
        expect(source.displayValue(GlucoseSourceUnit.mmolL), isNull);
      }
    });
    test('even corrupt historic value is preserved but not normalized', () {
      final old =
          GlucoseQuantityEvidence.unknownLegacy(storedValue: double.nan);
      expect(old.originalRawValue.isNaN, isTrue);
      expect(old.canonicalMgDl, isNull);
    });
  });
}
