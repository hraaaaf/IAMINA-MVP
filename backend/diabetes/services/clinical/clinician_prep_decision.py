"""Governed CLINICIAN_PREP advice family.

This family reuses the certified consultation-brief.v1 projection. It may organize
approved structured facts into discussion preparation, but it cannot diagnose,
prescribe, change treatment, decide urgency, override a clinician, or invent
missing evidence.
"""
from __future__ import annotations

import re
from datetime import timedelta

from django.utils import timezone

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from diabetes.services.clinical.consultation_brief_assembler import (
    assemble_consultation_brief,
)

_CLINICIAN_RE = re.compile(
    r"(?:\b(?:médecin|medecin|docteur|doctor|clinician|tbib|tobib)\b|"
    r"(?:ال)?طبيب|(?:ال)?دكتور)",
    re.IGNORECASE,
)
_PREP_RE = re.compile(
    r"(?:\b(?:prépar\w*|prepar\w*|rendez[- ]?vous|appointment|visit|"
    r"question\w*|ask|discuss|parler|dire|résum\w*|resum\w*|summary|"
    r"bring|apporter|montrer|show)\b|"
    r"(?:نوجد|نحضّر|نحضر|أسئلة|اسئلة|نسول|نهضر|نوري|نلخص|نلخّص))",
    re.IGNORECASE,
)

_EVIDENCE = ("rule.consultation.preparation.v1",)
_FORBIDDEN = (
    "diagnose_from_consultation_brief",
    "infer_causality_from_consultation_brief",
    "calculate_insulin_dose",
    "change_treatment",
    "prescribe_treatment",
    "override_clinician",
    "decide_urgency",
    "invent_missing_clinical_data",
)
_LIMITATIONS = (
    "consultation_brief_structured_fields_only",
    "clinician_remains_medical_decision_authority",
    "no_diagnosis_causality_dose_or_treatment_change",
)

_WINDOW_DAYS = 14


def classify_clinician_prep(message: str) -> bool:
    text = (message or "").strip()
    return bool(text and _CLINICIAN_RE.search(text) and _PREP_RE.search(text))


def _brief_topics(brief) -> tuple[str, ...]:
    keys = {item.key for item in brief.items}
    topics: list[str] = []
    if any(key.startswith("recorded_glucose.") for key in keys):
        topics.append("recorded_glucose")
    if any(key.startswith("clinical_twin.") for key in keys):
        topics.append("governed_context_observations")
    if any(key.startswith("companion_change.") for key in keys):
        topics.append("descriptive_changes_since_review")
    if brief.missing_data:
        topics.append("missing_or_limited_data")
    return tuple(topics)


def _reply(language: str, *, topics: tuple[str, ...], has_items: bool) -> str:
    if language.startswith("ar"):
        if has_items:
            intro = "باش توجد الموعد، IAmina جمعت غير المعلومات المنظمة والمسموح بها."
        else:
            intro = "المعلومات المنظمة المتاحة دابا محدودة، لذلك التحضير غادي يبقى عام."
        labels = {
            "recorded_glucose": "القياسات المسجلة",
            "governed_context_observations": "الملاحظات المنظمة على السياق",
            "descriptive_changes_since_review": "التغييرات الوصفية من آخر مراجعة",
            "missing_or_limited_data": "المعلومات الناقصة أو المحدودة",
        }
        present = "، ".join(labels[item] for item in topics if item in labels)
        scope = f" تقدر تجيب معاك: {present}." if present else ""
        return (
            f"{intro}{scope} أسئلة تقدر تسول للطبيب: شنو أهم حاجة كتشوفها فهاد المعطيات؟ "
            "شنو المعلومات اللي خاصها تكمل؟ وشنو خاصني نراقب حتى الموعد الجاي؟ "
            "IAmina ما كتديرش تشخيص وما كتبدلش العلاج."
        )

    if language.startswith("en"):
        intro = (
            "For your appointment, IAmina has organized only approved structured information."
            if has_items
            else "The approved structured information available right now is limited, so the preparation stays general."
        )
        labels = {
            "recorded_glucose": "recorded glucose data",
            "governed_context_observations": "governed context observations",
            "descriptive_changes_since_review": "descriptive changes since the last review",
            "missing_or_limited_data": "missing or limited data",
        }
        present = ", ".join(labels[item] for item in topics if item in labels)
        scope = f" You can bring: {present}." if present else ""
        return (
            f"{intro}{scope} Useful questions for your clinician: What stands out in these records? "
            "What information is still missing? What should I keep monitoring before the next review? "
            "IAmina does not diagnose or change treatment."
        )

    intro = (
        "Pour ton rendez-vous, IAmina a organisé uniquement les informations structurées déjà autorisées."
        if has_items
        else "Les informations structurées autorisées sont limitées pour l’instant, donc la préparation reste générale."
    )
    labels = {
        "recorded_glucose": "tes mesures de glycémie enregistrées",
        "governed_context_observations": "les observations de contexte déjà gouvernées",
        "descriptive_changes_since_review": "les changements descriptifs depuis le dernier point",
        "missing_or_limited_data": "les données manquantes ou limitées",
    }
    present = ", ".join(labels[item] for item in topics if item in labels)
    scope = f" Tu peux apporter : {present}." if present else ""
    return (
        f"{intro}{scope} Questions utiles à poser : Qu’est-ce qui ressort de ces données ? "
        "Quelles informations manquent encore ? Qu’est-ce que je dois continuer à surveiller avant le prochain point ? "
        "IAmina ne pose pas de diagnostic et ne modifie pas le traitement."
    )


def resolve_clinician_prep(
    patient_id: int,
    message: str,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    if not classify_clinician_prep(message):
        return None

    window_end = timezone.now()
    window_start = window_end - timedelta(days=_WINDOW_DAYS)
    brief = assemble_consultation_brief(
        patient_id=patient_id,
        window_start=window_start,
        window_end=window_end,
    )
    topics = _brief_topics(brief)
    has_items = bool(brief.items)

    decision = AdviceDecision(
        intent="clinician_prep",
        authority_level=(
            AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL
            if has_items
            else AdviceAuthorityLevel.L1_EDUCATION
        ),
        decision=AdviceDisposition.CONSTRAIN,
        rule_id=(
            "diabetes.clinician_prep.structured_brief"
            if has_items
            else "diabetes.clinician_prep.insufficient_data"
        ),
        rule_version="1",
        allowed_actions=(
            ("prepare_clinician_discussion", "summarize_approved_consultation_brief")
            if has_items
            else ("explain_consultation_preparation",)
        ),
        forbidden_actions=_FORBIDDEN,
        required_facts=("certified_consultation_brief",),
        missing_facts=(() if has_items else ("approved_consultation_brief_items",)),
        evidence_refs=_EVIDENCE,
        limitations=_LIMITATIONS + tuple(brief.limitations),
        language=language,
    )
    return AdviceResolution(
        decision=decision,
        reply=_reply(language, topics=topics, has_items=has_items),
    )


__all__ = ["classify_clinician_prep", "resolve_clinician_prep"]
