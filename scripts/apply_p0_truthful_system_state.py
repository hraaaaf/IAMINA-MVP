#!/usr/bin/env python3
"""Apply the scoped P0 truthful-system-state copy patch."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORT = ROOT / "frontend/lib/features/import/import_screen.dart"


def replace_once(old: str, new: str) -> None:
    source = IMPORT.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"expected one import-screen match, found {count}")
    IMPORT.write_text(source.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_once(
        """                if (lastLogAt != null)\n                  Text(\n                    'Dernière mesure $label',\n                    style: const TextStyle(\n                      fontSize: 11,\n                      color: AminaTheme.teal600,\n                    ),\n                  ),\n              ],\n            ),\n          ),\n          const Icon(Icons.sync_outlined, size: 16, color: AminaTheme.teal500),""",
        """                if (lastLogAt != null)\n                  Text(\n                    'Dernière mesure $label · Stockage local',\n                    style: const TextStyle(\n                      fontSize: 11,\n                      color: AminaTheme.teal600,\n                    ),\n                  ),\n              ],\n            ),\n          ),\n          const Tooltip(\n            message: 'Données stockées sur cet appareil',\n            child: Icon(\n              Icons.storage_outlined,\n              size: 16,\n              color: AminaTheme.teal500,\n            ),\n          ),""",
    )
    print("P0 truthful-system-state copy patch applied.")


if __name__ == "__main__":
    main()
