import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 supersedes D27 floating avatar on Home without changing chat route', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final wrapper = File(
      'lib/features/dashboard/dashboard_companion_entry_screen.dart',
    ).readAsStringSync();
    final today = File(
      'lib/features/dashboard/widgets/dashboard_today_section.dart',
    ).readAsStringSync();
    final premium = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    expect(module, contains("path: '/companion/chat'"));
    expect(module, contains('builder: () => const DashboardCompanionEntryScreen()'));
    expect(wrapper, contains('DashboardPremiumScreen('));
    expect(wrapper, isNot(contains('DashboardCompanionAvatarAction')));
    expect(wrapper, isNot(contains('FloatingActionButton')));
    expect(wrapper, isNot(contains('Positioned.fill')));
    expect(today, contains('const DashboardCompanionCallout()'));
    expect(premium, contains('const DashboardCompanionCallout(compact: true)'));
  });
}
