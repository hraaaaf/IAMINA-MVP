"""
IAmina — Triage Path Registry
==============================
Append-only registry of paths and keyword sets where the TriageVitalMiddleware
is active. Modules register their paths during AppConfig.ready() — no hardcoded
tuples in the middleware itself.

Design constraints:
  - Append-only: no clear(), no __setitem__, no __delitem__.
  - Singleton: TRIAGE_REGISTRY is the single authoritative instance.
  - Import-safe: no Django model/ORM imports at module level.
"""
from __future__ import annotations


class AppendOnlyTriageRegistry:
    """Registry of triage-eligible paths and keyword sets.

    Only append operations are permitted — removal is intentionally impossible.
    This prevents accidental de-registration of the medical emergency gate.
    """

    def __init__(self) -> None:
        self._paths: list[str] = []
        self._keyword_sets: list[frozenset[str]] = []

    def register_path(self, path: str) -> None:
        """Register a URL path prefix where triage applies."""
        self._paths.append(path)

    def register_keywords(self, kws: frozenset[str]) -> None:
        """Register an additional set of emergency keywords."""
        self._keyword_sets.append(kws)

    # Explicitly no clear(), __setitem__, or __delitem__ — append-only by design.


TRIAGE_REGISTRY = AppendOnlyTriageRegistry()
