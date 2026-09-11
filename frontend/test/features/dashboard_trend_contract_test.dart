import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard trend uses factual time ranges and governed daily summaries', () {
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
    expect(painter, contains('_paintRecordedPoints'));
    expect(painter, contains('_paintDailySummary'));
    expect(painter, contains('_dailySummaries'));
    expect(painter, contains('median: median'));
    expect(painter, contains('min: values.first'));
    expect(painter, contains('max: values.last'));
    expect(section + painter, isNot(contains('ClinicalEngine')));
    expect(section + painter, isNot(contains('calcGMI')));
    expect(section + painter, isNot(contains('Agp')));
    expect(section + painter, isNot(contains('AGP')));
  });

  test('Dashboard trend normalizes locale before Intl date formatting', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();

    expect(section, contains('_dashboardTrendDateLocale'));
    expect(section, contains("'fr' => 'fr-FR'"));
    expect(section, contains("'ar' => 'ar-MA'"));
    expect(section, contains("'en' => 'en-US'"));
    expect(
      section,
      contains('final locale = _dashboardTrendDateLocale(context);'),
    );
  });

  test('Approved target composition is present in the real dashboard trend', () {
    final section = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();

    expect(section, contains('_TrendSummary'));
    expect(section, contains('_SummaryMetric'));
    expect(section, contains("'Récent'"));
    expect(section, contains("'Moyenne'"));
    expect(section, contains("'Dans la cible'"));
    expect(section, contains("'Médiane journalière'"));
    expect(section, contains("'Min – Max (observé)'"));
    expect(section, contains('Plage cible'));
    expect(section, contains('_TrendSelectionCard'));
    expect(painter, contains('path.cubicTo'));
    expect(painter, contains('_paintTargetBand'));
    expect(painter, contains('_paintDailySummary'));
  });

  test('Daily line connects daily medians rather than raw measurements', () {
    final painter = File(
      'lib/features/dashboard/widgets/dashboard_trend_painter.dart',
    ).readAsStringSync();

    expect(painter, contains('final median = values.length.isOdd'));
    expect(painter, contains('yFor(summary.median)'));
    expect(painter, contains('path.cubicTo'));
    expect(painter, isNot(contains('_paintRecordedTrajectory')));
    expect(painter, isNot(contains('forecast')));
    expect(painter, isNot(contains('prediction')));
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

  test('Dashboard trend keeps provenance and selected reading context explicit', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_trend_section.dart',
    ).readAsStringSync();

    expect(source, contains('dashboardTrendSourceLabel(log.source)'));
    expect(source, contains('dashboardTrendNoContext'));
    expect(source, contains('log.glycemicContext'));
    expect(source, contains('log.mealType'));
    expect(source, contains('DateFormat('));
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

  test('Dashboard responsive composition keeps trend after today summary', () {
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
