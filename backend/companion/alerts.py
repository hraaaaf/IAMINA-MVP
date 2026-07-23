from dataclasses import dataclass
from typing import Optional


@dataclass
class Alert:
    level: str
    message_fr: str
    message_darija: str

_ALERTS = [
    Alert(
        level="critical_low",
        message_fr="⚠️ Glycémie très basse. Mange du sucre maintenant et appelle ton médecin.",
        message_darija="⚠️ Sokkar dyal ddem bayn bgha ihbt. Kul chi hlu daba u tssnt l tbib."
    ),
    Alert(
        level="critical_high",
        message_fr="⚠️ Glycémie très élevée. Contacte ton médecin ou le 15.",
        message_darija="⚠️ Sokkar dyal ddem 3ali bzaf. Tssnt l tbib wlla 15."
    ),
]

def check_alert(entry, language: str = "fr") -> Optional[str]:
    """Returns alert message or None. No LLM. No DB. Pure logic."""
    g = getattr(entry, "blood_sugar", getattr(entry, "glucose_value", None))
    if g is None:
        return None
    try:
        g_val = float(g)
    except ValueError:
        return None

    if g_val < 54:
        alert = _ALERTS[0]
    elif g_val > 300:
        alert = _ALERTS[1]
    else:
        return None
    return alert.message_darija if language == "ar-MA" else alert.message_fr
