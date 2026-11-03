import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// D22 Web — source-order contract for the Profile UI candidate only.
///
/// This is NOT an actual browser/widget FUE, target-provenance validation,
/// conversion test or approval to display/use any clinical target. D19 G1–G7
/// still gate functional changes and release.
void main() {
  final source = File(
    'lib/features/profile/profile_screen_presentation.dart',
  ).readAsStringSync();

  test('D22 Profile offers a glucose unit before target inputs', () {
    const unitTitle = '_buildSectionTitle(Icons.straighten, l10n.measureUnit)';
    const targetTitle = '_buildSectionTitle(Icons.show_chart, l10n.glucoseTarget)';
    const saveAction = 'onPressed: _saveProfile';

    final unit = source.indexOf(unitTitle);
    final target = source.indexOf(targetTitle);
    final save = source.indexOf(saveAction, target);

    expect(unit, greaterThanOrEqualTo(0));
    expect(target, greaterThan(unit));
    expect(save, greaterThan(target));
    expect(source.indexOf(unitTitle, unit + unitTitle.length), -1);
    expect(source.indexOf(targetTitle, target + targetTitle.length), -1);

    final unitChooser = source.substring(unit, target);
    expect(unitChooser, contains("['mg/dL', 'mmol/L']"));
    expect(unitChooser, contains('_unit'));
  });

  test('D22 candidate retains the existing two target entry fields', () {
    const targetTitle = '_buildSectionTitle(Icons.show_chart, l10n.glucoseTarget)';
    const saveAction = 'onPressed: _saveProfile';
    final start = source.indexOf(targetTitle);
    final end = source.indexOf(saveAction, start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final targetForm = source.substring(start, end);
    expect(targetForm, contains('_targetLowController'));
    expect(targetForm, contains('_targetHighController'));
    expect(targetForm, contains('AuditedPageCopy.of(context).minimum'));
    expect(targetForm, contains('AuditedPageCopy.of(context).maximum'));
  });
}
