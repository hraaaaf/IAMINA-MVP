import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test(
    'summary degraded state preserves a focal wide composition without harming mobile',
    () {
      final source = _read('lib/features/journal/ai_summary_screen.dart');
      expect(source, contains('constraints.maxWidth >= 720'));
      expect(source, contains('AlignmentDirectional.topStart'));
      expect(source, contains('maxWidth: isWide ? 960 : 520'));
      expect(source, contains('_GreetingHeader(periodDays: _periodDays)'));
      expect(source, contains('SizedBox(width: 190, child: retry)'));
      expect(source, contains('minimumSize: const Size.fromHeight(48)'));
      expect(source, isNot(contains('const Alignment(0, -0.30)')));
      expect(source, isNot(contains('maxWidth: isWide ? 480 : 420')));
    },
  );

  test(
    'journal wide empty state stays attached to the readable content region',
    () {
      final source = _read('lib/features/journal/journal_screen.dart');
      expect(source, contains('(viewportWidth - 980) / 2'));
      expect(source, contains('viewportWidth < 700'));
      expect(source, contains('BoxConstraints(maxWidth: 720)'));
      expect(source, contains('AminaFirstUsePanel('));
      expect(source, contains('AlignmentDirectional.topCenter'));
      expect(source, contains('PersonalResponseSection(unit: unit)'));
    },
  );

  test(
    'profile desktop groups progressive sections with shared clinical surfaces',
    () {
      final source = _read('lib/features/profile/profile_screen.dart');
      expect(source, contains('maxWidth: 1040'));
      expect(source, contains('constraints.maxWidth < 900'));
      expect(
        RegExp(
          r'BorderRadius\.circular\(\s*AminaTheme\.radius3XL,?\s*\)',
        ).hasMatch(source),
        isTrue,
      );
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
    final cgm = _read('lib/features/import/cgm_connections_section.dart');
    expect(importer, contains('maxWidth: 1160'));
    expect(importer, contains('const CgmConnectionsSection()'));
    expect(cgm, contains('constraints.maxWidth >= 900'));
    expect(cgm, contains('Expanded(child: cards[i])'));
  });
}
