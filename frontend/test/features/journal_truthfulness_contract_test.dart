import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Journal range label follows the active filter', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('_journalRangeLabel'));
    expect(source, contains('return l10n.last7Days'));
    expect(source, contains('return l10n.last30Days'));
    expect(source, contains('return l10n.allHistory'));
    expect(source, isNot(contains('subtitle: l10n.journalSubtitle')));
  });

  test('Journal converts stored mg/dL values for mmol/L display', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains("unit == 'mmol/L'"));
    expect(source, contains('(val / 18.0).toStringAsFixed(1)'));
    expect(source, contains('displayValue'));
  });

  test('Personal Response is secondary, after history, and collapsed by default', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('bool _showPersonalResponse = false'));
    expect(source, contains("Key('journal-personal-response-disclosure')"));
    expect(source, contains('if (_showPersonalResponse)'));

    final historyIndex = source.indexOf('final groupedLogs');
    final disclosureIndex = source.indexOf('journal-personal-response-disclosure');
    expect(historyIndex, greaterThanOrEqualTo(0));
    expect(disclosureIndex, greaterThan(historyIndex));
  });
}
