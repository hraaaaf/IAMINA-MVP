"""
DomainContext — chassis-level clinical output struct.

This is the structured data a module returns to the chassis after running
its analyze() method. The chassis uses this to drive the LLM narrative
engine (core/llm_gateway.narrate()).

NOT to be confused with CompanionIdentity (core/contracts/companion_identity.py),
which carries companion persona (name, description, unit). See ADR-0008.

Data flow: module.analyze(patient_id, language) -> DomainContext -> narrate()
"""
from dataclasses import dataclass, field
from typing import Literal

AnalysisStatus = Literal["complete", "partial", "unavailable", "insufficient_data"]


@dataclass
class DomainContext:
    kpi_summary: dict
    # Module-computed KPIs as a plain dict. Values must be JSON-serializable.

    detected_patterns: list[str]
    insights: list[str]
    pivot_text: str
    language: str

    # Companion-facing fields.
    has_sufficient_data: bool = False
    tone_signals: dict = field(default_factory=dict)
    trend: dict = field(default_factory=dict)
    primary_label: str = "score"
    patterns_detail: list = field(default_factory=list)

    # ANALYSIS-0 integrity/observability contract.
    # This status describes execution integrity, never clinical severity.
    analysis_status: AnalysisStatus = "complete"
    analysis_degradations: list[str] = field(default_factory=list)
    # Degradation codes must be technical, stable and PHI-free. They exist so a
    # failed detector/query cannot silently masquerade as "no clinical finding".

    def __post_init__(self) -> None:
        if self.analysis_status == "complete" and self.analysis_degradations:
            raise ValueError("complete analysis cannot contain degradation codes")
        if self.analysis_status == "insufficient_data" and self.has_sufficient_data:
            raise ValueError("insufficient_data cannot declare sufficient data")

    @property
    def is_degraded(self) -> bool:
        return self.analysis_status in {"partial", "unavailable"}

    @classmethod
    def empty(cls, language: str = "fr") -> "DomainContext":
        """Neutral context for a valid analysis with insufficient clinical data."""
        return cls(
            kpi_summary={},
            detected_patterns=[],
            insights=[],
            pivot_text="",
            language=language,
            has_sufficient_data=False,
            analysis_status="insufficient_data",
        )

    @classmethod
    def unavailable(
        cls,
        *,
        language: str = "fr",
        degradation_codes: list[str] | None = None,
    ) -> "DomainContext":
        """Fail closed when analysis execution itself is unavailable."""
        return cls(
            kpi_summary={},
            detected_patterns=[],
            insights=[],
            pivot_text="",
            language=language,
            has_sufficient_data=False,
            analysis_status="unavailable",
            analysis_degradations=list(degradation_codes or ["analysis_unavailable"]),
        )
