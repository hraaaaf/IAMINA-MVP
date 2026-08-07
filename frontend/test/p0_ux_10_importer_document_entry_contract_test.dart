import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('Importer is the only primary navigation entry for acquisition', () {
    final module = _read('lib/modules/diabetes_module.dart');
    final navBlock = module.split('shellRoutes:').first;

    expect(navBlock, contains("route: '/importer'"));
    expect(navBlock, isNot(contains("route: '/pulper'")));
    expect(module, contains("ModuleFullScreenRoute(path: '/pulper'"));
  });

  test('document import is entered from Importer with task-first wording', () {
    final importer = _read('lib/features/import/import_screen.dart');

    expect(importer, contains("onTap: () => context.push('/pulper')"));
    expect(importer, contains('AuditedPageCopy.of(context).documentTitle'));
    expect(importer, contains('AuditedPageCopy.of(context).openDocumentImport'));
    expect(importer, contains('class _DocumentImportCard'));
    expect(importer, isNot(contains("'Pulper IAmina'")));
    expect(importer, isNot(contains('class _PulperCard')));
  });

  test('document screen exposes the user task, not internal Pulper branding', () {
    final screen = _read('lib/features/documents/document_import_screen.dart');

    expect(screen, contains('AuditedPageCopy.of(context).documentTitle'));
    expect(screen, contains('AuditedPageCopy.of(context).documentIntro'));
    expect(screen, contains('AuditedPageCopy.of(context).chooseDocument'));
    expect(screen, contains('class _DocumentImportIcon'));
    expect(screen, isNot(contains("'Pulper IAmina'")));
    expect(screen, isNot(contains('class _PulperIcon')));
  });
}
