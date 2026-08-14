import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard companion context follows the active locale', () {
    final source = File('lib/features/dashboard/dashboard_screen.dart').readAsStringSync();
    expect(source, isNot(contains('Ma dernière mesure est')));
    expect(source, contains('dashboardChatContext('));
    expect(source, contains('_buildChatContext(BuildContext context)'));
  });

  test('Dashboard supplemental copy keeps explicit EN FR AR parity', () {
    final copy = File('lib/core/localization/dashboard_localized_copy.dart').readAsStringSync();
    expect(copy, contains("'ar' => ar"));
    expect(copy, contains("'fr' => fr"));
    expect(copy, contains('_ => en'));
  });
}
