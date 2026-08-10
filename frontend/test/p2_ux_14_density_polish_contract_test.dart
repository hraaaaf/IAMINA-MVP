import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test(
    'summary error uses a proportionate wide composition without harming mobile',
    () {
      final source = _read('lib/features/journal/ai_summary_screen.dart');
      expect(source, contains('constraints.maxWidth >= 720'));
      expect(source, contains('BoxConstraints(maxWidth: 820)'));
      expect(source, contains('SizedBox(width: 210, child: retry)'));
      expect(source, contains('return Center('));
      expect(source, contains('alignment: Alignment.topCenter'));
      expect(source, contains('BoxConstraints(maxWidth: 420)'));
      expect(source, contains('minimumSize: const Size.fromHeight(48)'));
    },
  );

  test(
    'journal wide empty state stays attached to the readable content region',
    () {
      final source = _read('lib/features/journal/journal_screen.dart');
      expect(source, contains('(viewportWidth - 980) / 2'));
      expect(source, contains('viewportWidth < 700'));
      expect(source, contains('BoxConstraints(maxWidth: 560)'));
      expect(source, contains('ClinicalCard('));
      expect(source, contains('AlignmentDirectional.topCenter'));
    },
  );

  test(
    'profile desktop groups progressive sections with shared clinical surfaces',
    () {
      final source = _read('lib/features/profile/profile_screen.dart');
      expect(source, contains('maxWidth: 1040'));
      expect(source, contains('constraints.maxWidth < 900'));
      expect(source, contains("ValueKey('profile-desktop-health-column')"));
      expect(source, contains("ValueKey('profile-desktop-account-column')"));
      expect(source, contains('BorderRadius.circular(AminaTheme.radius3XL)'));
      expect(source, contains('BorderRadius.circular(AminaTheme.radius2XL)'));
      expect(source, contains('boxShadow: AminaTheme.shadowClinical'));
      expect(
        source,
        isNot(contains('borderRadius: BorderRadius.circular(18)')),
      );
    },
  );

  test('P0 desktop density contracts remain intact', () {
    final importer = _read('lib/features/import/import_screen.dart');
    expect(importer, contains('maxWidth: 1160'));
    expect(importer, contains('constraints.maxWidth >= 900'));
    expect(importer, contains('Expanded(child: cards[0])'));
    expect(importer, contains('Expanded(child: cards[1])'));
  });
}
