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
}
