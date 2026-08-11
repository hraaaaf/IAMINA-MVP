import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  final header = _read('lib/core/widgets/mobile_page_header.dart');
  final dashboard = _read('lib/features/dashboard/widgets/top_bar.dart');
  final journal = _read('lib/features/journal/journal_screen.dart');
  final importer = _read('lib/features/import/import_screen.dart');
  final profile = _read('lib/features/profile/profile_screen.dart');
  final summary = _read('lib/features/journal/ai_summary_screen.dart');

  test('canonical mobile header owns hierarchy, safe area and RTL spacing', () {
    expect(header, contains('class AminaMobilePageHeader'));
    expect(header, contains('Semantics('));
    expect(header, contains('header: true'));
    expect(header, contains('MediaQuery.paddingOf(context).top'));
    expect(header, contains('EdgeInsetsDirectional.fromSTEB('));
    expect(header, contains('AlignmentDirectional.centerEnd'));
    expect(header, contains('minWidth: 44'));
    expect(header, contains('minHeight: 44'));
    expect(header, isNot(contains('EdgeInsets.fromLTRB(')));
    expect(header, isNot(contains('Positioned(left:')));
  });

  test('all five audited primary mobile surfaces use the shared header', () {
    expect(dashboard, contains('AminaMobilePageHeader('));
    expect(journal, contains('AminaMobilePageHeader('));
    expect(importer, contains('AminaMobilePageHeader('));
    expect(profile, contains('AminaMobilePageHeader('));
    expect(summary, contains('AminaMobilePageHeader('));
  });

  test('journal keeps its wide hero while mobile uses compact chrome', () {
    expect(journal, contains('MediaQuery.sizeOf(context).width < 700'));
    expect(journal, contains('expandedHeight: 140'));
    expect(journal, contains('gradient: AminaTheme.heroGradient'));
    expect(journal, contains('subtitle: l10n.journalSubtitle'));
    expect(journal, contains('iconColor: AminaTheme.textSecondary(context)'));
  });

  test('dashboard keeps controls inside the canonical compact hierarchy', () {
    expect(dashboard, contains('title: copy.overview'));
    expect(dashboard, contains('trailing: _syncButton()'));
    expect(dashboard, contains('_RangeChips(range: range'));
    expect(
      dashboard,
      contains('_ParlerButton(onTap: onChatTap, compact: true)'),
    );
  });

  test(
    'profile removes stock AppBar only on mobile and desktop stays intact',
    () {
      expect(
        profile,
        contains('final isMobile = MediaQuery.sizeOf(context).width < 700'),
      );
      expect(
        profile,
        contains('if (isMobile) AminaMobilePageHeader(title: l10n.myProfile)'),
      );
      expect(
        profile,
        contains('AppBar(title: Text(l10n.myProfile), centerTitle: true)'),
      );
    },
  );

  test(
    'summary period selection remains reachable in shared mobile chrome',
    () {
      expect(summary, contains('title: l10n.navIamina'));
      expect(summary, contains("label: '7 \${l10n.dayShort}'"));
      expect(summary, contains("label: '21 \${l10n.dayShort}'"));
      expect(summary, contains("label: '90 \${l10n.dayShort}'"));
      expect(summary, contains('AlignmentDirectional.centerStart'));
    },
  );
}
