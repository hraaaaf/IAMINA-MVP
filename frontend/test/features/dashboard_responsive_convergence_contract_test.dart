import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard route always resolves to the same primary entry', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(module, contains("path: '/dashboard'"));
    expect(module, contains('builder: () => const DashboardCompanionEntryScreen()'));
    expect(module, isNot(contains('DashboardScreen()')));
    expect(module, isNot(contains("dashboard_screen.dart")));
    expect(module, isNot(contains('constraints.maxWidth < 700'));
  });

  test('Responsive density changes layout, not semantic product authority', () {
    final responsive = File(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    ).readAsStringSync();

    expect(responsive, contains('constraints.maxWidth < 760'));
    expect(responsive, contains('DashboardTrendSection('));
    expect(responsive, contains('DashboardAdaptiveKpiSection('));
    expect(responsive, contains('DashboardInsightSection('));
    expect(responsive, contains('DashboardNextActionSection('));
    expect(responsive, isNot(contains('DashboardScreen')));
    expect(responsive, isNot(contains('ClinicalEngine')));
    expect(responsive, isNot(contains('calcGMI')));
    expect(responsive, isNot(contains('calcTIR')));
  });

  test('Large screens are bounded and centered without changing data semantics', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    expect(dashboard, contains('final horizontalPadding = width >= 1200'));
    expect(dashboard, contains('(width - 1120) / 2'));
    expect(dashboard, contains('width >= 700'));
    expect(dashboard, contains('DashboardResponsiveSections('));
    expect(dashboard, contains('watchRecentLogs(limit: 1)'));
    expect(dashboard, isNot(contains('Duration(days: 21)')));
  });
}
