"""
IAmina Alert State Machine
===========================
Offline, < 50ms, zero LLM dependency.

Handles critical glycemic events:
  - Level 2 Hypoglycemia (< 54 mg/dL)
  - Severe Hyperglycemia (> 300 mg/dL)
  - Sustained hyperglycemia (> 250 for 2+ consecutive readings)

Design: Pure Python state machine. Never calls the LLM.
Responses are pre-written templates in FR and Darija.
"""

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


# ── Thresholds (mg/dL) ──
HYPO_LEVEL2 = 54
HYPO_LEVEL1 = 70
HYPER_SEVERE = 300
HYPER_SUSTAINED = 250


# ── Pre-written templates (no LLM) ──
_TEMPLATES = {
    AlertType.HYPO_SEVERE: AlertResponse(
        level=AlertLevel.EMERGENCY,
        alert_type=AlertType.HYPO_SEVERE,
        message_fr=(
            "⚠️ ALERTE URGENTE — Hypoglycémie sévère détectée.\n\n"
            "Ta glycémie est dangereusement basse (< 54 mg/dL).\n"
            "1. Prends immédiatement 15-20g de sucre rapide (jus de fruit pur, sucre, gel de glucose)\n"
            "2. Attends 15 minutes et recon​trôle\n"
            "3. Si tu ne te sens pas mieux, appelle le 15 (SAMU)\n\n"
            "Ne reste pas seul(e). Préviens un proche maintenant."
        ),
        message_darija=(
            "⚠️ تنبيه عاجل — نقص حاد فالسكر.\n\n"
            "السكر ديالك نازل بزاف (< 54 mg/dL).\n"
            "1. خود دابا 15-20g ديال السكر السريع (عصير، سكر، جيل)\n"
            "2. تسنا 15 دقيقة وعاود قيس\n"
            "3. إلا ما حسيتيش بتحسن، عيط للإسعاف\n\n"
            "ما تبقاش بوحدك. عيط لشي واحد قريب منك."
        ),
        action_required=True,
        call_emergency=True,
    ),
    AlertType.HYPO_MODERATE: AlertResponse(
        level=AlertLevel.WARNING,
        alert_type=AlertType.HYPO_MODERATE,
        message_fr=(
            "⚡ Attention — Glycémie basse détectée.\n\n"
            "Ta glycémie est en dessous de 70 mg/dL.\n"
            "Prends 15 g de glucides RAPIDES maintenant (ex : 3 morceaux de sucre, "
            "150 mL de jus de fruit pur, 1 sachet de gel de glucose), "
            "puis recon​trôle dans 15 minutes."
        ),
        message_darija=(
            "⚡ انتباه — السكر ناقص شوية.\n\n"
            "السكر ديالك تحت 70 mg/dL.\n"
            "خود دابا 15g ديال سكر سريع (3 قطع سكر، 150mL عصير فواكه، جيل جلوكوز) "
            "وعاود قيس بعد 15 دقيقة."
        ),
        action_required=True,
    ),
    AlertType.HYPER_SEVERE: AlertResponse(
        level=AlertLevel.CRITICAL,
        alert_type=AlertType.HYPER_SEVERE,
        message_fr=(
            "🔴 ALERTE — Hyperglycémie sévère détectée.\n\n"
            "Ta glycémie dépasse 300 mg/dL.\n"
            "1. Bois de l'eau régulièrement (réhydratation importante)\n"
            "2. Contacte ton médecin ou ton équipe soignante dès que possible\n"
            "3. ⚠️ Si tu ressens nausées, vomissements ou douleur abdominale → appelle le 15 (SAMU)\n\n"
            "Ne modifie pas ton traitement sans avis médical."
        ),
        message_darija=(
            "🔴 تنبيه — السكر طالع بزاف.\n\n"
            "السكر ديالك فوق 300 mg/dL.\n"
            "1. شرب الما بزاف (مهم للترطيب)\n"
            "2. تواصل مع الطبيب ديالك دابا\n"
            "3. ⚠️ إلا كان عندك غثيان ولا وجع فالكرش → عيط للإسعاف (15)\n\n"
            "ما تبدلش الدوا بلا ما تتكلم مع الطبيب."
        ),
        action_required=True,
    ),
    AlertType.HYPER_SUSTAINED: AlertResponse(
        level=AlertLevel.WARNING,
        alert_type=AlertType.HYPER_SUSTAINED,
        message_fr=(
            "📈 Attention — Hyperglycémie prolongée.\n\n"
            "Ta glycémie reste élevée (> 250 mg/dL) sur plusieurs mesures consécutives.\n"
            "Pense à revoir ton alimentation récente et hydrate-toi bien.\n"
            "Si ça persiste, contacte ton médecin ou ton équipe soignante."
        ),
        message_darija=(
            "📈 انتباه — السكر طالع من مدة.\n\n"
            "السكر ديالك باقي فوق 250 mg/dL على عدة قياسات.\n"
            "شوف الماكلة ديالك والدوا.\n"
            "إلا بقا هكاك، تواصل مع الطبيب ديالك."
        ),
        action_required=True,
    ),
}

# ── Sentinel: no alert ──
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
    """
    Evaluate a glucose reading against the alert state machine.
    Pure Python, < 50ms, zero external dependencies.
    """
    # Emergency: Level 2 hypoglycemia
    if glucose_value < HYPO_LEVEL2:
        logger.warning("ALERT: Hypo severe — %s mg/dL", glucose_value)
        return _TEMPLATES[AlertType.HYPO_SEVERE]

    # Warning: Level 1 hypoglycemia
    if glucose_value < HYPO_LEVEL1:
        return _TEMPLATES[AlertType.HYPO_MODERATE]

    # Critical: Severe hyperglycemia
    if glucose_value > HYPER_SEVERE:
        logger.warning("ALERT: Hyper severe — %s mg/dL", glucose_value)
        return _TEMPLATES[AlertType.HYPER_SEVERE]

    # Warning: Sustained hyperglycemia (2+ consecutive readings > 250)
    if recent_readings and len(recent_readings) >= 2:
        last_two = recent_readings[-2:]
        if all(r > HYPER_SUSTAINED for r in last_two) and glucose_value > HYPER_SUSTAINED:
            return _TEMPLATES[AlertType.HYPER_SUSTAINED]

    return _NO_ALERT
