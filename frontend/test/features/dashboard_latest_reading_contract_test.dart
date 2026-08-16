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

  test('Dashboard latest reading exposes exact timestamp and freshness', () {
    final source = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();

    expect(source, contains('_latestReadingFreshnessLabel'));
    expect(source, contains('DateTime.now().difference(latestAt)'));
    expect(
      source,
      contains("ValueKey('dashboard-latest-reading-timestamp')"),
    );
    expect(
      source,
      contains("ValueKey('dashboard-latest-reading-freshness')"),
    );
    expect(source, contains('dashboardLatestKnownReading'));
  });

  test('Dashboard target status fails closed without a configured profile', () {
    final source = File(
      'lib/features/dashboard/dashboard_premium_screen.dart',
    ).readAsStringSync();
    final localizedCopy = File(
      'lib/core/localization/dashboard_localized_copy.dart',
    ).readAsStringSync();

    expect(source, isNot(contains('targetRangeLow ?? 70.0')));
    expect(source, isNot(contains('targetRangeHigh ?? 180.0')));
    expect(source, contains('hasConfiguredTarget'));
    expect(source, contains('dashboardTargetNotConfigured'));
    expect(source, contains('targetConfigured: hasTarget'));
    expect(localizedCopy, contains('dashboardTargetNotConfigured'));
  });
}
