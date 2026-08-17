import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('shared first-use panel is directional, semantic and action safe', () {
    final source = _read('lib/core/widgets/first_use_panel.dart');
    expect(source, contains('class AminaFirstUsePanel'));
    expect(source, contains('EdgeInsetsDirectional.fromSTEB'));
    expect(source, contains('Semantics('));
    expect(source, contains('minimumSize: const Size.fromHeight(48)'));
    expect(
      source,
      contains('shortViewport = MediaQuery.sizeOf(context).height <= 600'),
    );
    expect(source, isNot(contains('mg/dL')));
    expect(source, isNot(contains('mmol/L')));
    expect(source, isNot(contains('GMI')));
  });

  test('dashboard first-use uses real add/import actions and truth note', () {
    final source = _read('lib/features/dashboard/dashboard_screen.dart');
    expect(source, contains('AminaFirstUsePanel('));
    expect(source, contains('emptyDashboardTitle'));
    expect(source, contains('emptyDashboardBody'));
    expect(source, contains('addFirstMeasurement'));
    expect(source, contains('importDocument'));
    expect(source, contains('firstUseTruthNote'));
    expect(source, contains("go('/ajouter')"));
    expect(source, contains("go('/importer')"));
  });

  test('journal hides longitudinal response before a first real log', () {
    final source = _read('lib/features/journal/journal_screen.dart');
    expect(source, contains('final logs = snapshot.data ?? []'));
    expect(source, contains('if (logs.isEmpty)'));
    expect(source, contains('_buildEmptyJournalSliver('));
    expect(source, contains('_buildPersonalResponseSliver(unit, horizontalPadding)'));
    expect(source, contains('PersonalResponseSection(unit: unit)'));
    expect(source, contains('AminaFirstUsePanel('));
    expect(source, contains('BoxConstraints(maxWidth: 720)'));
    expect(source, contains("context.go('/ajouter')"));
    expect(source, contains("context.go('/importer')"));

    final emptyGuard = source.indexOf('if (logs.isEmpty)');
    final emptyReturn = source.indexOf('_buildEmptyJournalSliver(', emptyGuard);
    final responsePlacement = source.indexOf(
      '_buildPersonalResponseSliver(unit, horizontalPadding)',
      emptyReturn,
    );
    expect(emptyGuard, greaterThanOrEqualTo(0));
    expect(emptyReturn, greaterThan(emptyGuard));
    expect(responsePlacement, greaterThan(emptyReturn));
  });

  test(
    'importer first-use leads to document review and exposes real CGM connectors',
    () {
      final importer = _read('lib/features/import/import_screen.dart');
      final cgm = _read('lib/features/import/cgm_connections_section.dart');
      expect(importer, contains('if (_totalLogs == 0)'));
      expect(importer, contains("ValueKey('import-first-use')"));
      expect(importer, contains('.documentIntro'));
      expect(importer, contains('.chooseDocument'));
      expect(importer, contains("context.push('/pulper')"));
      expect(importer, contains('const CgmConnectionsSection()'));
      expect(cgm, contains('Dexcom G6/G7'));
      expect(cgm, contains('FreeStyle Libre'));
      expect(cgm, contains('LinX / AiDEX X'));
      expect(cgm, contains('OutlinedButton('));
      expect(cgm, isNot(contains('const _UnavailableAction()')));
    },
  );

  test('profile first-use guides but never auto-saves medical defaults', () {
    final source = _read('lib/features/profile/profile_screen.dart');
    expect(source, contains('if (!_hasPersistedProfile)'));
    expect(source, contains("ValueKey('profile-first-use')"));
    expect(source, contains('.profileCompletionPrompt'));
    expect(source, contains('initiallyExpanded: false'));
    final firstUseStart = source.indexOf("ValueKey('profile-first-use')");
    final medicalStart = source.indexOf(
      '_buildMedicalSection(l10n)',
      firstUseStart,
    );
    final firstUseBlock = source.substring(firstUseStart, medicalStart);
    expect(firstUseBlock, isNot(contains('_saveProfile')));
  });

  test('summary distinguishes no local data from a retrieval failure', () {
    final source = _read('lib/features/journal/ai_summary_screen.dart');
    expect(source, contains('final count = await db.countLogs()'));
    expect(source, contains('_hasLocalLogs = count > 0'));
    expect(source, contains('_hasLocalLogs == false'));
    expect(source, contains('_buildFirstUse()'));
    expect(source, contains('_buildError()'));
    expect(source, contains('AminaFirstUsePanel('));
    expect(source, contains("context.go('/ajouter')"));
    expect(source, contains("context.go('/importer')"));
    expect(source, contains('analysisLoadError'));
  });
}
