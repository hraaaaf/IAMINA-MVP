import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('first-use dashboard distinguishes loading, error and empty states', () {
    final source = _read('lib/features/dashboard/dashboard_screen.dart');

    expect(source, contains('localDataLoading'));
    expect(source, contains('localDataError'));
    expect(source, contains('_DashboardLocalState'));
    expect(source, contains('dashboardLoadingTitle'));
    expect(source, contains('dashboardLoadErrorTitle'));
    expect(source, contains('SyncUiState.offline'));
  });

  test('empty dashboard prioritizes real acquisition without fake metrics', () {
    final source = _read('lib/features/dashboard/dashboard_screen.dart');

    expect(source, contains('addFirstMeasurement'));
    expect(source, contains('importDocument'));
    expect(source, contains('firstUseTruthNote'));
    expect(source, contains("go('/ajouter')"));
    expect(source, contains("go('/importer')"));
    expect(source, isNot(contains("Text('🩺'")));
    expect(source, isNot(contains('_FeaturePill')));
  });

  test('first-use copy exists in FR AR and EN', () {
    for (final file in ['app_fr.arb', 'app_ar.arb', 'app_en.arb']) {
      final arb = _read('lib/l10n/$file');
      expect(arb, contains('dashboardLoadingTitle'));
      expect(arb, contains('dashboardLoadErrorTitle'));
      expect(arb, contains('firstUseTruthNote'));
    }
  });

  test('desktop and short-height first-use layouts are explicit', () {
    final source = _read('lib/features/dashboard/dashboard_screen.dart');

    expect(source, contains('wideFirstUse'));
    expect(source, contains('constraints.maxWidth >= 720'));
    expect(source, contains('compactHeight'));
    expect(source, contains('AlignmentDirectional'));
  });
}
