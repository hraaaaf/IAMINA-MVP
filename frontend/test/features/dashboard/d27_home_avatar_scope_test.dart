import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 supersedes D27 movable ChatBrain with approved single safe-lane FAB', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final wrapper = File('lib/features/dashboard/dashboard_companion_entry_screen.dart').readAsStringSync();
    final fab = File('lib/features/dashboard/widgets/dashboard_companion_fab.dart').readAsStringSync();
    final today = File('lib/features/dashboard/widgets/dashboard_today_section.dart').readAsStringSync();
    final premium = File('lib/features/dashboard/dashboard_premium_screen.dart').readAsStringSync();
    expect(module, contains("path: '/companion/chat'"));
    expect(module, contains('builder: () => const DashboardCompanionEntryScreen()'));
    expect(wrapper, contains('DashboardPremiumScreen('));
    expect(wrapper, contains('DashboardCompanionFloatingShell('));
    expect(wrapper, isNot(contains('Positioned.fill')));
    expect(wrapper, isNot(contains('DashboardCompanionAvatarAction')));
    expect(fab, contains("context.push('/companion/chat')"));
    expect(fab, isNot(contains('iamina_chatbrain_diabetes.png')));
    expect(today, isNot(contains('DashboardCompanionCallout')));
    expect(premium, isNot(contains('DashboardCompanionCallout')));
  });
}
