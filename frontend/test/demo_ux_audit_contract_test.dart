import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  String source(String path) => File(path).readAsStringSync();

  test('home keeps import and CGM below the primary follow-up actions', () {
    final today = source(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    );
    final dashboard = source(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    );
    expect(today, isNot(contains('dashboard-secondary-import')));
    expect(dashboard, contains("context.go('/importer')"));
    expect(dashboard, contains("context.go('/cgm')"));
  });

  test('home no longer duplicates the adaptive indicator block', () {
    final responsive = source(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    );
    expect(responsive, isNot(contains('DashboardAdaptiveKpiSection(')));
  });

  test('IAmina chat entry is distinct from automatic insight', () {
    final today = source(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    );
    final insight = source(
      'lib/core/localization/dashboard_insight_localized_copy.dart',
    );
    expect(today, contains("context.go('/companion/chat')"));
    expect(insight, contains('Automatic IAmina insight'));
  });

  test('importer route opens the document import task directly', () {
    final module = source('lib/modules/diabetes_module.dart');
    expect(
      module,
      contains(
        "path: '/importer',\n      builder: (s) => const DocumentImportPremiumScreen(),",
      ),
    );
  });

  test('reports stay descriptive instead of switching to AI summary', () {
    final reports = source('lib/features/journal/reports_screen.dart');
    expect(reports, contains('return const _OfflineReportsScreen();'));
    expect(reports, isNot(contains('AISummaryScreen')));
  });

  test('profile assistant action opens chat instead of onboarding', () {
    final profile = source(
      'lib/features/profile/profile_screen_presentation.dart',
    );
    expect(profile, contains("context.push('/companion/chat')"));
    expect(profile, isNot(contains("context.push('/onboarding')")));
  });

  test('edit measurement persists add-flow context dimensions', () {
    final edit = source('lib/features/journal/edit_log_screen.dart');
    for (final token in <String>[
      'glycemicContext: drift.Value(_glycemicContext)',
      'mealType: drift.Value(_mealType)',
      'mealItemsJson: drift.Value',
      'mealPortionsJson: drift.Value',
      'loggedAt: drift.Value(_selectedTime)',
      'AddLogMeasurementContext(',
      'AddLogMealCapture(',
      'AddLogDetailsCard(',
    ]) {
      expect(edit, contains(token), reason: token);
    }
  });
}
