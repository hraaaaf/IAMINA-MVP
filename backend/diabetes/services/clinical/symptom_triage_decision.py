"""Governed SYMPTOM_TRIAGE advice family.

Urgent classification remains owned by the shared core safety gate. This resolver
handles only current patient-reported symptom messages that survive that gate.
It never diagnoses, attributes cause, prescribes treatment, reassures that a
symptom is benign, or downgrades urgency.
"""
from __future__ import annotations

import re

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from core.contracts.domain_context import DomainContext
from core.input_safety import ALLOW, evaluate_input_safety

_PERSONAL_RE = re.compile(
    r"(?:\b(?:j['’]?ai|je\s+suis|je\s+me\s+sens|je\s+ressens|je\s+vomis|"
    r"i['’]?m|i\s+am|i\s+feel|i\s+have|i['’]?ve\s+been|i\s+keep|"
    r"3ndi|fiya|ana)\b|(?:عندي|أشعر|اشعر|حاس|حاسة|كنحس|أنا|انا))",
    re.IGNORECASE,
)
_SYMPTOM_RE = re.compile(
    r"(?:\b(?:fatigu[eé]?|fatigue|tired|nausea|nauseous|naus[eé]es?|vomit\w*|"
    r"vomissement\w*|soif|thirsty|urine\w*|uriner|peeing|urinating|"
    r"malade|unwell|sick|mal\s+au\s+ventre|douleur\s+abdominale|"
    r"abdominal\s+pain|stomach\s+pain|headache|mal\s+de\s+t[eê]te)\b|"
    r"(?:تعبان|تعبانة|عيان|عيانة|غثيان|قيء|استفراغ|عطشان|عطشانة|"
    r"ألم البطن|الم بطن|كنبول بزاف|تبول كثير))",
    re.IGNORECASE,
)

_EVIDENCE = ("rule.triage.symptom-professional-escalation.v1",)
_FORBIDDEN = (
    "diagnose_from_symptom",
    "attribute_symptom_to_glucose",
    "reassure_symptom_is_benign",
    "downgrade_emergency_urgency",
    "delay_professional_assessment",
    "calculate_insulin_dose",
    "change_treatment",
    "prescribe_symptom_treatment",
)
_LIMITATIONS = (
    "shared_core_emergency_gate_has_precedence",
    "symptom_report_does_not_establish_diagnosis_or_cause",
    "professional_assessment_required_for_patient_specific_symptoms",
)


def classify_symptom_triage(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if evaluate_input_safety(text).action != ALLOW:
        return False
    return bool(_PERSONAL_RE.search(text) and _SYMPTOM_RE.search(text))


def _reply(language: str) -> str:
    if language.startswith("ar"):
        return (
            "كتوصف عرض كتحس به دابا. IAmina ما تقدرش تحدد السبب ولا درجة الخطورة من الشات. "
            "تاصل بالفريق الصحي ديالك باش يدير تقييم مهني. إلا الحالة تزادت بسرعة أو وليتي "
            "حاس براسك فحالة خطيرة، تاصل بخدمات الطوارئ المحلية."
        )
    if language.startswith("en"):
        return (
            "You are describing a current symptom. IAmina cannot determine its cause or "
            "severity from chat alone. Contact your care team for professional assessment. "
            "If you become severely unwell or worsen rapidly, use local emergency services."
        )
    return (
        "Tu décris un symptôme actuel. IAmina ne peut pas en déterminer la cause ni le "
        "niveau de gravité à partir du chat seul. Contacte ton équipe soignante pour une "
        "évaluation professionnelle. Si ton état devient sévère ou s’aggrave rapidement, "
        "utilise les services d’urgence locaux."
    )


def resolve_symptom_triage(
    message: str,
    context: DomainContext,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    del context
    if not classify_symptom_triage(message):
        return None

    decision = AdviceDecision(
        intent="symptom_triage",
        authority_level=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
        decision=AdviceDisposition.ESCALATE,
        rule_id="diabetes.symptom.professional_triage",
        rule_version="1",
        forbidden_actions=_FORBIDDEN,
        evidence_refs=_EVIDENCE,
        required_facts=("current_patient_reported_symptom",),
        limitations=_LIMITATIONS,
        escalation="contact_clinical_team_for_symptom_assessment",
        language=language,
    )
    return AdviceResolution(decision=decision, reply=_reply(language))


__all__ = ["classify_symptom_triage", "resolve_symptom_triage"]
