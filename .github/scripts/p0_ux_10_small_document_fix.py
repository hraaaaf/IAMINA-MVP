from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)

p = Path('frontend/lib/features/documents/document_import_screen.dart')
s = p.read_text()
s = replace_once(
    s,
    "  Widget _buildPick() {\n    return LayoutBuilder(\n      builder: (context, constraints) => SingleChildScrollView(\n        key: const ValueKey('document-import-pick-scroll'),\n        padding: const EdgeInsets.all(24),",
    "  Widget _buildPick() {\n    final compactHeight = MediaQuery.sizeOf(context).height <= 600;\n    final verticalPadding = compactHeight ? 12.0 : 24.0;\n    return LayoutBuilder(\n      builder: (context, constraints) => SingleChildScrollView(\n        key: const ValueKey('document-import-pick-scroll'),\n        padding: EdgeInsets.symmetric(horizontal: compactHeight ? 20 : 24, vertical: verticalPadding),",
    'compact pick shell',
)
s = replace_once(
    s,
    "            minHeight: constraints.maxHeight > 48\n                ? constraints.maxHeight - 48\n                : 0,",
    "            minHeight: constraints.maxHeight > verticalPadding * 2\n                ? constraints.maxHeight - verticalPadding * 2\n                : 0,",
    'compact min height',
)
s = replace_once(s, "              const _DocumentImportIcon(),\n              const SizedBox(height: 20),", "              const _DocumentImportIcon(),\n              SizedBox(height: compactHeight ? 14 : 20),", 'compact icon gap')
s = replace_once(
    s,
    "                style: TextStyle(\n                  fontSize: 14,\n                  color: AminaTheme.textSecondary(context),\n                  height: 1.5,",
    "                style: TextStyle(\n                  fontSize: compactHeight ? 13 : 14,\n                  color: AminaTheme.textSecondary(context),\n                  height: compactHeight ? 1.4 : 1.5,",
    'compact intro',
)
s = replace_once(s, "              const SizedBox(height: 32),\n              // Format chips", "              SizedBox(height: compactHeight ? 20 : 32),\n              // Format chips", 'compact format gap')
s = replace_once(s, "              const SizedBox(height: 20),\n              const _PrivacyGateNotice(),\n              const SizedBox(height: 24),", "              SizedBox(height: compactHeight ? 12 : 20),\n              const _PrivacyGateNotice(),\n              SizedBox(height: compactHeight ? 14 : 24),", 'compact privacy gaps')
s = replace_once(s, "                    padding: const EdgeInsets.symmetric(vertical: 16),", "                    padding: EdgeInsets.symmetric(vertical: compactHeight ? 13 : 16),", 'compact CTA')
s = replace_once(
    s,
    "  Widget build(BuildContext context) {\n    return Container(\n      width: 100,\n      height: 100,",
    "  Widget build(BuildContext context) {\n    final compactHeight = MediaQuery.sizeOf(context).height <= 600;\n    return Container(\n      width: compactHeight ? 84 : 100,\n      height: compactHeight ? 84 : 100,",
    'compact icon size',
)
s = replace_once(s, "      child: const Icon(Icons.upload_file, color: Colors.white, size: 48),", "      child: Icon(Icons.upload_file, color: Colors.white, size: compactHeight ? 40 : 48),", 'compact icon glyph')
p.write_text(s)

p = Path('frontend/test/p0_ux_10_importer_document_entry_contract_test.dart')
s = p.read_text()
s = replace_once(
    s,
    "    expect(screen, contains('class _DocumentImportIcon'));\n",
    "    expect(screen, contains('class _DocumentImportIcon'));\n    expect(screen, contains('compactHeight = MediaQuery.sizeOf(context).height <= 600'));\n    expect(screen, contains('verticalPadding = compactHeight ? 12.0 : 24.0'));\n",
    'compact contract',
)
p.write_text(s)
