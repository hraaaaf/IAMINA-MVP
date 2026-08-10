import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('shell exposes the actual post-sidebar viewport to routed pages', () {
    final shell = _read('lib/features/navigation/main_shell.dart');
    expect(shell, contains('LayoutBuilder('));
    expect(
      shell,
      contains('size: Size(constraints.maxWidth, constraints.maxHeight)'),
    );
  });

  test(
    'dashboard keeps first-use copy readable while data views gain width',
    () {
      final dashboard = _read('lib/features/dashboard/dashboard_screen.dart');
      expect(
        RegExp(
          r'BoxConstraints\(\s*maxWidth:\s*900,?\s*\)',
        ).hasMatch(dashboard),
        isTrue,
      );
      expect(
        RegExp(
          r'screenW\s*>=\s*1400\s*\?\s*\(screenW\s*-\s*1200\)\s*/\s*2',
        ).hasMatch(dashboard),
        isTrue,
      );
    },
  );

  test('journal caps long-history reading width on desktop', () {
    final journal = _read('lib/features/journal/journal_screen.dart');
    expect(journal, contains('(viewportWidth - 980) / 2'));
    expect(journal, contains('viewportWidth >= 700'));
  });

  test('importer uses a desktop two-column connection layout', () {
    final source = _read('lib/features/import/import_screen.dart');
    expect(source, contains('ResponsiveContentSurface('));
    expect(source, contains('maxWidth: 1160'));
    expect(source, contains('constraints.maxWidth >= 900'));
    expect(source, contains('Expanded(child: cards[0])'));
    expect(source, contains('Expanded(child: cards[1])'));
  });

  test(
    'profile and Pulper cap over-wide desktop bodies without shrinking tablet',
    () {
      final profile = _read('lib/features/profile/profile_screen.dart');
      final pulper = _read(
        'lib/features/documents/document_import_screen.dart',
      );
      final surface = _read('lib/core/widgets/responsive_content_surface.dart');
      expect(profile, contains('maxWidth: 1040'));
      expect(pulper, contains('maxWidth: 980'));
      expect(surface, contains('math.min(constraints.maxWidth, maxWidth)'));
      expect(surface, contains('AlignmentDirectional.topCenter'));
    },
  );
}
