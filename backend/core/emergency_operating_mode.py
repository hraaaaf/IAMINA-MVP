"""Explicit emergency operating mode for the pilot.

IAmina has no monitored human response team by default. Emergency responses must
state that fact and direct the user to local emergency services or a trusted
person. A monitored mode cannot be enabled without complete operational evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SELF_CARE_ONLY = "SELF_CARE_ONLY"
MONITORED_HUMAN = "MONITORED_HUMAN"


@dataclass(frozen=True, slots=True)
class EmergencyOperatingPolicy:
    mode: str
    policy_owner: str
    effective_on: date
    review_due_on: date
    human_monitoring: bool
    monitored_channel: str | None = None
    escalation_owner: str | None = None
    staffed_hours: str | None = None
    last_drill_on: date | None = None

    def validate(self, *, today: date | None = None) -> None:
        current = today or date.today()
        if self.mode not in {SELF_CARE_ONLY, MONITORED_HUMAN}:
            raise ValueError("unknown emergency operating mode")
        if not self.policy_owner.strip():
            raise ValueError("emergency policy owner is required")
        if self.effective_on > current:
            raise ValueError("emergency policy is not effective yet")
        if self.review_due_on < current:
            raise ValueError("emergency policy is stale")

        if self.mode == SELF_CARE_ONLY:
            if self.human_monitoring:
                raise ValueError("self-care-only mode cannot claim human monitoring")
            if any(
                value
                for value in (
                    self.monitored_channel,
                    self.escalation_owner,
                    self.staffed_hours,
                    self.last_drill_on,
                )
            ):
                raise ValueError("self-care-only mode cannot carry monitored-channel evidence")
            return

        required = {
            "monitored_channel": self.monitored_channel,
            "escalation_owner": self.escalation_owner,
            "staffed_hours": self.staffed_hours,
            "last_drill_on": self.last_drill_on,
        }
        missing = [name for name, value in required.items() if not value]
        if not self.human_monitoring or missing:
            raise ValueError(
                "monitored emergency mode lacks operational evidence: "
                + ", ".join(missing or ["human_monitoring"])
            )


PILOT_EMERGENCY_POLICY = EmergencyOperatingPolicy(
    mode=SELF_CARE_ONLY,
    policy_owner="IAmina Safety & Compliance",
    effective_on=date(2026, 8, 2),
    review_due_on=date(2026, 11, 2),
    human_monitoring=False,
)

_DISCLOSURES = {
    "fr": (
        "IAmina ne surveille pas cette alerte en temps réel et aucun professionnel "
        "n'a été automatiquement prévenu. Contactez immédiatement les services "
        "d'urgence ou une personne de confiance."
    ),
    "en": (
        "IAmina does not monitor this alert in real time and no professional has "
        "been notified automatically. Contact emergency services or a trusted "
        "person immediately."
    ),
    "ar": (
        "لا تتم مراقبة هذا التنبيه بشكل مباشر ولم يتم إبلاغ أي مهني تلقائيا. "
        "اتصل فورا بخدمات الطوارئ أو بشخص تثق به."
    ),
    "ar-MA": (
        "IAmina ma katra9ebch had l-alert f lwa9t l7a9i9i, w ma t3ayet l ta wa7ed "
        "mn l-mihaniyin automatiquement. 3ayet daba l-tawari2 wla chi wa7ed kat9 fih."
    ),
}


def emergency_disclosure(language: str = "fr") -> str:
    """Return the mandatory disclosure for the active operating mode."""
    PILOT_EMERGENCY_POLICY.validate()
    return _DISCLOSURES.get(language, _DISCLOSURES["fr"])


def append_emergency_disclosure(message: str, language: str = "fr") -> str:
    disclosure = emergency_disclosure(language)
    if disclosure in message:
        return message
    return f"{message.rstrip()}\n\n{disclosure}"


def decorate_emergency_payload(
    payload: dict[str, object],
    *,
    language: str = "fr",
) -> dict[str, object]:
    """Return an emergency payload with truthful operating-mode metadata."""
    PILOT_EMERGENCY_POLICY.validate()
    result = dict(payload)
    reply = str(result.get("reply", ""))
    result["reply"] = append_emergency_disclosure(reply, language)
    result["emergency_operating_mode"] = PILOT_EMERGENCY_POLICY.mode
    result["human_monitoring"] = PILOT_EMERGENCY_POLICY.human_monitoring
    return result
