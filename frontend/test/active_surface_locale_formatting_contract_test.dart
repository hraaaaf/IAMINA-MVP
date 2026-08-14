import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Medication and Reminder active surfaces use locale-aware date formatting', () {
    final medication = File(
      'lib/features/medications/medication_screen.dart',
    ).readAsStringSync();
    final reminders = File(
      'lib/features/reminders/reminders_screen.dart',
    ).readAsStringSync();
    final helper = File(
      'lib/core/localization/locale_formatting.dart',
    ).readAsStringSync();

    for (final source in <String>[medication, reminders]) {
      expect(source, isNot(contains("DateFormat('dd/MM/yyyy HH:mm')")));
      expect(source, contains('formatLocalizedDateTime(context,'));
    }

    expect(helper, contains('Localizations.localeOf(context).toLanguageTag()'));
    expect(helper, contains('DateFormat.yMd(locale).add_Hm()'));
  });
}
