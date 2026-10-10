"""CAL-07: prevent accidental activation of permissive legacy unit conversion.

This is a static production-import guard, not a claim that dynamic imports or
all runtime code paths have been exhaustively certified.
"""
from __future__ import annotations

import ast
from pathlib import Path

LEGACY_MODULE = "diabetes.services.clinical.unit_guard"


def test_no_backend_production_directly_imports_legacy_unit_guard() -> None:
    """All user-facing input conversion must use the strict contracts instead."""
    backend = Path(__file__).resolve().parents[2]
    old_module = backend / "diabetes/services/clinical/unit_guard.py"
    found: list[str] = []
    examined = 0
    for path in backend.rglob("*.py"):
        if (
            path == old_module
            or "tests" in path.relative_to(backend).parts
            or "test" in path.relative_to(backend).parts
            or "__pycache__" in path.parts
        ):
            continue
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
        examined += 1
        relative_path = path.relative_to(backend)
        inside_clinical = (
            relative_path.parent.as_posix()
            == "diabetes/services/clinical"
        )
        for node in ast.walk(tree):
            direct = False
            if isinstance(node, ast.Import):
                direct = any(
                    a.name == LEGACY_MODULE
                    or a.name.startswith(LEGACY_MODULE + ".")
                    for a in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                direct = (
                    node.level == 0 and node.module == LEGACY_MODULE
                ) or (
                    node.level == 1
                    and node.module == "unit_guard"
                    and inside_clinical
                )
            elif isinstance(node, ast.Call):
                fn = node.func
                is_import = (
                    isinstance(fn, ast.Name) and fn.id == "__import__"
                ) or (
                    isinstance(fn, ast.Attribute)
                    and fn.attr == "import_module"
                )
                direct = (
                    is_import
                    and bool(node.args)
                    and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == LEGACY_MODULE
                )
            if direct:
                found.append(f"{relative_path}:{node.lineno}")

    assert examined >= 50, (
        "Source scan did not cover expected production Python files"
    )
    assert not found, (
        "Permissive legacy glucose UnitGuard imported in production; "
        "use diabetes.contracts.log_entry / active strict middleware "
        f"instead: {found}"
    )
