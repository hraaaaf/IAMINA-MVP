#!/usr/bin/env python3
"""Apply scoped mobile-import accessibility fixes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "frontend/lib/features/navigation/main_shell.dart"
IMPORT_SCREEN = ROOT / "frontend/lib/features/import/import_screen.dart"
DOCUMENT = ROOT / "frontend/lib/features/documents/document_import_screen.dart"


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_once(
        SHELL,
        """      child: NavigationBar(\n        selectedIndex: selectedIndex.clamp(0, entries.length - 1),\n        onDestinationSelected: (i) => GoRouter.of(context).go(entries[i].route),\n        destinations: [\n          for (final e in entries)\n            NavigationDestination(\n              icon: Icon(e.icon),\n              selectedIcon: Icon(e.selectedIcon),\n              label: e.label(AppLocalizations.of(context)!),\n            ),\n        ],\n      ),""",
        """      child: NavigationBar(\n        selectedIndex: selectedIndex.clamp(0, entries.length - 1),\n        onDestinationSelected: (i) => GoRouter.of(context).go(entries[i].route),\n        labelBehavior: MediaQuery.sizeOf(context).width < 430\n            ? NavigationDestinationLabelBehavior.onlyShowSelected\n            : NavigationDestinationLabelBehavior.alwaysShow,\n        destinations: [\n          for (final e in entries)\n            NavigationDestination(\n              key: ValueKey('mobile-nav-${e.route}'),\n              icon: Icon(e.icon),\n              selectedIcon: Icon(e.selectedIcon),\n              label: e.label(AppLocalizations.of(context)!),\n            ),\n        ],\n      ),""",
    )

    replace_once(
        IMPORT_SCREEN,
        """                  _PulperCard(onTap: () => context.push('/pulper')),""",
        """                  _PulperCard(\n                    key: const ValueKey('import-document-cta'),\n                    onTap: () => context.push('/pulper'),\n                  ),""",
    )
    replace_once(
        IMPORT_SCREEN,
        """class _PulperCard extends StatelessWidget {\n  final VoidCallback onTap;\n  const _PulperCard({required this.onTap});""",
        """class _PulperCard extends StatelessWidget {\n  final VoidCallback onTap;\n  const _PulperCard({super.key, required this.onTap});""",
    )
    replace_once(
        IMPORT_SCREEN,
        """    return GestureDetector(\n      onTap: onTap,\n      child: Container(""",
        """    return Semantics(\n      button: true,\n      label: 'Ouvrir l’import de document',\n      child: InkWell(\n        onTap: onTap,\n        borderRadius: BorderRadius.circular(20),\n        child: Container(""",
    )
    replace_once(
        IMPORT_SCREEN,
        """        ),\n      ),\n    );\n  }\n}\n\nclass _PulperChip""",
        """        ),\n      ),\n      ),\n    );\n  }\n}\n\nclass _PulperChip""",
    )

    old_pick_start = """  Widget _buildPick() {\n    return Padding(\n      padding: const EdgeInsets.all(24),\n      child: Column(\n        mainAxisAlignment: MainAxisAlignment.center,\n        children: ["""
    new_pick_start = """  Widget _buildPick() {\n    return LayoutBuilder(\n      builder: (context, constraints) => SingleChildScrollView(\n        key: const ValueKey('document-import-pick-scroll'),\n        padding: const EdgeInsets.all(24),\n        child: ConstrainedBox(\n          constraints: BoxConstraints(\n            minHeight: constraints.maxHeight > 48\n                ? constraints.maxHeight - 48\n                : 0,\n          ),\n          child: Column(\n            mainAxisAlignment: MainAxisAlignment.center,\n            children: ["""
    replace_once(DOCUMENT, old_pick_start, new_pick_start)
    replace_once(
        DOCUMENT,
        """          if (_error != null) ...[\n            const SizedBox(height: 16),\n            _ErrorCard(message: _error!),\n          ],\n        ],\n      ),\n    );\n  }""",
        """              if (_error != null) ...[\n                const SizedBox(height: 16),\n                _ErrorCard(message: _error!),\n              ],\n            ],\n          ),\n        ),\n      ),\n    );\n  }""",
    )
    replace_once(
        DOCUMENT,
        """            child: ElevatedButton.icon(\n              onPressed: _pickFile,""",
        """            child: ElevatedButton.icon(\n              key: const ValueKey('choose-document-button'),\n              onPressed: _pickFile,""",
    )

    print("P0 mobile import patch applied.")


if __name__ == "__main__":
    main()
