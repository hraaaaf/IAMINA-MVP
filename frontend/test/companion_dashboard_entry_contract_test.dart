import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('dashboard primary insight opens companion without changing nav', () {
    final source = File(
      'lib/features/dashboard/dashboard_convergent_screen.dart',
    ).readAsStringSync();

    expect(source, contains("ValueKey('dashboard-companion-insight')"));
    expect(
      source,
      contains("onTap: () => GoRouter.of(context).go('/companion')"),
    );
  });

  test('mobile dashboard exposes a persistent visible IAmina companion entry', () {
    final wrapper = File(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    ).readAsStringSync();
    final premium = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(wrapper, contains("ValueKey('dashboard-companion-primary-entry')"));
    expect(wrapper, contains('DashboardPremiumScreen'));
    expect(premium, contains("context.go('/companion')"));
    expect(premium, contains("'Compagnon'"));
    expect(module, contains('const DashboardCompanionEntryScreen()'));
  });
}
