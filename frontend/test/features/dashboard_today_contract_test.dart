import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard today summary consumes companion overview read only', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();

    expect(source, contains('_service.fetchOverview()'));
    expect(source, contains('signals.take(2)'));
    expect(source, contains("context.go('/companion')"));
    expect(source, contains("context.go('/importer')"));
    expect(source, isNot(contains('proactive-insights')));
    expect(source, isNot(contains('evaluateProactive')));
    expect(source, isNot(contains("context.go('/journal')")));
  });

  test('Dashboard today summary does not rank companion patterns clinically', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();

    expect(source, contains("overview.reviewStatus == 'ready'"));
    expect(source, contains("change.changeKind != 'unknown'"));
    expect(source, contains('determinateChangeCount > 0'));
    expect(source, contains("overview.patternStatus == 'ready'"));
    expect(source, contains('overview.patterns.isNotEmpty'));
    expect(source, isNot(contains('sort(')));
    expect(source, isNot(contains('evidenceDensity')));
    expect(source, isNot(contains('recurrenceCount')));
  });

  test('Dashboard today summary exposes loading unavailable and retry states', () {
    final source = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();
    final localizedCopy = File(
      'lib/core/localization/dashboard_localized_copy.dart',
    ).readAsStringSync();

    expect(source, contains('late Future<CompanionOverview?> _overviewFuture'));
    expect(source, contains('void _reload()'));
    expect(source, contains('final loading = snapshot.connectionState != ConnectionState.done'));
    expect(source, contains('final unavailable = overviewResolved && snapshot.data == null'));
    expect(source, contains('dashboardTodayLoading'));
    expect(source, contains('dashboardTodayUnavailable'));
    expect(source, contains("ValueKey('dashboard-today-retry')"));
    expect(localizedCopy, contains('dashboardTodayLoading'));
    expect(localizedCopy, contains('dashboardTodayUnavailable'));
    expect(localizedCopy, contains('dashboardRetry'));
  });

  test('Dashboard removes the previous three-card shortcut grid', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    expect(dashboard, contains('DashboardTodaySection('));
    expect(dashboard, isNot(contains('class _QuickActions')));
    expect(dashboard, isNot(contains('class _ActionCard')));
    expect(dashboard, isNot(contains('class _TrustCard')));
  });
}
