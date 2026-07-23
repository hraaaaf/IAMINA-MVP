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


@dataclass
class DomainContext:
    kpi_summary: dict
    # Module-computed KPIs as a plain dict. Values must be JSON-serializable
    # (no ORM objects, no numpy types).
    # Example: {"tir_pct": 68.2, "gmi": 7.1, "cv_pct": 33.4, "entries": 42}

    detected_patterns: list[str]
    # Human-readable pattern labels detected by the module's clinical engine.
    # Example: ["dawn_phenomenon", "post_exercise_hypoglycemia"]

    insights: list[str]
    # English plain-text clinical insights for the LLM prompt.
    # Must be PHI-free: no patient names, no DOB, no national IDs.
    # Example: ["Patient shows consistent dawn phenomenon over 7 days."]

    pivot_text: str
    # Compressed English pivot text for the LLM system prompt.
    # Output of SemanticCompressor. Must be PHI-free.

    language: str
    # BCP-47 target language for the narrative response.
    # Example: "ar-MA" (Darija), "fr", "en"

    # ── P4.5 companion-facing fields ──────────────────────────────────────────
    # The companion runtime (chat, tone, narration) consumes the SAME DomainContext
    # that narrate() consumes — one module→chassis clinical contract. Defaults keep
    # existing narrate() callers unaffected. All values must be JSON-serializable.

    has_sufficient_data: bool = False
    # False → companion shows a "not enough data yet" message and skips the LLM.

    tone_signals: dict = field(default_factory=dict)
    # Two normalized scores the tone/state logic reads, condition-agnostic:
    #   primary:   0–100, higher = better (diabetes: TIR%; HTN: time-in-BP-target%)
    #   stability: lower = steadier      (diabetes: CV%;  HTN: BP variability)
    # Example: {"primary": 68.2, "stability": 33.4}

    trend: dict = field(default_factory=dict)
    # Opaque module-produced trend dict read by key ("direction", etc.).

    primary_label: str = "score"
    # Vocabulary hint for IAmina's internal self-note (diabetes: "TIR").

    patterns_detail: list = field(default_factory=list)
    # Patterns with evidence for the Mode-3 summary prompt.
    # Example: [{"code": "DAWN_PHENOMENON", "priority": 2, "evidence": "…"}]

    @classmethod
    def empty(cls, language: str = "fr") -> "DomainContext":
        """Neutral context — no active engine or insufficient data."""
        return cls(
            kpi_summary={},
            detected_patterns=[],
            insights=[],
            pivot_text="",
            language=language,
            has_sufficient_data=False,
        )
