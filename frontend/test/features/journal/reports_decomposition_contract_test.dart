import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Reports keeps DB/stream orchestration out of presentation part', () {
    final state = File(
      'lib/features/journal/reports_screen.dart',
    ).readAsStringSync();
    final presentation = File(
      'lib/features/journal/reports_screen_presentation.dart',
    ).readAsStringSync();

    expect(state, contains("part 'reports_screen_presentation.dart';"));
    expect(state, contains('class _OfflineReportsScreenState'));
    expect(state, contains('context.read<AppDatabase>()'));
    expect(state, contains('watchProfile()'));
    expect(state, contains('watchLogsInRange(start, end)'));
    expect(state, contains('setState(() => _days = value)'));
    expect(state, isNot(contains('class _ReportView')));
    expect(state, isNot(contains('class _Metrics')));
    expect(state, isNot(contains('class _Distribution')));
    expect(state, isNot(contains('class _Latest')));

    expect(presentation, contains('class _ReportView'));
    expect(presentation, contains('class _Metrics'));
    expect(presentation, contains('class _Distribution'));
    expect(presentation, contains('class _Latest'));
    expect(presentation, isNot(contains('context.read<AppDatabase>()')));
    expect(presentation, isNot(contains('watchLogsInRange(')));
    expect(presentation, isNot(contains("import 'package:")));
  });
}
