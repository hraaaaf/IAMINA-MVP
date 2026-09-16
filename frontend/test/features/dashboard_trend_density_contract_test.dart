import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('multi-day trend summarizes daily data without dot clouds', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();

    expect(section, contains('bool get useDailySummary'));
    expect(section, contains('dailySummary: range.useDailySummary'));
    expect(painter, contains('_paintDailySummary'));
    expect(painter, contains('_dailySummaries'));
    expect(painter, contains('final median = values.length.isOdd'));
    expect(painter, contains('min: values.first'));
    expect(painter, contains('max: values.last'));
    expect(painter, contains('path.cubicTo'));
    expect(painter, isNot(contains('_paintRecordedTrajectory')));
  });

  test('premium trend retains target, min-max and selected-reading semantics', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final view = File(
      'lib/features/dashboard/widgets/dashboard_trend_view.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();

    expect(section, contains('DashboardTrendSelectionCard'));
    expect(view, contains("'Médiane journalière'"));
    expect(view, contains("'Min – Max (observé)'"));
    expect(view, contains('Plage cible'));
    expect(view, contains('class DashboardTrendSelectionCard'));
    expect(painter, contains('_paintTargetBand'));
    expect(painter, contains('summary.logIds.contains(selectedLogId)'));
  });
}
