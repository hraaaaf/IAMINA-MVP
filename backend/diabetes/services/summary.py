"""Retired legacy diabetes summary entry points.

ANALYSIS-3 removes the former parallel clinical-summary authority. Public
analysis must flow through the registered evidence-gated diabetes engine and
its governed projections. These compatibility symbols intentionally fail
closed so an undiscovered legacy caller cannot emit fabricated clinical claims
or treatment advice.
"""


class LegacyClinicalSummaryDisabled(RuntimeError):
    """Raised when retired clinical-summary code is called directly."""


def _disabled(name: str) -> None:
    raise LegacyClinicalSummaryDisabled(
        f"{name} is retired; use the registered evidence-gated diabetes engine."
    )


def prepare_clinical_metrics(logs, target_low, target_high):
    """Retired parallel Python KPI calculator; retained only as a fail-closed symbol."""
    _ = (logs, target_low, target_high)
    _disabled("prepare_clinical_metrics")


def generate_ai_summary(user, logs):
    """Retired direct clinical LLM summary path; retained only as a fail-closed symbol."""
    _ = (user, logs)
    _disabled("generate_ai_summary")


def generate_fallback_summary(user, logs):
    """Retired fabricated fallback summary; retained only as a fail-closed symbol."""
    _ = (user, logs)
    _disabled("generate_fallback_summary")
