import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard has no floating ChatBrain and uses one in-flow CTA per state', () {
    final wrapper = File(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    ).readAsStringSync();
    final premium = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final today = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();
    final callout = File(
      'lib/features/dashboard/widgets/dashboard_companion_callout.dart',
    ).readAsStringSync();
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(wrapper, contains("ValueKey('dashboard-companion-primary-entry')"));
    expect(wrapper, contains('DashboardPremiumScreen('));
    expect(wrapper, isNot(contains('DashboardCompanionAvatarAction')));
    expect(wrapper, isNot(contains('Positioned.fill')));
    expect(wrapper, isNot(contains('Stack(')));
    expect(premium, contains('DashboardTodaySection('));
    expect(premium, contains('const DashboardCompanionCallout(compact: true)'));
    expect(premium, contains("dashboard-first-reading-primary"));
    expect(premium, contains('const DashboardMyRemindersCard()'));
    expect(today, contains('const DashboardCompanionCallout()'));
    expect(callout, contains("context.go('/companion/chat')"));
    expect(callout, contains("dashboard-secondary-companion"));
    expect(callout, contains("dashboard-empty-companion-secondary"));
    expect(callout, contains("IAMINA · Votre compagnon"));
    expect(callout, contains("Poser une question"));
    expect(callout, isNot(contains('iamina_chatbrain_diabetes.png')));
    expect(module, contains('const DashboardCompanionEntryScreen()'));
  });
}
