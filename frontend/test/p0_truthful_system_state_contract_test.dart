import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('sync service exposes every patient-relevant state explicitly', () {
    final source = _read('lib/services/sync_service.dart');

    for (final state in <String>[
      'checking',
      'upToDate',
      'pending',
      'syncing',
      'offline',
      'error',
    ]) {
      expect(source, contains(state), reason: 'Missing sync state: $state');
    }

    expect(source, contains('ValueNotifier<SyncUiState> state'));
    expect(source, contains('ConnectivityResult.none'));
    expect(source, contains('await _db.getPendingLogs()'));
    expect(source, contains('state.value = SyncUiState.offline'));
    expect(source, contains('state.value = SyncUiState.syncing'));
    expect(source, contains('state.value = SyncUiState.error'));
    expect(source, contains('SyncUiState.upToDate'));
  });

  test('dashboard renders only the authoritative synchronization state', () {
    final source = _read('lib/features/dashboard/widgets/top_bar.dart');
    final copy = _read('lib/l10n/audited_page_copy.dart');

    expect(source, contains('ValueListenableBuilder<SyncUiState>'));
    expect(source, contains('valueListenable: syncService.state'));

    for (final state in <String>[
      'checking',
      'upToDate',
      'pending',
      'syncing',
      'offline',
      'error',
    ]) {
      expect(
        source,
        contains("AuditedPageCopy.of(context).sync('$state')"),
        reason: 'Dashboard must localize authoritative sync state: $state',
      );
    }

    expect(copy, contains('Données à jour'));
    expect(copy, contains('Données en attente de synchronisation'));
    expect(copy, contains('Hors ligne · données conservées sur cet appareil'));
    expect(copy, contains('Échec de synchronisation · appuyer pour réessayer'));
    expect(source, isNot(contains('valueListenable: syncService.isSyncing')));
  });

  test('locally stored import data is never labelled as synchronized', () {
    final source = _read('lib/features/import/import_screen.dart');

    expect(source, contains('Stockage local'));
    expect(source, contains('Données stockées sur cet appareil'));
    expect(source, contains('Icons.storage_outlined'));
    expect(source, isNot(contains('Icons.sync_outlined')));
  });

  test('static system-success claims and decorative notifications are absent', () {
    final paths = <String>[
      'lib/features/dashboard/dashboard_screen.dart',
      'lib/features/dashboard/widgets/top_bar.dart',
      'lib/features/journal/ai_summary_screen.dart',
      'lib/features/import/import_screen.dart',
      'lib/features/profile/profile_screen.dart',
      'lib/features/navigation/main_shell.dart',
    ];
    final combined = paths.map(_read).join('\n');

    expect(combined, isNot(contains('Pilote actif')));
    expect(combined, isNot(contains('Synchronisé')));
    expect(combined, isNot(contains('notifications_none')));
    expect(combined, isNot(contains('notification_important')));
  });
}
