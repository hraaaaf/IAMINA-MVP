import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('add log keeps domain/persistence logic out of presentation view', () {
    final sheet = File(
      'lib/features/dashboard/widgets/add_log_sheet.dart',
    ).readAsStringSync();
    final view = File(
      'lib/features/dashboard/widgets/add_log_view.dart',
    ).readAsStringSync();

    expect(sheet, contains('classifyGlucoseEntrySafety'));
    expect(sheet, contains('mealTypesForProfileDate'));
    expect(sheet, contains('LogEntriesCompanion.insert'));
    expect(sheet, contains('_confirmLowGlucose'));
    expect(sheet, contains('_saveLog'));
    expect(sheet, contains("import 'add_log_view.dart';"));

    expect(view, contains('class AddLogSurface'));
    expect(view, contains('class AddLogGlucoseCard'));
    expect(view, contains('class AddLogMealCapture'));
    expect(view, contains('class AddLogDetailsCard'));
    expect(view, contains('class AddLogSaveBar'));

    expect(view, isNot(contains('LogEntriesCompanion')));
    expect(view, isNot(contains('AppDatabase')));
    expect(view, isNot(contains('mealTypesForProfileDate')));
    expect(view, isNot(contains('classifyGlucoseEntrySafety')));
  });
}
