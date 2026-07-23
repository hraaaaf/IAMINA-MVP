"""
AppendOnlyTriageRegistry — unit tests
======================================
T1: registered path appears in _paths
T2: registry exposes no mutation surface (no clear / __setitem__)
T3: unregistered path does not appear in _paths
"""
from django.test import SimpleTestCase

from core.safety_registry import AppendOnlyTriageRegistry


class AppendOnlyTriageRegistryTests(SimpleTestCase):
    """Each test operates on a fresh local registry instance to avoid
    cross-test contamination with the module-level TRIAGE_REGISTRY singleton."""

    def _make_registry(self):
        return AppendOnlyTriageRegistry()

    # T1 — registered path is present
    def test_registered_path_appears_in_paths(self):
        registry = self._make_registry()
        registry.register_path("/test")
        self.assertIn("/test", registry._paths)

    # T2 — no mutation surface exposed
    def test_registry_has_no_clear_method(self):
        registry = self._make_registry()
        self.assertFalse(hasattr(registry, "clear"))

    def test_registry_has_no_setitem(self):
        registry = self._make_registry()
        self.assertFalse(hasattr(registry, "__setitem__"))

    # T3 — unregistered path is absent
    def test_unregistered_path_not_in_paths(self):
        registry = self._make_registry()
        self.assertNotIn("/api/v1/never/registered", registry._paths)
