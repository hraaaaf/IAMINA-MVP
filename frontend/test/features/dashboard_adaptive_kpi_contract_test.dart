import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Adaptive KPIs describe recorded data without advanced CGM formulas', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_adaptive_kpi_section.dart',
    ).readAsStringSync();

    expect(source, contains('watchDashboardTrendLogs(start, now)'));
    expect(source, contains('const Duration(days: 6)'));
    expect(source, contains("logs.fold<double>"));
    expect(source, contains('daysWithData'));
    expect(source, isNot(contains('ClinicalEngine')));
    expect(source, isNot(contains('calcGMI')));
    expect(source, isNot(contains('calcCV')));
    expect(source, isNot(contains('calcTIR')));
    expect(source, isNot(contains('timeInRange')));
    expect(source, isNot(contains('70.0')));
    expect(source, isNot(contains('180.0')));
    expect(source, isNot(contains('250.0')));
  });

  test('Personal-target count is explicit and never presented as time in range', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_adaptive_kpi_section.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/dashboard_kpi_localized_copy.dart',
    ).readAsStringSync();

    expect(source, contains('final targetConfigured = low != null && high != null'));
    expect(source, contains('log.bloodSugar >= low!'));
    expect(source, contains('log.bloodSugar <= high!'));
    expect(source, contains("value: targetConfigured ? '\$readingsInTarget/\$count' : '—'"));
    expect(copy, contains('dashboardKpiNotTimeInRange'));
    expect(copy, contains('pas du temps dans la cible'));
  });

  test('CGM-labelled local rows fail closed without governed coverage authority', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_adaptive_kpi_section.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/dashboard_kpi_localized_copy.dart',
    ).readAsStringSync();

    expect(source, contains('_looksCgmLabelled'));
    expect(source, contains("normalized.contains('dexcom')"));
    expect(source, contains("normalized.contains('libre')"));
    expect(source, contains("normalized.contains('nightscout')"));
    expect(source, contains('dashboardKpiCgmMarkedUnverified'));
    expect(source, contains('dashboardKpiAdvancedCgmLocked'));
    expect(copy, contains('couverture active du capteur ne peut pas être prouvée'));
    expect(copy, contains('couverture capteur n’est pas prouvée'));
    expect(source, isNot(contains('coveragePercent')));
    expect(source, isNot(contains('activeCoverage')));
  });

  test('Adaptive KPI density keeps 390px in two-column mode and 360px cards full width', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_adaptive_kpi_section.dart',
    ).readAsStringSync();

    expect(source, contains('constraints.maxWidth < 310'));
    expect(source, isNot(contains('constraints.maxWidth < 330')));
    expect(source, contains('width: (constraints.maxWidth - 8) / 2'));
    expect(source, contains('width: double.infinity'));
  });

  test('Dashboard composition places adaptive KPIs after factual trend on mobile', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final responsive = File(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    ).readAsStringSync();

    final responsiveIndex = dashboard.indexOf('DashboardResponsiveSections(');
    final trendIndex = responsive.indexOf('DashboardTrendSection(');
    final kpiIndex = responsive.indexOf('DashboardAdaptiveKpiSection(');
    expect(responsiveIndex, greaterThanOrEqualTo(0));
    expect(trendIndex, greaterThanOrEqualTo(0));
    expect(kpiIndex, greaterThan(trendIndex));
    expect(dashboard, contains('unit: unit'));
    expect(dashboard, contains('low: low'));
    expect(dashboard, contains('high: high'));
  });
}
