from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


# Import hub: one explicit document-import action, no Pulper product terminology.
p = Path('frontend/lib/features/import/import_screen.dart')
s = p.read_text()
s = replace_once(s, "                  // ── Pulper IAmina ──────────────────────────────────────────\n                  _PulperCard(", "                  // ── Document import ─────────────────────────────────────────\n                  _DocumentImportCard(", 'import hub card call')
s = replace_once(s, "// ── Pulper IAmina card ────────────────────────────────────────────────────────\n\nclass _PulperCard extends StatelessWidget {", "// ── Document import card ───────────────────────────────────────────────────────\n\nclass _DocumentImportCard extends StatelessWidget {", 'import hub class')
s = replace_once(s, "  const _PulperCard({super.key, required this.onTap});", "  const _DocumentImportCard({super.key, required this.onTap});", 'import hub constructor')
s = replace_once(
    s,
    "                    const Text(\n                      'Pulper IAmina',\n                      style: TextStyle(",
    "                    Text(\n                      AuditedPageCopy.of(context).documentTitle,\n                      style: const TextStyle(",
    'import hub visible title',
)
s = s.replace('_PulperChip(', '_DocumentFormatChip(')
s = s.replace('class _PulperChip extends StatelessWidget {', 'class _DocumentFormatChip extends StatelessWidget {')
s = s.replace('const _PulperChip({required this.label});', 'const _DocumentFormatChip({required this.label});')
p.write_text(s)


# Document flow: app bar names the task; hero avoids repeating the same title.
p = Path('frontend/lib/features/documents/document_import_screen.dart')
s = p.read_text()
s = replace_once(s, "              const _PulperIcon(),", "              const _DocumentImportIcon(),", 'document icon call')
s = replace_once(
    s,
    "              const SizedBox(height: 28),\n              Text(\n                'Pulper IAmina',\n                style: TextStyle(\n                  fontSize: 26,\n                  fontWeight: FontWeight.w800,\n                  color: AminaTheme.textPrimary(context),\n                  letterSpacing: -0.5,\n                ),\n              ),\n              const SizedBox(height: 10),",
    "              const SizedBox(height: 20),",
    'document duplicate hero title',
)
s = s.replace('class _PulperIcon extends StatelessWidget {', 'class _DocumentImportIcon extends StatelessWidget {')
s = s.replace('const _PulperIcon();', 'const _DocumentImportIcon();')
p.write_text(s)


# Permanent contract: Importer is the only primary nav entry; document processing is subordinate.
p = Path('frontend/test/p0_ux_10_importer_document_entry_contract_test.dart')
p.write_text(r'''import 'dart:io';

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
''')
