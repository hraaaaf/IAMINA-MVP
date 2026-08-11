import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('360px dashboard removes redundant FAB on first-use state', () {
    final source = _read('lib/features/dashboard/dashboard_screen.dart');
    final firstUse = _read('lib/core/widgets/first_use_panel.dart');
    expect(source, contains('screenW >= 720 || logs.isEmpty'));
    expect(
      RegExp(r'BoxConstraints\(\s*maxWidth:\s*900,?\s*\)').hasMatch(source),
      isTrue,
    );
    expect(source, contains('emptyDashboardTitle'));
    expect(source, contains('emptyDashboardBody'));
    expect(
      firstUse,
      contains('shortViewport = MediaQuery.sizeOf(context).height <= 600'),
    );
    expect(firstUse, contains('minimumSize: const Size.fromHeight(48)'));
    expect(source, isNot(contains("'Commencez votre suivi'")));
    expect(source, isNot(contains("'Ajouter ma première mesure'")));
  });

  test(
    'short-screen profile sign-out sheet is scroll controlled and safe-area aware',
    () {
      final source = _read('lib/features/profile/profile_screen.dart');
      final signOutStart = source.indexOf('void _confirmSignOut()');
      final withdrawStart = source.indexOf('void _confirmWithdrawConsent');
      final block = source.substring(signOutStart, withdrawStart);
      expect(block, contains('isScrollControlled: true'));
      expect(block, contains('useSafeArea: true'));
      expect(block, contains('SingleChildScrollView'));
    },
  );

  test('certified offline IAmina states are localized', () {
    final source = _read('lib/features/journal/ai_summary_screen.dart');
    expect(source, contains('analysisLoadError'));
    expect(source, contains('analysisLoading'));
    expect(source, contains('analysisLoadingWait'));
    expect(source, contains('.retry'));
    expect(
      source,
      contains('final isCompact = MediaQuery.sizeOf(context).width < 600'),
    );
    expect(source, contains('AminaMobilePageHeader('));
    expect(source, contains('title: l10n.navIamina'));
    expect(source, contains('l10n.breadcrumb'));
    expect(source, isNot(contains('floatingActionButton: _ChatFab')));
    expect(source, contains('copy.greeting(hour, name)'));
    expect(source, contains('copy.observation(periodDays)'));
    expect(source, isNot(contains("'Impossible de récupérer les analyses.'")));
    expect(source, isNot(contains("'Réessayer'")));
  });

  test('Arabic ARB owns the small-screen first-use and error copy', () {
    final ar = _read('lib/l10n/app_ar.arb');
    expect(ar, contains('\"dayShort\": \"يوم\"'));
    for (final key in <String>[
      'emptyDashboardTitle',
      'emptyDashboardBody',
      'addFirstMeasurement',
      'importDocument',
      'analysisLoadError',
      'retry',
    ]) {
      expect(ar, contains('"$key"'));
    }
  });
}
