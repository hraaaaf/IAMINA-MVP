import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Dashboard latest reading is not limited to a 21-day window', () {
    final source = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    expect(source, contains('db.watchRecentLogs(limit: 1)'));
    expect(source, isNot(contains('watchLogsInRange(start, now)')));
    expect(source, isNot(contains('Duration(days: 21)')));
  });
}
