import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

String _readDocumentImportLibrary() => [
  _read('lib/features/documents/document_import_screen.dart'),
  _read('lib/features/documents/document_import_screen_presentation.dart'),
].join('\n');

void main() {
  test('Importer opens the document task directly without becoming a root', () {
    final module = _read('lib/modules/diabetes_module.dart');
    final premium = _read(
      'lib/features/documents/document_import_premium_screen.dart',
    );
    final navBlock = module.split('shellRoutes:').first;

    expect(navBlock, isNot(contains("route: '/importer'")));
    expect(module, contains("path: '/importer'"));
    expect(module, contains("path: '/pulper'"));
    expect(module, isNot(contains("import '../features/import/import_screen.dart';")));
    expect(module, isNot(contains('builder: (s) => const ImportScreen()')));
    expect(module, contains('builder: (s) => const DocumentImportPremiumScreen()'));
    expect(premium, contains('DocumentImportScreen'));
  });

  test('document import is a one-step route before the native file picker', () {
    final module = _read('lib/modules/diabetes_module.dart');
    final importerIndex = module.indexOf("path: '/importer'");
    final pulperIndex = module.indexOf("path: '/pulper'");
    final importerBlock = module.substring(importerIndex, pulperIndex);

    expect(importerBlock, contains('DocumentImportPremiumScreen'));
    expect(importerBlock, isNot(contains('ImportScreen')));
  });

  test('document screen exposes the user task, not internal Pulper branding', () {
    final screen = _readDocumentImportLibrary();

    expect(screen, contains('AuditedPageCopy.of(context).documentTitle'));
    expect(screen, contains('AuditedPageCopy.of(context).documentIntro'));
    expect(screen, contains('AuditedPageCopy.of(context).chooseDocument'));
    expect(screen, contains('class _DocumentImportIcon'));
    expect(
      screen,
      contains('compactHeight = MediaQuery.sizeOf(context).height <= 600'),
    );
    expect(screen, contains('verticalPadding = compactHeight ? 12.0 : 24.0'));
    expect(screen, isNot(contains("'Pulper IAmina'")));
    expect(screen, isNot(contains('class _PulperIcon')));
  });
}
