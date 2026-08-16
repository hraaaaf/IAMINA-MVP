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
        final line =
            '\n'.allMatches(source.substring(0, match.start)).length + 1;
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
    expect(
      RegExp(
        r'db\s*\.\s*into\(db\.logEntries\)\s*\.\s*insert\s*\(',
      ).hasMatch(add),
      isTrue,
    );
    expect(journal, contains("context.push('/journal/\${log.id}/edit')"));
    expect(journal, contains('db.deleteLog(log.id)'));
  });

  test(
    'mobile navigation exposes approved destinations while Import stays reachable',
    () {
      final module = _read('lib/modules/diabetes_module.dart');
      final shell = _read('lib/features/navigation/main_shell.dart');
      final dashboard = _read(
        'lib/features/dashboard/dashboard_convergent_screen.dart',
      );

      expect(module, contains("route: '/importer'"));
      expect(shell, contains("entry.route != '/importer'"));
      expect(shell, contains('_GlassNavDestination('));
      expect(shell, contains('entry: mobileEntries[index]'));
      expect(shell, contains("ValueKey('mobile-nav-\${entry.route}')"));
      expect(
        RegExp(
          r'GoRouter\.of\(\s*context,?\s*\)\s*\.go\(mobileEntries\[index\]\.route\)',
        ).hasMatch(shell),
        isTrue,
      );
      expect(shell, contains("GoRouter.of(context).go('/ajouter')"));
      expect(dashboard, contains("ValueKey('dashboard-reminders-action')"));
      expect(dashboard, contains("GoRouter.of(context).go('/reminders')"));
    },
  );

  test('CGM integrations expose real governed actions without fake availability', () {
    final importer = _read('lib/features/import/import_screen.dart');
    final cgm = _read('lib/features/import/cgm_connections_section.dart');
    final service = _read('lib/services/cgm_service.dart');

    expect(importer, contains('const CgmConnectionsSection()'));
    expect(cgm, contains("id: 'dexcom'"));
    expect(cgm, contains("id: 'libre'"));
    expect(cgm, contains("id: 'linx'"));
    expect(cgm, contains('OutlinedButton('));
    expect(cgm, contains('FilledButton.icon('));
    expect(cgm, contains('TextButton(onPressed: _disconnect'));
    expect(cgm, isNot(contains('Notifiez-moi')));
    expect(cgm, isNot(contains("rejoignez la liste d'attente")));
    expect(service, contains('class CgmService'));
    expect(service, contains('Future<CgmConnectionState> getConnection'));
    expect(service, contains('Future<CgmConnectionState> configure'));
    expect(service, contains('Future<CgmSyncResult> sync'));
  });

  test('summary contains no fallback dose or basal adjustment advice', () {
    final summary = _read('lib/features/journal/ai_summary_screen.dart');
    final localizedCopy =
        _read('lib/core/localization/ai_summary_localized_copy.dart');
    final combined = '$summary\n$localizedCopy';
    const forbidden = <String>[
      'Diviser la dose repas glucidique',
      'Fractionner bolus avant et après le repas',
      'Basale nocturne −15 %',
      "PLAN D'ACTION",
      'Recommandation :',
      'notifications_none',
      'class _ActionBtn',
    ];

    for (final phrase in forbidden) {
      expect(
        combined,
        isNot(contains(phrase)),
        reason: 'Forbidden UI contract: $phrase',
      );
    }
    expect(summary, contains('l10n.discussionPoints'));
    expect(summary, contains('l10n.discussionSuggestion(card.action)'));
    expect(localizedCopy, contains('POINTS À DISCUTER'));
    expect(localizedCopy, contains('Piste à discuter :'));
    expect(summary, contains('onDiscoverTap: _scrollToInsights'));
  });
}
