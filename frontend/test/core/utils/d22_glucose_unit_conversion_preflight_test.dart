import 'package:amina/core/utils/glucose_formatter.dart';
import 'package:flutter_test/flutter_test.dart';

/// D22 preflight: pure display arithmetic, using synthetic examples only.
///
/// This verifies an existing formatter, NOT clinical target policy, the
/// PatientProfiles schema, or whether a patient's saved range can be safely
/// interpreted after a unit change. Those require the D19 contract.
void main() {
  group('D22 Web glucose unit display preflight', () {
    test('uses the existing mg/dL canonical input and display conversion', () {
      expect(GlucoseFormatter.mgdlToMmolFactor, inInclusiveRange(18.0, 18.1));

      // D19 #920 proposes a different close-precision conversion constant.\n      // Do not pin a pending clinical authority decision in D22 preflight.\n      // Illustrative laboratory quantities, never prescribed targets.
      expect(GlucoseFormatter.format(90, 'mg/dL'), '90 mg/dL');
      expect(GlucoseFormatter.format(90, 'mmol/L'), '5.0 mmol/L');
      expect(GlucoseFormatter.format(126, 'mmol/L'), '7.0 mmol/L');
      expect(GlucoseFormatter.format(180, 'mmol/L'), '10.0 mmol/L');

      // The input is always in mg/dL. Unit is display-only in this helper.
      expect(GlucoseFormatter.convert(180, 'mg/dL'), 180);
      expect(GlucoseFormatter.convert(180, 'mmol/L'),
          closeTo(180 / GlucoseFormatter.mgdlToMmolFactor, 0.000001));
    });

    test('formatting and chart conversion do not modify raw observations', () {
      final storedMgDl = <double>[90, 126, 180];
      final before = List<double>.from(storedMgDl);

      final formatted = storedMgDl
          .map((value) => GlucoseFormatter.format(value, 'mmol/L'))
          .toList();

      expect(formatted, <String>[
        '5.0 mmol/L',
        '7.0 mmol/L',
        '10.0 mmol/L',
      ]);
      expect(storedMgDl, before);

      final mmolBounds =
          GlucoseFormatter.getChartBounds(storedMgDl, 'mmol/L');
      final mgBounds =
          GlucoseFormatter.getChartBounds(storedMgDl, 'mg/dL');
      expect(mmolBounds[0], lessThan(90 / GlucoseFormatter.mgdlToMmolFactor));
      expect(mmolBounds[1], greaterThan(180 / GlucoseFormatter.mgdlToMmolFactor));
      expect(mgBounds[0], lessThan(90));
      expect(mgBounds[1], greaterThan(180));
      expect(storedMgDl, before);
    });

    test('only the two documented unit spellings are contract-tested', () {
      // Do not infer support for arbitrary units from a fallback to mg/dL.
      expect(GlucoseFormatter.format(90, 'mg/dL'), '90 mg/dL');
      expect(GlucoseFormatter.format(90, 'mmol/L'), '5.0 mmol/L');
    });
  });
}
