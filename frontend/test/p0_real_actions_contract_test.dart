import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

const _patientFacingSources = <String>[
  'lib/features/dashboard/dashboard_screen.dart',
  'lib/features/dashboard/widgets/top_bar.dart',
  'lib/features/dashboard/widgets/add_log_sheet.dart',
  'lib/features/journal/journal_screen.dart',
  'lib/features/journal/ai_summary_screen.dart',
  'lib/features/journal/edit_log_screen.dart',
  'lib/features/import/import_screen.dart',
  'lib/features/profile/profile_screen.dart',
  'lib/features/navigation/main_shell.dart',
];

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('patient-facing controls never use empty callbacks', () {
    final emptyCallback = RegExp(
      r'on(?:Tap|Pressed):\s*\(\)\s*\{\s*\}',
      multiLine: true,
    );
    final failures = <String>[];

    for (final path in _patientFacingSources) {
      final source = _read(path);
      for (final match in emptyCallback.allMatches(source)) {
        final line = '\n'.allMatches(source.substring(0, match.start)).length + 1;
        failures.add('$path:$line has an empty patient-facing callback');
      }
    }

    expect(failures, isEmpty, reason: failures.join('\n'));
  });

  test('the core add-view-edit-delete loop is wired to persisted data', () {
    final module = _read('lib/modules/diabetes_module.dart');
    final add = _read('lib/features/dashboard/widgets/add_log_sheet.dart');
    final journal = _read('lib/features/journal/journal_screen.dart');

    expect(module, contains("path: '/ajouter'"));
    expect(module, contains("path: '/journal/:id/edit'"));
    expect(add, contains('db.into(db.logEntries).insert'));
    expect(journal, contains("context.push('/journal/\${log.id}/edit')"));
    expect(journal, contains('db.deleteLog(log.id)'));
  });

  test('mobile navigation derives every destination including Importer', () {
    final module = _read('lib/modules/diabetes_module.dart');
    final shell = _read('lib/features/navigation/main_shell.dart');

    expect(module, contains("route: '/importer'"));
    expect(shell, contains('for (final e in entries)'));
    expect(shell, contains('NavigationDestination('));
    expect(shell, contains('onDestinationSelected:'));
  });

  test('unavailable integrations cannot masquerade as active actions', () {
    final import = _read('lib/features/import/import_screen.dart');
    final frenchArb = _read('lib/l10n/app_fr.arb');
    final adapter = _read('lib/l10n/audited_page_copy.dart');

    expect(import, isNot(contains('Notifiez-moi')));
    expect(import, isNot(contains('rejoignez la liste d\'attente')));
    expect(import, contains('AuditedPageCopy.of(context).unavailable'));
    expect(import, contains('AuditedPageCopy.of(context).dexcomDescription'));
    expect(import, contains('AuditedPageCopy.of(context).libreDescription'));
    expect(import, contains('action: const _UnavailableAction()'));
    expect(frenchArb, contains('Non disponible'));
    expect(frenchArb, contains('à confirmer avant activation'));
    expect(adapter, contains('l10n.unavailable'));
    expect(adapter, contains('l10n.dexcomDescription'));
    expect(adapter, contains('l10n.libreDescription'));
  });

  test('summary contains no fallback dose or basal adjustment advice', () {
    final summary = _read('lib/features/journal/ai_summary_screen.dart');
    const forbidden = <String>[
      'Diviser la dose repas glucidique',
      'Fractionner bolus avant et après le repas',
      'Basale nocturne −15 %',
      'PLAN D\'ACTION',
      'Recommandation :',
      'notifications_none',
      'class _ActionBtn',
    ];

    for (final phrase in forbidden) {
      expect(summary, isNot(contains(phrase)), reason: 'Forbidden UI contract: $phrase');
    }
    expect(summary, contains('POINTS À DISCUTER'));
    expect(summary, contains('Piste à discuter :'));
    expect(summary, contains('onDiscoverTap: _scrollToInsights'));
  });
}
