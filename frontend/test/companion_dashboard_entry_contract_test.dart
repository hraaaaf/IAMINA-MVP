import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('dashboard primary companion actions use the canonical Today section', () {
    final today = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();

    expect(today, contains("ValueKey('dashboard-secondary-companion')"));
    expect(today, contains("context.go('/companion')"));
  });

  test('mobile dashboard exposes a persistent visible IAmina companion entry', () {
    final wrapper = File(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    ).readAsStringSync();
    final premium = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final today = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(wrapper, contains("ValueKey('dashboard-companion-primary-entry')"));
    expect(wrapper, contains('DashboardPremiumScreen'));
    expect(premium, contains('DashboardTodaySection('));
    expect(today, contains("context.go('/companion')"));
    expect(today, contains("ValueKey('dashboard-secondary-companion')"));
    expect(module, contains('const DashboardCompanionEntryScreen()'));
  });
}
