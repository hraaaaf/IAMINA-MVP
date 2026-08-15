import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('legacy insulin focus resolves to Medications, not Add Log insulin UI', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final addLog = File(
      'lib/features/dashboard/widgets/add_log_sheet.dart',
    ).readAsStringSync();

    expect(module, contains("s.uri.queryParameters['focus'] == 'insulin'"));
    expect(module, contains('const MedicationScreen()'));
    expect(addLog, isNot(contains('insulin-taken-input')));
    expect(addLog, isNot(contains('AddLogFocus.insulin')));
  });
}
