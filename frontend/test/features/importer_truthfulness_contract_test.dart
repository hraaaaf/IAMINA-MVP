import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Importer latest reading uses effective event time, not row creation order', () {
    final source = File('lib/features/import/import_screen.dart').readAsStringSync();

    expect(source, contains('final rows = await db.select(db.logEntries).get();'));
    expect(source, contains('final occurredAt = row.loggedAt ?? row.createdAt;'));
    expect(source, contains('occurredAt.isAfter(lastLogAt)'));
    expect(source, contains('_lastLogAt = lastLogAt;'));
    expect(source, isNot(contains('OrderingTerm.desc(t.createdAt)')));
  });

  test('Importer does not invent a three-day stale warning', () {
    final source = File('lib/features/import/import_screen.dart').readAsStringSync();

    expect(source, isNot(contains('_isDataStale')));
    expect(source, isNot(contains('staleDataTitle')));
    expect(source, isNot(contains('staleDataBody')));
    expect(source, isNot(contains('Duration(days: 3)')));
    expect(source, contains('latestReadingStoredLocally(label)'));
  });
}
