import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard trend uses factual time ranges and recorded points only', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();
    final queries = File(
      'lib/data/drift/dashboard_trend_queries.dart',
    ).readAsStringSync();

    expect(section, contains('const Duration(hours: 24)'));
    expect(section, contains('const Duration(days: 7)'));
    expect(section, contains('const Duration(days: 14)'));
    expect(section, contains('const Duration(days: 30)'));
    expect(section, contains('watchDashboardTrendLogs(start, now)'));
    expect(queries, contains('row.loggedAt.isBetweenValues(start, end)'));
    expect(queries, contains('row.loggedAt.isNull()'));
    expect(queries, contains('row.createdAt.isBetweenValues(start, end)'));
    expect(painter, contains('canvas.drawCircle'));
    expect(section + painter, isNot(contains('LineChart')));
    expect(section + painter, isNot(contains('isCurved')));
    expect(section + painter, isNot(contains('ClinicalEngine')));
    expect(section + painter, isNot(contains('calcGMI')));
    expect(section + painter, isNot(contains('Agp')));
    expect(section + painter, isNot(contains('AGP')));
  });

  test('Dashboard trend never introduces local glucose thresholds', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();
    final source = section + painter;

    expect(source, isNot(contains('bloodSugar < 70')));
    expect(source, isNot(contains('bloodSugar > 250')));
    expect(source, isNot(contains('bloodSugar > 180')));
    expect(section, contains('widget.low != null && widget.high != null'));
    expect(section, contains('widget.low! < widget.high!'));
    expect(section, contains('low: hasTarget ? widget.low : null'));
    expect(section, contains('high: hasTarget ? widget.high : null'));
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
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();
    final queries = File(
      'lib/data/drift/dashboard_trend_queries.dart',
    ).readAsStringSync();

    expect(section, contains('watchDashboardMedicationEvents(start, end)'));
    expect(painter, contains('event.takenAt'));
    expect(queries, contains('row.takenAt.isBetweenValues(start, end)'));
    expect(section + painter, isNot(contains('treatmentResponse')));
    expect(section + painter, isNot(contains('causal')));
  });

  test('Dashboard responsive composition includes factual trend after today summary', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final responsive = File(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    ).readAsStringSync();

    final todayIndex = dashboard.indexOf('DashboardTodaySection(');
    final responsiveIndex = dashboard.indexOf('DashboardResponsiveSections(');
    final trendIndex = responsive.indexOf('DashboardTrendSection(');

    expect(todayIndex, greaterThanOrEqualTo(0));
    expect(responsiveIndex, greaterThan(todayIndex));
    expect(trendIndex, greaterThanOrEqualTo(0));
    expect(responsive, contains('unit: unit'));
    expect(responsive, contains('low: low'));
    expect(responsive, contains('high: high'));
  });
}
