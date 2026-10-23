import 'dart:io';

import 'package:amina/core/data/ramadan_context.dart' as ramadan;
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 Ramadan Web suppression and L0 finite glucose coexist', () {
    final event = DateTime(2026, 3, 5);
    final start = DateTime(2026, 2, 18);
    final end = DateTime(2026, 3, 20);
    expect(ramadan.shouldApplyRamadanProfileContext(isWeb: true), isFalse);
    expect(
      ramadan.mealTypesForSurfaceDate(event, start, end, isWeb: true),
      ramadan.regularMealTypes,
    );
    expect(
      ramadan.mealTypesForSurfaceDate(event, start, end, isWeb: false),
      ramadan.ramadanMealTypes,
    );
    expect(parsePositiveFiniteGlucoseInput('5,5'), 5.5);
    expect(normalizeFiniteGlucoseMgdl('5,5', 'mmol/L'), 99.0);
    expect(normalizeFiniteGlucoseMgdl('NaN', 'mg/dL'), isNull);
    expect(normalizeFiniteGlucoseMgdl('1e999', 'mmol/L'), isNull);
  });

  test('W03 and L0 share the add-log form without disabling save guard', () {
    final code = File('lib/features/dashboard/widgets/add_log_sheet.dart')
        .readAsStringSync();
    expect(code, contains('shouldApplyRamadanProfileContext(isWeb: kIsWeb)'));
    expect(code.split('mealTypesForSurfaceDate(').length - 1, 2);
    expect(code, contains('parsePositiveFiniteGlucoseInput('));
    expect(code, contains('normalizeFiniteGlucoseMgdl('));
    expect(code, contains('if (_saving) return false;'));
  });
}
