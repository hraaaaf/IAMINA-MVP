import 'dart:io';

import 'package:amina/core/utils/glucose_formatter.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('backend-contract glucose factor preserves the 190 mg/dL boundary oracle', () {
    expect(GlucoseFormatter.mgdlToMmolFactor, 18.016);
    expect(GlucoseFormatter.convert(190, 'mmol/L').toStringAsFixed(1), '10.5');
    expect(GlucoseFormatter.format(190, 'mmol/L'), '10.5 mmol/L');
    expect(GlucoseFormatter.format(190, 'mg/dL'), '190 mg/dL');
    expect(GlucoseFormatter.convert(190, 'mg/dL'), 190);
  });

  test('clinical target cutpoints remain independent of display rounding', () {
    expect(GlucoseFormatter.convert(70, 'mmol/L').toStringAsFixed(1), '3.9');
    expect(GlucoseFormatter.convert(180, 'mmol/L').toStringAsFixed(1), '10.0');
    expect(GlucoseFormatter.convert(118, 'mmol/L').toStringAsFixed(1), '6.5');
    expect(GlucoseFormatter.convert(109, 'mmol/L').toStringAsFixed(1), '6.1');
    expect(GlucoseFormatter.convert(190, 'mmol/L') * 18.016, closeTo(190, 1e-9));
  });

  test('editing unchanged 69.9 mg/dL never crosses the 70 boundary', () {
    const original = 69.9;
    final displayed = GlucoseFormatter.convert(original, 'mmol/L');
    expect(displayed.toStringAsFixed(1), '3.9');
    expect(
      GlucoseFormatter.editedToMgDl(
        3.9, 'mmol/L',
        initialDisplayedValue: 3.9, initialMgDl: original,
      ),
      69.9,
    );
    expect(GlucoseFormatter.toMgDl(3.9, 'mmol/L'), closeTo(70.2624, 1e-7));
    expect(
      GlucoseFormatter.editedToMgDl(
        4.0, 'mmol/L',
        initialDisplayedValue: 3.9, initialMgDl: original,
      ),
      closeTo(72.064, 1e-7),
    );
    expect(GlucoseFormatter.toMgDl(10.5, 'mmol/L'), closeTo(189.168, 1e-7));
    expect(GlucoseFormatter.toMgDl(190, 'mg/dL'), 190);
  });

  test('reachable Home and Reports use the shared normalization factor', () {
    final dashboard = File('lib/features/dashboard/dashboard_premium_screen.dart')
        .readAsStringSync();
    final reports = File('lib/features/journal/reports_screen_presentation.dart')
        .readAsStringSync();
    expect(dashboard, contains('GlucoseFormatter.convert(mg, unit)'));
    expect(reports, contains('GlucoseFormatter.convert(mgDl, unit)'));
    expect(dashboard, isNot(contains('mg / 18.0')));
    expect(reports, isNot(contains('mgDl / 18.0')));
    final addLog = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    final editLog = File('lib/features/journal/edit_log_screen.dart')
        .readAsStringSync();
    expect(addLog, contains('GlucoseFormatter.toMgDl'));
    expect(editLog, contains('GlucoseFormatter.editedToMgDl'));
    expect(addLog, isNot(contains('value * 18.0')));
    expect(editLog, isNot(contains('value * 18.0')));
  });
}
