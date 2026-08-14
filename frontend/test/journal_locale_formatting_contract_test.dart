import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('journal date headers follow the active app locale', () {
    final source = File('lib/features/journal/journal_screen.dart').readAsStringSync();

    expect(source, isNot(contains("DateFormat('EEEE d MMMM', 'fr_FR')")));
    expect(source, contains('Localizations.localeOf(context).toLanguageTag()'));
    expect(source, contains("DateFormat('EEEE d MMMM', localeTag)"));
  });
}
