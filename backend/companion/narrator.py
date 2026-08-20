import logging

from companion.parser import parse_llm_json
from companion.prompts import SUMMARY_USER, SYSTEM_BASE, get_language_label
from core.companion.clinical import get_domain_context
from core.llm_gateway import get_gateway_llm
from core.medical_safety import apply_no_prescription_policy
from llm.usage_telemetry import usage_workload_scope

logger = logging.getLogger(__name__)

_FALLBACK_NARRATIVE = (
    "Voici un aperçu de ta semaine. Je n'ai pas pu générer un résumé complet "
    "pour le moment — réessaie dans quelques instants."
)


def summarize(patient, memory, llm=None, language: str = "fr", days: int = 7) -> str:
    """Mode 3: Narrative summary — transforms module KPIs into a warm story.

    Clinical data comes from the active module's engine via the single chassis
    contract (get_domain_context → DomainContext); the narrator is condition-agnostic.
    """
    if llm is None:
        llm = get_gateway_llm()

    ctx = get_domain_context(patient.id, language=language, days=days)

    if not ctx.has_sufficient_data:
        return (
            f"Je n'ai pas encore assez de données sur les {days} derniers jours "
            "pour faire un résumé fiable. Continue à enregistrer tes mesures !"
        )

    patterns_text = (
        "\n".join(
            f"- [{p.get('priority')}] {p.get('code')}: {p.get('evidence')}"
            for p in ctx.patterns_detail
        )
        or "Aucun pattern significatif détecté."
    )

    system = SYSTEM_BASE.format(language=get_language_label(language), tone=memory.current_tone)
    user_prompt = SUMMARY_USER.format(
        window_days=days,
        stats=ctx.pivot_text,
        patterns=patterns_text,
    )

    try:
        with usage_workload_scope("summary"):
            result = llm.complete(system, user_prompt)
        parsed = parse_llm_json(result.content, ["narrative", "key_insight", "doctor_brief"])

        if parsed.get("doctor_brief"):
            logger.info(
                "IAmina doctor_brief for patient=%s: %s",
                patient.id,
                parsed["doctor_brief"],
            )

        return apply_no_prescription_policy(parsed["narrative"] or _FALLBACK_NARRATIVE, language)

    except Exception:
        logger.exception("IAmina narrator.summarize failed for patient=%s", patient.id)
        return _FALLBACK_NARRATIVE
