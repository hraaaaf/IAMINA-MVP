"""
DomainAlert — chassis-level offline safety alert (P4.5).

Returned by BaseEngine.evaluate_alert() when a single log entry trips the
module's offline safety gate (e.g. severe hypoglycemia). The companion runtime
decides whether to short-circuit (blocking) and records the event — it never
sees the module's clinical thresholds.

See docs/architecture/platform-transformation-plan.md (P4.5 section).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DomainAlert:
    severity: str                   # "warning" | "critical" | "emergency"
    blocking: bool                  # True → return message immediately, skip the LLM
    message: str                    # localized message for the requested language
    event_type: str = "alert"       # for the deep-memory event log
    event_description: str = ""
    value: float | None = None      # triggering measurement, for the event log
