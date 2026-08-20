import ast
from pathlib import Path
from unittest import TestCase


class DocumentLayerBoundaryTest(TestCase):
    def test_media_documents_never_imports_diabetes_capsule(self):
        documents_dir = Path(__file__).resolve().parents[1] / "documents"
        violations: list[str] = []

        for path in sorted(documents_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                else:
                    continue

                for module in modules:
                    if module == "diabetes" or module.startswith("diabetes."):
                        violations.append(f"{path.name}: {module}")

        self.assertEqual(violations, [])
