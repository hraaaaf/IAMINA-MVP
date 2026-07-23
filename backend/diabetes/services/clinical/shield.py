import logging
import re

from diabetes.domain_config import DIABETES_CONFIG

logger = logging.getLogger(__name__)

# 1. EMERGENCY_PATTERNS: Red flags requiring immediate medical attention.
EMERGENCY_PATTERNS = [
    r"(?i)coma",
    r"(?i)évanouissement",
    r"(?i)perte de connaissance",
    r"(?i)convulsion",
    r"(?i)acidocétose",
    r"(?i)douleur à la poitrine",
    r"(?i)chest pain",
    r"(?i)difficulté à respirer",
    r"(?i)breathless",
]

# 2. SYMPTOMATIC_EMERGENCY: Signs of Diabetic Ketoacidosis (DKA) or extreme distress.
SYMPTOMATIC_EMERGENCY = [
    r"(?i)(nausé|envie de vomir).*(hyper|sucre|élevé|300|400)",
    r"(?i)(vomir|vomissement).*(hyper|sucre|élevé|300|400)",
    r"(?i)souffle.*fruité",
    r"(?i)haleine.*pomme",
    r"(?i)soif.*intense",
    r"(?i)vision.*trouble",
    r"(?i)confus",
]

# 3. FORBIDDEN_SCOPE: Non-medical or dangerous topics IAmina must refuse.
#
# Word-boundary notes:
#   \bmort\b  — blocks "mort" (death) but NOT "mortalité", "immortel", "remords"
#               (all legitimate medical/everyday words — documented false-positive fixed)
#   \bsex\b   — blocks "sex" but NOT "sexuel", "sexualité"
#               (patients legitimately discuss sexual health in a diabetes context)
#   Other patterns left as-is: "suicide", "tuer", "drogue", "poison" have no
#   common medical compound that would produce false positives.
FORBIDDEN_SCOPE = [
    r"(?i)suicide",
    r"(?i)tuer",
    r"(?i)\bmort\b",
    r"(?i)drogue",
    r"(?i)poison",
    r"(?i)\bsex\b",
]

class ClinicalShield:
    """
    Clinical Shield (Phase 6)
    ========================
    Safety layer that filters LLM inputs and outputs to prevent
    medical errors or dangerous advice.
    """

    @staticmethod
    def check_safety(text: str) -> bool:
        """Returns True if the text is SAFE, False if it contains violations."""
        all_bad_patterns = EMERGENCY_PATTERNS + SYMPTOMATIC_EMERGENCY + FORBIDDEN_SCOPE
        for pattern in all_bad_patterns:
            if re.search(pattern, text):
                logger.warning(f"ClinicalShield: Violation detected for pattern {pattern}")
                return False
        return True

    @staticmethod
    def triage_vital(glucose_value: float) -> str:
        """
        Shunt IA logic (Triage Vital).
        Detects extreme values that require immediate human intervention
        rather than AI analysis.
        """
        if glucose_value < DIABETES_CONFIG.vital_low:
            return "VITAL_EMERGENCY_HYPO"
        if glucose_value > DIABETES_CONFIG.vital_high:
            return "VITAL_EMERGENCY_HYPER"
        return "STABLE"

    @staticmethod
    def get_emergency_message() -> str:
        """Standardized emergency message to bypass IA."""
        return (
            "DANGER : IAmina a détecté un risque vital immédiat. "
            "Veuillez contacter les urgences ou votre médecin immédiatement. "
            "Ne prenez pas de décision médicale basée sur cette application."
        )
