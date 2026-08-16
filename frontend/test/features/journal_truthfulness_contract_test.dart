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

  test('Journal exposes all three range choices directly below the header', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('_buildFilterChips(horizontalPadding)'));
    expect(source, contains('journal-range-'));
    expect(source, contains('(7, l10n.last7Days)'));
    expect(source, contains('(30, l10n.last30Days)'));
    expect(source, contains('(0, l10n.allHistory)'));
    expect(source, contains('ChoiceChip('));
    expect(source, isNot(contains('PopupMenuButton<int>')));
  });

  test('Journal all-history includes legacy rows without loggedAt', () {
    final screen = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();
    final queries = File(
      'lib/features/journal/journal_queries.dart',
    ).readAsStringSync();

    expect(screen, contains('db.watchAllJournalLogs()'));
    expect(screen, contains('db.watchJournalLogsInRange('));
    expect(screen, isNot(contains('DateTime(2000)')));
    expect(queries, contains('t.loggedAt.isNull()'));
    expect(queries, contains('t.createdAt.isBetweenValues(start, end)'));
  });

  test('Journal empty state offers add and import paths', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('primaryActionLabel: l10n.addMeasurement'));
    expect(source, contains("onPrimaryAction: () => context.go('/ajouter')"));
    expect(source, contains('secondaryActionLabel: l10n.navImport'));
    expect(source, contains("onSecondaryAction: () => context.go('/importer')"));
  });

  test('Journal converts stored mg/dL values for mmol/L display', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains("unit == 'mmol/L'"));
    expect(source, contains('(val / 18.0).toStringAsFixed(1)'));
    expect(source, contains('displayValue'));
    expect(source, contains("Key('journal-glucose-unit')"));
  });

  test('Journal keeps meal context compact in history rows', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('mealLabels.take(2)'));
    expect(source, contains("Key('journal-meal-summary')"));
    expect(source, contains('maxLines: 1'));
    expect(source, contains('TextOverflow.ellipsis'));
    expect(source, isNot(contains('Wrap(\n                          spacing: 4')));
  });

  test('Journal life-context icons have readable semantics', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('final String label'));
    expect(source, contains('return Semantics('));
    expect(source, contains('label: label'));
    expect(source, contains('ExcludeSemantics('));
    expect(source, contains("label: l10n.sick"));
    expect(source, contains("label: l10n.stressed"));
    expect(source, contains("label: l10n.fatigue"));
  });

  test('Journal signals that tapping a row opens details', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains("context.push('/journal/\${log.id}/edit')"));
    expect(source, contains('Icons.chevron_right_rounded'));
    expect(source, contains("Key('journal-entry-details-chevron')"));
  });

  test('Journal detail exposes confirmed deletion as well as swipe delete', () {
    final source = File(
      'lib/features/journal/edit_log_screen.dart',
    ).readAsStringSync();

    expect(source, contains("Key('delete-edit-log-button')"));
    expect(source, contains('Future<void> _deleteLog'));
    expect(source, contains('l10n.actionIrreversible'));
    expect(source, contains('await db.deleteLog(widget.logId)'));
    expect(source, contains('Navigator.of(context).maybePop()'));
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

  test('Journal shows sync state only when user attention is needed', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains("if (status == 'pending')"));
    expect(source, contains("if (status == 'error')"));
    expect(source, contains('return const SizedBox.shrink();'));
    expect(source, isNot(contains('Icons.cloud_done_outlined')));
    expect(source, isNot(contains('Icons.cloud_off_outlined')));
  });

  test('Journal reserves red for hypoglycemia and uses target range for highs', () {
    final source = File(
      'lib/features/journal/journal_screen.dart',
    ).readAsStringSync();

    expect(source, contains('if (val < 70)'));
    expect(source, contains('else if (val < low || val > high)'));
    expect(source, isNot(contains('val < 70 || val > 250')));
  });
}
