import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decision #2 reserves the notification bell for real notifications', () {
    final dashboard = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    const marker = "key: const ValueKey('dashboard-reminders-action')";
    final offset = dashboard.indexOf(marker);
    expect(offset, greaterThanOrEqualTo(0));
    final reminderAction = dashboard.substring(offset, offset + 360);

    expect(reminderAction, contains("context.go('/reminders')"));
    expect(reminderAction, contains('Icons.event_note_outlined'));
    expect(reminderAction, isNot(contains('Icons.notifications')));
    expect(reminderAction, contains('tooltip: _t(context'));
    expect(reminderAction, contains("'Rappels'"));
    expect(reminderAction, contains("'Reminders'"));
    expect(reminderAction, contains("'التذكيرات'"));
  });

  test('decision #2 does not misrepresent local reminders as OS push', () {
    final reminders = File(
      'lib/features/reminders/reminders_screen.dart',
    ).readAsStringSync();
    expect(reminders, contains('notifications système ne sont pas activées'));
    expect(reminders, contains('System notifications are not enabled'));
    expect(reminders, contains("Icons.event_note_outlined"));
  });
}
