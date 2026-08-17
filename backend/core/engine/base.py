"""
BaseEngine ABC — the single module→chassis clinical contract (P4.5).

A module's engine owns its own data access. Given a patient_id and a window, it
returns a DomainContext (the universal clinical output struct) that drives both
the LLM gateway (narrate()) and the companion runtime (chat, tone, narration).
It may also expose a governed read-only CompanionContext for longitudinal
companion state, plus an offline per-entry safety gate via evaluate_alert().

Usage:
    from core.engine import BaseEngine

    class MyEngine(BaseEngine):
        def analyze(self, patient_id, language="fr", days=14):
            ...

History: replaces the DA-03 S1 signature analyze(entries, kpis, ...). See
docs/architecture/platform-transformation-plan.md (P4.5 section).
"""
from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.contracts.alert import DomainAlert
    from core.contracts.companion_context import CompanionContext
    from core.contracts.domain_context import DomainContext


class BaseEngine(abc.ABC):
    """
    Abstract base class for module clinical engines.

    Subclasses MUST implement :meth:`analyze`. The base class cannot be
    instantiated directly (raises ``TypeError``).
    """

    @abc.abstractmethod
    def analyze(
        self,
        patient_id: int,
        language: str = "fr",
        days: int = 14,
    ) -> "DomainContext":
        """
        Run clinical analysis for a patient and return a :class:`DomainContext`.

        The engine fetches its own data (entries, KPIs) given ``patient_id`` —
        callers never pass ORM objects. Returns ``DomainContext.empty()`` when
        the patient has insufficient data.

        Args:
            patient_id: Django ``User.id`` of the patient.
            language:   Patient preferred_language code ('fr', 'ar-MA', 'ar').
            days:       Trailing window in days to analyze.

        Returns:
            A populated (or empty) :class:`DomainContext`.
        """

    def companion_context(
        self,
        patient_id: int,
        language: str = "fr",
    ) -> "CompanionContext":
        """Return governed longitudinal state without consuming delivery budget.

        Modules with certified longitudinal companion projections override this
        method. The default is a neutral empty context, preserving compatibility
        for modules that only implement the instant ``DomainContext`` contract.
        """
        from core.contracts.companion_context import CompanionContext

        return CompanionContext.empty(language=language)

    def evaluate_alert(
        self,
        entry,
        language: str = "fr",
    ) -> "DomainAlert | None":
        """
        Offline per-entry safety gate (the hard medical gate).

        Evaluates a single just-logged entry against the module's clinical
        thresholds and returns a localized :class:`DomainAlert`, or ``None`` if
        no alert fires. Default implementation raises no alert; modules with a
        safety gate override this. Must be offline and fast (<50ms, no LLM).
        """
        return None
