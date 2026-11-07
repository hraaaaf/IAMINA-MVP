import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('W03 approved single premium FAB preserves Dashboard without overlay', () {
    final wrapper = File('lib/features/dashboard/dashboard_companion_entry_screen.dart').readAsStringSync();
    final fab = File('lib/features/dashboard/widgets/dashboard_companion_fab.dart').readAsStringSync();
    final premium = File('lib/features/dashboard/dashboard_premium_screen.dart').readAsStringSync();
    final today = File('lib/features/dashboard/widgets/dashboard_today_section.dart').readAsStringSync();
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();

    expect(wrapper, contains("ValueKey('dashboard-companion-primary-entry')"));
    expect(wrapper, contains('DashboardPremiumScreen('));
    expect(wrapper, contains('DashboardCompanionFloatingShell('));
    expect(wrapper, contains('Expanded(child: child)'));
    expect(wrapper, contains('height: 78'));
    expect(wrapper, isNot(contains('Positioned.fill')));
    expect(wrapper, isNot(contains('DashboardCompanionAvatarAction')));
    expect(premium, contains('DashboardTodaySection('));
    expect(premium, contains("dashboard-first-reading-primary"));
    expect(premium, contains('const DashboardMyRemindersCard()'));
    expect(premium, isNot(contains('DashboardCompanionCallout')));
    expect(today, isNot(contains('DashboardCompanionCallout')));
    expect(fab, contains("context.push('/companion/chat')"));
    expect(fab, contains("dashboard-companion-chat-action"));
    expect(fab, contains('width: 58'));
    expect(fab, isNot(contains('iamina_chatbrain_diabetes.png')));
    expect(module, contains('const DashboardCompanionEntryScreen()'));
  });
}
