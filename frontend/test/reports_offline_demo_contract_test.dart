import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Reports route selects a local-only surface in offline demo mode', () {
    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    final reports = File(
      'lib/features/journal/reports_screen.dart',
    ).readAsStringSync();

    expect(module, contains("path: '/summary'"));
    expect(module, contains('builder: () => const ReportsScreen()'));
    expect(module, isNot(contains('builder: () => const AISummaryScreen()')));
    expect(reports, contains('if (kOfflineDemo)'));
    expect(reports, contains('const AISummaryScreen()'));
    expect(reports, contains('db.watchLogsInRange('));
    expect(reports, contains('_Stats.from('));
    expect(reports, isNot(contains('ApiClient')));
    expect(reports, isNot(contains('getAiSummary(')));
    expect(reports, isNot(contains('getKpis(')));
  });

  test('Offline report states its truth boundary instead of inventing analysis', () {
    final reports = File(
      'lib/features/journal/reports_screen.dart',
    ).readAsStringSync();

    expect(reports, contains('Ce rapport reste descriptif'));
    expect(reports, contains('ni cause, ni diagnostic, ni analyse IA avancée'));
    expect(reports, contains('final int below;'));
    expect(reports, contains('final int inside;'));
    expect(reports, contains('final int above;'));
  });
}
