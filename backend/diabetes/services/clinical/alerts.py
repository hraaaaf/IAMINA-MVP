"""
IAmina diabetes glucose alert state machine.

Classification is deterministic and independent of generative AI. This diabetes
layer deliberately contains no country-specific emergency number: jurisdiction
resources are owned by ``core.emergency_resources`` and may be selected only from
an explicitly confirmed, current locale policy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    HYPO_SEVERE = "hypo_severe"
    HYPO_MODERATE = "hypo_moderate"
    HYPER_SEVERE = "hyper_severe"
    HYPER_SUSTAINED = "hyper_sustained"


@dataclass
class AlertResponse:
    level: AlertLevel
    alert_type: Optional[AlertType]
    message_fr: str
    message_darija: str
    action_required: bool
    call_emergency: bool = False


HYPO_LEVEL2 = 54
HYPO_LEVEL1 = 70
HYPER_SEVERE = 300
HYPER_SUSTAINED = 250

_TEMPLATES = {
    AlertType.HYPO_SEVERE: AlertResponse(
        level=AlertLevel.EMERGENCY,
        alert_type=AlertType.HYPO_SEVERE,
        message_fr=(
            "⚠️ ALERTE URGENTE — Glycémie très basse détectée.\n\n"
            "La mesure est <54 mg/dL. Utilise immédiatement le plan de prise en charge "
            "de l'hypoglycémie qui t'a été expliqué par ton équipe soignante et demande "
            "l'aide d'une personne de confiance.\n\n"
            "Si tu ne peux pas te prendre en charge normalement, si ton état s'aggrave "
            "ou si tu perds connaissance, les services d'urgence locaux doivent être contactés. "
            "IAmina ne choisit aucun numéro ici sans juridiction confirmée."
        ),
        message_darija=(
            "⚠️ تنبيه عاجل — قياس السكر هابط بزاف (<54 mg/dL).\n\n"
            "طبق دابا الخطة ديال التعامل مع نقص السكر اللي شرحها ليك الفريق الصحي ديالك، "
            "وطلب المساعدة من شي واحد كاتيق فيه.\n\n"
            "إلا ما قدرتيش تتصرف بشكل عادي، ولا الحالة تزادت، ولا فقدتي الوعي، "
            "خاص يتصلو بخدمات الطوارئ المحلية. IAmina ما كتختارش رقم بلا بلد مؤكد."
        ),
        action_required=True,
        call_emergency=True,
    ),
    AlertType.HYPO_MODERATE: AlertResponse(
        level=AlertLevel.WARNING,
        alert_type=AlertType.HYPO_MODERATE,
        message_fr=(
            "⚡ Attention — Glycémie basse détectée (<70 mg/dL).\n\n"
            "Utilise le plan de prise en charge de l'hypoglycémie déjà validé avec ton équipe "
            "soignante et recontrôle selon ce plan. Si tu te sens mal ou si la situation "
            "s'aggrave, demande de l'aide."
        ),
        message_darija=(
            "⚡ انتباه — قياس السكر تحت 70 mg/dL.\n\n"
            "طبق الخطة ديال نقص السكر اللي متافق عليها مع الفريق الصحي ديالك، "
            "وعاود القياس كيف ما مكتوب فيها. إلا حسّيتي براسك ماشي مزيان ولا الحالة تزادت، طلب المساعدة."
        ),
        action_required=True,
    ),
    AlertType.HYPER_SEVERE: AlertResponse(
        level=AlertLevel.CRITICAL,
        alert_type=AlertType.HYPER_SEVERE,
        message_fr=(
            "🔴 ALERTE — Glycémie très élevée détectée (>300 mg/dL).\n\n"
            "Contacte ton équipe soignante selon ton plan habituel. Si tu présentes des "
            "symptômes inquiétants ou si ton état s'aggrave, contacte les services d'urgence "
            "locaux. Ne modifie pas ton traitement sur la seule base de cette alerte."
        ),
        message_darija=(
            "🔴 تنبيه — قياس السكر فوق 300 mg/dL.\n\n"
            "تواصل مع الفريق الصحي ديالك حسب الخطة ديالك. إلا كانت أعراض مقلقة ولا الحالة تزادت، "
            "تواصل مع خدمات الطوارئ المحلية. ما تبدلش العلاج غير بهاد التنبيه."
        ),
        action_required=True,
    ),
    AlertType.HYPER_SUSTAINED: AlertResponse(
        level=AlertLevel.WARNING,
        alert_type=AlertType.HYPER_SUSTAINED,
        message_fr=(
            "📈 Attention — Plusieurs mesures élevées ont été détectées (>250 mg/dL).\n\n"
            "Cette séquence mérite d'être notée et discutée avec ton équipe soignante si elle "
            "persiste. Ne modifie pas ton traitement sur la seule base de cette alerte."
        ),
        message_darija=(
            "📈 انتباه — تسجلو كثر من قياس فوق 250 mg/dL.\n\n"
            "دوّن هاد السلسلة، وإلا بقات تواصل مع الفريق الصحي ديالك. "
            "ما تبدلش العلاج غير بهاد التنبيه."
        ),
        action_required=True,
    ),
}

_NO_ALERT = AlertResponse(
    level=AlertLevel.NONE,
    alert_type=None,
    message_fr="",
    message_darija="",
    action_required=False,
)


def evaluate(
    glucose_value: float,
    recent_readings: Optional[List[float]] = None,
) -> AlertResponse:
    """Evaluate one normalized mg/dL reading against deterministic thresholds."""
    if glucose_value < HYPO_LEVEL2:
        logger.warning("ALERT: level-2 hypoglycemia — %s mg/dL", glucose_value)
        return _TEMPLATES[AlertType.HYPO_SEVERE]

    if glucose_value < HYPO_LEVEL1:
        return _TEMPLATES[AlertType.HYPO_MODERATE]

    if glucose_value > HYPER_SEVERE:
        logger.warning("ALERT: severe hyperglycemia — %s mg/dL", glucose_value)
        return _TEMPLATES[AlertType.HYPER_SEVERE]

    if recent_readings and len(recent_readings) >= 2:
        last_two = recent_readings[-2:]
        if all(reading > HYPER_SUSTAINED for reading in last_two) and glucose_value > HYPER_SUSTAINED:
            return _TEMPLATES[AlertType.HYPER_SUSTAINED]

    return _NO_ALERT
