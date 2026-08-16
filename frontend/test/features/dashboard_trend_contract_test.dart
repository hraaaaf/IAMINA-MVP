import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard trend uses factual time ranges and recorded points only', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final queries = File(
      'lib/data/drift/dashboard_trend_queries.dart',
    ).readAsStringSync();

    expect(source, contains('const Duration(hours: 24)'));
    expect(source, contains('const Duration(days: 7)'));
    expect(source, contains('const Duration(days: 14)'));
    expect(source, contains('const Duration(days: 30)'));
    expect(source, contains('watchDashboardTrendLogs(start, now)'));
    expect(queries, contains('row.loggedAt.isBetweenValues(start, end)'));
    expect(queries, contains('row.loggedAt.isNull()'));
    expect(queries, contains('row.createdAt.isBetweenValues(start, end)'));
    expect(source, contains('canvas.drawCircle'));
    expect(source, isNot(contains('LineChart')));
    expect(source, isNot(contains('isCurved')));
    expect(source, isNot(contains('ClinicalEngine')));
    expect(source, isNot(contains('calcGMI')));
    expect(source, isNot(contains('Agp')));
    expect(source, isNot(contains('AGP')));
  });

  test('Dashboard trend never introduces local glucose thresholds', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();

    expect(source, isNot(contains('bloodSugar < 70')));
    expect(source, isNot(contains('bloodSugar > 250')));
    expect(source, isNot(contains('bloodSugar > 180')));
    expect(source, contains('widget.low != null && widget.high != null'));
    expect(source, contains('widget.low! < widget.high!'));
    expect(source, contains('low: targetConfigured ? widget.low : null'));
    expect(source, contains('high: targetConfigured ? widget.high : null'));
  });

  test('Dashboard trend keeps missing continuity and provenance explicit', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/dashboard_trend_localized_copy.dart',
    ).readAsStringSync();

    expect(source, contains('dashboardTrendNoInterpolation'));
    expect(copy, contains('Les espaces vides restent des données manquantes'));
    expect(source, contains('dashboardTrendSourceLabel(log.source)'));
    expect(source, contains('dashboardTrendNoContext'));
    expect(source, contains('log.glycemicContext'));
    expect(source, contains('log.mealType'));
  });

  test('Dashboard trend renders treatment events as separate recorded events', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final queries = File(
      'lib/data/drift/dashboard_trend_queries.dart',
    ).readAsStringSync();

    expect(source, contains('watchDashboardMedicationEvents(start, now)'));
    expect(source, contains('event.takenAt'));
    expect(queries, contains('row.takenAt.isBetweenValues(start, end)'));
    expect(source, isNot(contains('treatmentResponse')));
    expect(source, isNot(contains('causal')));
  });

  test('Dashboard mobile composition includes the factual trend after today summary', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    final todayIndex = dashboard.indexOf('DashboardTodaySection(');
    final trendIndex = dashboard.indexOf('DashboardTrendSection(');
    expect(todayIndex, greaterThanOrEqualTo(0));
    expect(trendIndex, greaterThan(todayIndex));
    expect(dashboard, contains('unit: unit'));
    expect(dashboard, contains('low: low'));
    expect(dashboard, contains('high: high'));
  });
}
