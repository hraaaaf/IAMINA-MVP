import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard smart insight reads only the governed preview GET', () {
    final service = File('lib/services/companion_service.dart').readAsStringSync();
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_insight_section.dart',
    ).readAsStringSync();

    expect(service, contains('fetchProactivePreview()'));
    expect(service, contains("/api/v1/proactive-insights/preview/"));
    expect(service, isNot(contains('/proactive-insights/evaluate/')));
    expect(widget, contains('fetchProactivePreview()'));
    expect(widget, isNot(contains('evaluate')));
    expect(widget, isNot(contains('sort(')));
    expect(widget, isNot(contains('max(')));
    expect(widget, isNot(contains('priority.')));
  });

  test('Dashboard smart insight is one fail-closed item with explicit states', () {
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_insight_section.dart',
    ).readAsStringSync();

    expect(widget, contains("preview.status == 'insufficient_data'"));
    expect(widget, contains("preview.status == 'cooldown'"));
    expect(widget, contains("preview.status == 'no_change'"));
    expect(widget, contains("preview.status != 'available' || item == null"));
    expect(widget, contains('dashboardInsightUnavailable'));
    expect(widget, contains('dashboardInsightRetry'));
    expect(widget, contains('_InsightBody(item: item)'));
    expect(widget, isNot(contains('.map((item)')));
    expect(widget, isNot(contains('List<ProactivePreviewItem>')));
  });

  test('Dashboard smart insight exposes evidence and limitation, not diagnosis', () {
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_insight_section.dart',
    ).readAsStringSync();
    final copy = File(
      'lib/core/localization/dashboard_insight_localized_copy.dart',
    ).readAsStringSync();

    expect(widget, contains('item.observations'));
    expect(widget, contains('item.distinctDays'));
    expect(widget, contains('item.evidenceWindowDays'));
    expect(widget, contains('item.evidenceDensity'));
    expect(widget, contains('item.allowedNextStep'));
    expect(widget, contains("context.go('/companion')"));
    expect(copy, contains('Association descriptive uniquement'));
    expect(copy, contains('ni cause, ni diagnostic, ni effet du traitement'));
    expect(copy, contains('dashboardInsightObservationLabel'));
    expect(widget, contains('dashboardInsightObservationLabel(item.observationKey)'));
    expect(widget, isNot(contains('personalBaselineComparisonMgDl')));
  });

  test('Dashboard mobile composition keeps governed insight after adaptive KPIs', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final responsive = File(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    ).readAsStringSync();

    final today = dashboard.indexOf('DashboardTodaySection(');
    final responsiveMount = dashboard.indexOf('DashboardResponsiveSections(');
    final trend = responsive.indexOf('DashboardTrendSection(');
    final kpi = responsive.indexOf('DashboardAdaptiveKpiSection(');
    final insight = responsive.indexOf('DashboardInsightSection(');

    expect(today, greaterThanOrEqualTo(0));
    expect(responsiveMount, greaterThan(today));
    expect(trend, greaterThanOrEqualTo(0));
    expect(kpi, greaterThan(trend));
    expect(insight, greaterThan(kpi));
  });

  test('Read-only backend preview has no clinical refresh or persistence writes', () {
    final preview = File(
      '../backend/diabetes/services/clinical/proactive_preview.py',
    ).readAsStringSync();
    final api = File('../backend/diabetes/api/v1/proactive.py').readAsStringSync();

    expect(preview, isNot(contains('refresh_personal_response_memory(')));
    expect(preview, isNot(contains('.save(')));
    expect(preview, isNot(contains('.create(')));
    expect(preview, contains('_derive_state'));
    expect(preview, contains('_derive_relevance'));
    expect(preview, contains('_derive_action'));
    expect(preview, contains('_priority_key'));
    expect(preview, contains('_build_item'));
    expect(api, contains('@router.get("/proactive-insights/preview/"'));
    expect(api, contains('@router.post("/proactive-insights/evaluate/"'));
  });
}
