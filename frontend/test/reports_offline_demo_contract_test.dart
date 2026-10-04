import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _readReportsLibrary() => [
  File('lib/features/journal/reports_screen.dart').readAsStringSync(),
  File('lib/features/journal/reports_screen_presentation.dart').readAsStringSync(),
].join('\n');

void main() {
  test('Reports always resolves to the descriptive recorded-measurement surface', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final reports = _readReportsLibrary();

    expect(module, contains("path: '/summary'"));
    expect(module, contains('builder: () => const ReportsScreen()'));
    expect(reports, contains('return const _OfflineReportsScreen();'));
    expect(reports, isNot(contains('AISummaryScreen')));
    expect(reports, isNot(contains('kOfflineDemo')));
    expect(reports, contains('db.watchLogsInRange('));
    expect(reports, contains('_Stats.from('));
    expect(reports, isNot(contains('ApiClient')));
    expect(reports, isNot(contains('getAiSummary(')));
    expect(reports, isNot(contains('getKpis(')));
  });

  test('Report states a concise descriptive truth boundary', () {
    final reports = _readReportsLibrary();

    expect(reports, contains('Ce rapport reste descriptif'));
    expect(
      reports,
      contains('Statistiques descriptives uniquement : aucun diagnostic ni conseil de traitement.'),
    );
    expect(reports, contains('final int below;'));
    expect(reports, contains('final int inside;'));
    expect(reports, contains('final int above;'));
  });
}
