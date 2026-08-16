import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Next action is never consumed automatically on Dashboard load', () {
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_next_action_section.dart',
    ).readAsStringSync();
    final service = File('lib/services/companion_service.dart').readAsStringSync();

    expect(service, contains('Future<CompanionNextAction?> evaluateNextAction()'));
    expect(service, contains("/api/v1/companion/next-action/evaluate/"));
    expect(service, contains('.post('));
    expect(widget, contains('Future<void> _evaluate()'));
    expect(widget, contains('_service.evaluateNextAction()'));
    expect(widget, isNot(contains('initState()')));
    expect(widget, isNot(contains('late Future<CompanionNextAction')));
    expect(widget, contains('else if (_result == null)'));
    expect(widget, contains('_IdleBody(onPrepare: _evaluate)'));
    expect(widget, contains("ValueKey('dashboard-next-action-prepare')"));
  });

  test('Next action fail-closes unknown suggestion classes and states', () {
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_next_action_section.dart',
    ).readAsStringSync();

    expect(widget, contains("result.status == 'cooldown'"));
    expect(widget, contains("result.status == 'no_change'"));
    expect(widget, contains("result.status == 'insufficient_data'"));
    expect(widget, contains("result.status != 'suggested' || suggestion == null"));
    expect(widget, contains("'UNDERSTAND_DATA'"));
    expect(widget, contains("'MONITOR'"));
    expect(widget, contains("'PREPARE_CLINICIAN_DISCUSSION'"));
    expect(widget, contains('if (!allowed)'));
    expect(widget, contains('Icons.lock_outline_rounded'));
  });

  test('Next action routes only to bounded existing product surfaces', () {
    final widget = File(
      'lib/features/dashboard/widgets/dashboard_next_action_section.dart',
    ).readAsStringSync();

    expect(
      widget,
      contains("suggestion.suggestionClass == 'MONITOR' ? '/journal' : '/companion'"),
    );
    expect(widget, isNot(contains("'/summary'")));
    expect(widget, isNot(contains("'/reminders'")));
    expect(widget, isNot(contains('notification')));
    expect(widget, isNot(contains('schedule')));
    expect(widget, contains("ValueKey('dashboard-next-action-open')"));
  });

  test('Next action copy never presents diagnosis or treatment authority', () {
    final copy = File(
      'lib/core/localization/dashboard_next_action_localized_copy.dart',
    ).readAsStringSync();

    expect(copy, contains('Rien n’est consommé avant votre demande'));
    expect(copy, contains('Ce n’est ni un diagnostic'));
    expect(copy, contains('ni une prescription'));
    expect(copy, contains('ni une dose'));
    expect(copy, contains('ni un changement de traitement'));
  });

  test('Backend next-action boundary is POST-only and delegates existing authority', () {
    final api = File('../backend/diabetes/api/v1/companion.py').readAsStringSync();

    expect(api, contains('@router.post("/companion/next-action/evaluate/"'));
    expect(api, contains('evaluate_companion_smart_suggestion(patient_id=request.user.id)'));
    expect(api, isNot(contains('@router.get("/companion/next-action/evaluate/"')));
  });

  test('Dashboard mobile composition places next action after governed insight', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final responsive = File(
      'lib/features/dashboard/widgets/dashboard_responsive_sections.dart',
    ).readAsStringSync();

    final responsiveIndex = dashboard.indexOf('DashboardResponsiveSections(');
    final insightIndex = responsive.indexOf('DashboardInsightSection(');
    final actionIndex = responsive.indexOf('DashboardNextActionSection(');
    expect(responsiveIndex, greaterThanOrEqualTo(0));
    expect(insightIndex, greaterThanOrEqualTo(0));
    expect(actionIndex, greaterThan(insightIndex));
    expect(responsive, contains("'dashboard_next_action_section.dart'"));
  });
}
