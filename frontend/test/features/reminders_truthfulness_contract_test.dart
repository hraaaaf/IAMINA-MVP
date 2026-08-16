import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('reminders do not expose an enabled switch without system notifications', () {
    final source = _read('lib/features/reminders/reminders_screen.dart');

    expect(source, contains('notifications système ne sont pas activées'));
    expect(source, isNot(contains('Switch(')));
    expect(source, isNot(contains('setReminderEnabled(')));
    expect(source, contains('Icons.event_note_outlined'));
  });

  test('reminder deletion requires confirmation', () {
    final source = _read('lib/features/reminders/reminders_screen.dart');

    expect(source, contains('Future<void> _confirmDeleteReminder'));
    expect(source, contains('showDialog<bool>'));
    expect(source, contains('if (confirmed == true) await db.deleteReminder(item.id);'));
    expect(source, contains('_confirmDeleteReminder(db, item)'));
  });
}
