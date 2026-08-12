"""
IAmina diabetes clinical observation engine.

Authority contract
------------------
This module may surface deterministic, evidence-qualified observations. It must
not diagnose a condition, infer causality from patient-entered context, prescribe
or optimize treatment, or promote an unvalidated prediction into clinical truth.

SQL-first KPI authority remains in ``sql_analytics``. Context associations that
need longitudinal repetition are owned by ``personal_response``. Generative AI
may only verbalize the structured observations produced here.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean, median
from typing import TYPE_CHECKING, Iterable

from core.contracts.capabilities import Capability
from core.llm_gateway import get_gateway_llm
from core.medical_safety import sanitize_patient_visible

from .sql_analytics import AnalyticalKPIs

if TYPE_CHECKING:
    from core.contracts.alert import DomainAlert
    from core.contracts.domain_context import DomainContext

logger = logging.getLogger(__name__)

ADA_2026_GLYCEMIC_SOURCE = "ADA Standards of Care in Diabetes—2026, section 6, DOI 10.2337/dc26-S006"
PHNH_2025_SOURCE = "González-Vidal et al. 2025, DOI 10.1007/s42000-025-00680-0, PMID 40465171"
PRODUCT_OBSERVATION_SOURCE = "IAmina deterministic observational rule v2026-08"

_GENERIC_LIMITATION_FR = (
    "Observation descriptive uniquement : elle ne démontre pas une cause, "
    "ne pose pas de diagnostic et ne justifie pas de modifier un traitement."
)
_GENERIC_LIMITATION_DARIJA = (
    "هاد غير ملاحظة وصفية فالمعطيات: ما كتثبتش السبب، ماشي تشخيص، "
    "وما كتسمحش تبدل العلاج."
)


@dataclass
class ClinicalPattern:
    """Evidence-qualified deterministic observation.

    ``code`` is a neutral machine identifier, not a diagnosis. ``evidence`` is
    the exact descriptive basis that may be passed to a narrator or clinician
    brief. Treatment advice does not belong in this structure.
    """

    code: str
    priority: int
    icon: str
    title: str
    evidence: str
    fallback_content: str
    fallback_action: str
    title_darija: str = ""
    fallback_content_darija: str = ""
    fallback_action_darija: str = ""
    evidence_count: int = 0
    distinct_days: int = 0
    data_scope: str = ""
    evidence_maturity: str = "product_observation"
    source_version: str = PRODUCT_OBSERVATION_SOURCE
    limitations: str = _GENERIC_LIMITATION_FR

    def narration_evidence(self) -> str:
        """Minimal evidence packet safe for LLM narration."""
        parts = [
            f"code={self.code}",
            f"observation={self.evidence}",
            f"source={self.source_version}",
            f"limitations={self.limitations}",
        ]
        if self.evidence_count:
            parts.append(f"observations={self.evidence_count}")
        if self.distinct_days:
            parts.append(f"distinct_days={self.distinct_days}")
        if self.data_scope:
            parts.append(f"scope={self.data_scope}")
        return " | ".join(parts)


@dataclass
class ClinicalReport:
    """Clinical analysis snapshot returned by the domain engine."""

    kpis: AnalyticalKPIs
    patterns: list[ClinicalPattern] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)


def _event_days(entries: Iterable) -> int:
    return len({e.effective_time.date() for e in entries})


def _morning_entries(entries):
    return [e for e in entries if 5 <= e.effective_time.hour <= 10]


def _night_entries(entries):
    return [e for e in entries if e.effective_time.hour >= 22 or e.effective_time.hour <= 2]


def _neutral_action_fr() -> str:
    return (
        "Continue à noter le contexte si cela se reproduit. "
        "Tu peux préparer cette observation pour en parler à ton professionnel de santé."
    )


def _neutral_action_darija() -> str:
    return (
        "إلا تكررات هاد الملاحظة، كمّل دوّن السياق ديالها. "
        "تقدر توجدها باش تهضر عليها مع المختص الصحي ديالك."
    )


def _pattern(
    *,
    code: str,
    priority: int,
    icon: str,
    title: str,
    evidence: str,
    content: str,
    title_darija: str,
    content_darija: str,
    evidence_count: int,
    distinct_days: int,
    data_scope: str,
    source_version: str = PRODUCT_OBSERVATION_SOURCE,
    evidence_maturity: str = "product_observation",
    limitations: str = _GENERIC_LIMITATION_FR,
) -> ClinicalPattern:
    return ClinicalPattern(
        code=code,
        priority=priority,
        icon=icon,
        title=title,
        evidence=f"{evidence} {_GENERIC_LIMITATION_FR}",
        fallback_content=f"{content} {_GENERIC_LIMITATION_FR}",
        fallback_action=_neutral_action_fr(),
        title_darija=title_darija,
        fallback_content_darija=f"{content_darija} {_GENERIC_LIMITATION_DARIJA}",
        fallback_action_darija=_neutral_action_darija(),
        evidence_count=evidence_count,
        distinct_days=distinct_days,
        data_scope=data_scope,
        evidence_maturity=evidence_maturity,
        source_version=source_version,
        limitations=limitations,
    )


def detect_dawn_phenomenon(entries) -> ClinicalPattern | None:
    """Compatibility entry point for a neutral morning-vs-night observation.

    This deliberately does *not* diagnose the dawn phenomenon. Sparse manually
    sampled time-of-day readings cannot establish its mechanism.
    """
    morning = _morning_entries(entries)
    night = _night_entries(entries)
    if len(morning) < 3 or len(night) < 2:
        return None

    avg_morning = mean(float(e.blood_sugar) for e in morning)
    avg_night = mean(float(e.blood_sugar) for e in night)
    delta = avg_morning - avg_night
    if avg_morning <= 145 or avg_night >= 130 or delta <= 30:
        return None

    involved = morning + night
    return _pattern(
        code="MORNING_NIGHT_GLUCOSE_DIFFERENCE",
        priority=2,
        icon="sunrise",
        title="Écart répété entre relevés du matin et de nuit",
        evidence=(
            f"{len(morning)} relevés matinaux : moyenne {avg_morning:.0f} mg/dL; "
            f"{len(night)} relevés nocturnes : moyenne {avg_night:.0f} mg/dL; "
            f"écart descriptif +{delta:.0f} mg/dL."
        ),
        content=(
            "Dans la fenêtre analysée, les relevés enregistrés le matin sont plus élevés "
            "que les relevés enregistrés la nuit. L'échantillonnage selon l'heure peut "
            "influencer cette comparaison; ce résultat n'est pas un diagnostic de "
            "« phénomène de l'aube »."
        ),
        title_darija="فرق متكرر بين قياسات الصباح والليل",
        content_darija=(
            "فالفترة اللي تحللات، القياسات اللي تسجلو فالصباح كانوا أعلى من قياسات الليل. "
            "طريقة ووقت القياس يقدرو يأثرو على المقارنة، وهاد الشي ماشي تشخيص."
        ),
        evidence_count=len(involved),
        distinct_days=_event_days(involved),
        data_scope="time_of_day_glucose_observation",
    )


def detect_post_exercise_hypo(entries) -> ClinicalPattern | None:
    """Neutral low-glucose observation on days with explicitly recorded activity."""
    exercise_days = {
        e.effective_time.date()
        for e in entries
        if getattr(e, "exercised", "") == "yes"
    }
    low_entries = [
        e
        for e in entries
        if float(e.blood_sugar) < 70
        and e.effective_time.date() in exercise_days
    ]
    if len(low_entries) < 3 or _event_days(low_entries) < 2:
        return None

    avg_low = mean(float(e.blood_sugar) for e in low_entries)
    return _pattern(
        code="LOW_GLUCOSE_WITH_RECORDED_ACTIVITY",
        priority=1,
        icon="activity",
        title="Glycémies basses répétées les jours avec activité enregistrée",
        evidence=(
            f"{len(low_entries)} relevés <70 mg/dL sur {_event_days(low_entries)} jours "
            f"où une activité a été explicitement enregistrée; moyenne {avg_low:.0f} mg/dL."
        ),
        content=(
            "Des glycémies basses ont été enregistrées à plusieurs reprises les mêmes jours "
            "qu'une activité physique. La chronologie disponible ne prouve pas que l'activité "
            "a causé ces baisses."
        ),
        title_darija="قياسات سكر هابط تكررات فنهارات تسجلات فيها الرياضة",
        content_darija=(
            "تسجلو قياسات سكر هابط كثر من مرة فنفس النهارات اللي تسجلات فيها الرياضة. "
            "المعطيات ما كتثبتش أن الرياضة هي السبب."
        ),
        evidence_count=len(low_entries),
        distinct_days=_event_days(low_entries),
        data_scope="explicit_activity_context",
        source_version=ADA_2026_GLYCEMIC_SOURCE,
        evidence_maturity="standard_threshold_observational_association",
    )


def _positive_context_observation(
    entries,
    *,
    field_name: str,
    positive_value: str,
    code: str,
    title: str,
    title_darija: str,
    context_label: str,
) -> ClinicalPattern | None:
    """Describe repeated explicit context without manufacturing a control cohort."""
    matching = [e for e in entries if getattr(e, field_name, "") == positive_value]
    if len(matching) < 3 or _event_days(matching) < 2:
        return None

    values = [float(e.blood_sugar) for e in matching]
    window_values = [float(e.blood_sugar) for e in entries]
    if not window_values:
        return None

    matching_median = float(median(values))
    window_median = float(median(window_values))
    evidence = (
        f"{len(matching)} mesures sur {_event_days(matching)} jours avec {context_label} "
        f"explicitement déclaré; médiane {matching_median:.0f} mg/dL; "
        f"médiane de la fenêtre {window_median:.0f} mg/dL."
    )
    return _pattern(
        code=code,
        priority=3,
        icon="journal-check",
        title=title,
        evidence=evidence,
        content=(
            f"Le contexte « {context_label} » a été enregistré à plusieurs reprises avec "
            "des mesures de glycémie. La comparaison est descriptive et n'utilise pas les "
            "anciens champs négatifs/neutres comme groupe contrôle."
        ),
        title_darija=title_darija,
        content_darija=(
            "هاد السياق تسجل كثر من مرة مع قياسات السكر. المقارنة غير وصفية، "
            "وما كتستعملش القيم القديمة السلبية بحال إلا كانت مجموعة contrôle."
        ),
        evidence_count=len(matching),
        distinct_days=_event_days(matching),
        data_scope=f"explicit_{field_name}_context",
    )


def detect_stress_correlation(entries) -> ClinicalPattern | None:
    """Compatibility name; returns a non-causal explicit-stress observation."""
    return _positive_context_observation(
        entries,
        field_name="stressed",
        positive_value="yes",
        code="GLUCOSE_WITH_RECORDED_STRESS",
        title="Mesures répétées avec stress explicitement déclaré",
        title_darija="قياسات متكررة مع الستريس اللي تسجل",
        context_label="stress",
    )


def detect_sleep_impact(entries) -> ClinicalPattern | None:
    """Compatibility name; returns a non-causal poor-sleep context observation."""
    return _positive_context_observation(
        entries,
        field_name="sleep_quality",
        positive_value="bad",
        code="GLUCOSE_WITH_RECORDED_POOR_SLEEP",
        title="Mesures répétées avec mauvais sommeil explicitement déclaré",
        title_darija="قياسات متكررة مع نعاس ماشي مزيان اللي تسجل",
        context_label="mauvais sommeil",
    )


def detect_high_variability(entries) -> ClinicalPattern | None:
    """Retired raw-entry CV detector.

    CV is a SQL-first CGM metric. Recomputing it from arbitrary manual Journal
    samples here would create a second authority and can apply a CGM threshold to
    the wrong modality. Kept as a compatibility symbol and fails closed.
    """
    _ = entries
    return None


def _high_variability_from_kpis(kpis: AnalyticalKPIs) -> ClinicalPattern | None:
    """Build a CV observation only when valid CGM wear eligibility is evidenced."""
    if (
        kpis.cv_pct is None
        or kpis.cv_pct <= 36
        or kpis.days_with_data < 14
        or kpis.cgm_active_pct is None
        or kpis.cgm_active_pct < 70
    ):
        return None

    return _pattern(
        code="CGM_HIGH_VARIABILITY",
        priority=1,
        icon="graph-up-arrow",
        title="Variabilité CGM au-dessus de la référence",
        evidence=(
            f"CV SQL={kpis.cv_pct:.1f}%; couverture CGM={kpis.cgm_active_pct:.1f}%; "
            f"{kpis.days_with_data} jours de données. Référence ADA 2026 : CV ≤36% "
            "avec ≥14 jours et ≥70% de temps CGM actif pour l'interprétation des métriques CGM."
        ),
        content=(
            "La variabilité calculée à partir d'une fenêtre CGM suffisamment couverte est "
            "au-dessus de la référence générale. Cette observation doit être interprétée "
            "avec le contexte clinique individuel."
        ),
        title_darija="التقلب ديال CGM فوق المرجع العام",
        content_darija=(
            "التقلب اللي تحسب من فترة CGM فيها تغطية كافية طالع على المرجع العام. "
            "خاص هاد الملاحظة تتفهم مع السياق الصحي ديال الشخص."
        ),
        evidence_count=kpis.log_count,
        distinct_days=kpis.days_with_data,
        data_scope="eligible_cgm_window",
        source_version=ADA_2026_GLYCEMIC_SOURCE,
        evidence_maturity="standard_of_care_metric",
    )


def detect_food_sensitivity(entries) -> ClinicalPattern | None:
    """Neutral repeated meal-text observation; never labels a food sensitivity."""
    targets = (
        "pizza", "pasta", "pâtes", "riz", "burger", "fast food", "baguette",
        "pain blanc", "couscous", "harira", "msemen", "batbout", "seffa",
        "chebakia", "rfissa", "pastilla", "briouats", "ktefa", "sellou",
        "kaab ghzal", "atay", "jus d'orange", "cornes de gazelle",
    )
    matching = [
        e
        for e in entries
        if any(t in (getattr(e, "meal_description", "") or "").lower() for t in targets)
        and float(e.blood_sugar) > 185
    ]
    if len(matching) < 3 or _event_days(matching) < 2:
        return None

    from collections import Counter

    meal_counts = Counter(
        (getattr(e, "meal_description", "") or "repas enregistré").strip().lower()
        for e in matching
    )
    top_label = meal_counts.most_common(1)[0][0] or "repas enregistré"
    return _pattern(
        code="HIGH_GLUCOSE_WITH_RECORDED_MEAL_TEXT",
        priority=3,
        icon="egg-fried",
        title="Glycémies élevées répétées avec certains repas enregistrés",
        evidence=(
            f"{len(matching)} mesures >185 mg/dL associées dans le Journal à des libellés "
            f"de repas correspondants; libellé le plus fréquent : {top_label}."
        ),
        content=(
            "Des mesures élevées et certains libellés de repas apparaissent ensemble à "
            "plusieurs reprises. Sans paire pré/post-prandiale et sans contrôle des autres "
            "facteurs, cela ne démontre ni une « sensibilité » alimentaire ni l'effet du repas."
        ),
        title_darija="قياسات طالعة تكررات مع شي وجبات مسجلة",
        content_darija=(
            "شي قياسات طالعة وشي أسماء ديال الماكلة بانوا مع بعضهم كثر من مرة. "
            "بلا قياسات قبل/بعد الماكلة ومعلومات أخرى، ما نقدرش نقولو الماكلة هي السبب."
        ),
        evidence_count=len(matching),
        distinct_days=_event_days(matching),
        data_scope="meal_text_association",
    )


def _is_cgm_entry(entry) -> bool:
    return getattr(entry, "source", "") == "cgm"


def detect_somogyi_rebound(entries) -> ClinicalPattern | None:
    """Neutral CGM observation: nocturnal low followed by later morning high.

    The compatibility function name is retained for imports, but the returned
    machine code and wording deliberately avoid diagnosing a Somogyi effect.
    """
    sorted_logs = sorted(entries, key=lambda x: x.effective_time)
    pairs: list[tuple] = []
    for i in range(len(sorted_logs) - 1):
        curr = sorted_logs[i]
        nxt = sorted_logs[i + 1]
        if not (_is_cgm_entry(curr) and _is_cgm_entry(nxt)):
            continue
        is_night_low = (
            curr.effective_time.hour >= 22 or curr.effective_time.hour <= 4
        ) and float(curr.blood_sugar) < 70
        is_morning_high = 5 <= nxt.effective_time.hour <= 11 and float(nxt.blood_sugar) > 180
        time_diff = nxt.effective_time - curr.effective_time
        if (
            is_night_low
            and is_morning_high
            and 0 < time_diff.total_seconds() <= 36000
        ):
            pairs.append((curr, nxt))

    if len(pairs) < 2:
        return None

    involved = [item for pair in pairs for item in pair]
    return _pattern(
        code="NIGHT_LOW_THEN_MORNING_HIGH",
        priority=1,
        icon="moon-stars",
        title="Baisses nocturnes suivies de hausses matinales observées",
        evidence=(
            f"{len(pairs)} séquences CGM avec <70 mg/dL la nuit puis >180 mg/dL le matin "
            "dans les 10 heures suivantes. Le terme « Somogyi » n'est pas utilisé comme "
            "diagnostic ou mécanisme déduit."
        ),
        content=(
            "La fenêtre CGM contient plusieurs séquences où une glycémie basse la nuit est "
            "suivie d'une valeur élevée le matin. Ce motif décrit la chronologie observée; "
            "il ne prouve pas pourquoi la hausse s'est produite."
        ),
        title_darija="سكر هابط فالليل ومن بعدو قياس طالع فالصباح",
        content_darija=(
            "فبيانات CGM بانو كثر من مرة قياس هابط فالليل ومن بعدو قياس طالع فالصباح. "
            "هاد الشي كيصف غير الترتيب اللي بان وما كيحددش السبب."
        ),
        evidence_count=len(involved),
        distinct_days=_event_days(involved),
        data_scope="cgm_night_to_morning_sequence",
        source_version=PHNH_2025_SOURCE,
        evidence_maturity="emerging_evidence_observational_pattern",
        limitations=(
            "Séquence CGM descriptive uniquement. L'étude 2025 porte sur des adultes "
            "avec DT1 et n'autorise pas à diagnostiquer un mécanisme chez un individu."
        ),
    )


def detect_fatigue_correlation(entries) -> ClinicalPattern | None:
    """Compatibility name; returns a non-causal explicit-fatigue observation."""
    return _positive_context_observation(
        entries,
        field_name="fatigue_level",
        positive_value="tired",
        code="GLUCOSE_WITH_RECORDED_FATIGUE",
        title="Mesures répétées avec fatigue explicitement déclarée",
        title_darija="قياسات متكررة مع العيا اللي تسجل",
        context_label="fatigue",
    )


def detect_illness_impact(entries) -> ClinicalPattern | None:
    """Compatibility name; returns a non-causal explicit-illness observation."""
    return _positive_context_observation(
        entries,
        field_name="is_sick",
        positive_value="yes",
        code="GLUCOSE_WITH_RECORDED_ILLNESS",
        title="Mesures répétées pendant une maladie explicitement déclarée",
        title_darija="قياسات متكررة فنهارات المرض اللي تسجل",
        context_label="maladie",
    )


def detect_postmeal_spike(entries) -> ClinicalPattern | None:
    """Describe repeated explicit pre→post-meal rises without treatment advice."""
    by_date: dict = defaultdict(list)
    for entry in sorted(entries, key=lambda x: x.effective_time):
        by_date[entry.effective_time.date()].append(entry)

    rises: list[float] = []
    involved = []
    for day_entries in by_date.values():
        for i, base in enumerate(day_entries):
            if getattr(base, "glycemic_context", "") != "pre_meal":
                continue
            base_val = float(base.blood_sugar)
            for later in day_entries[i + 1 :]:
                hours = (later.effective_time - base.effective_time).total_seconds() / 3600
                if hours > 2:
                    break
                if getattr(later, "glycemic_context", "") != "post_meal":
                    continue
                rise = float(later.blood_sugar) - base_val
                if rise > 60:
                    rises.append(rise)
                    involved.extend([base, later])
                    break

    if len(rises) < 2 or _event_days(involved) < 2:
        return None

    avg_rise = mean(rises)
    return _pattern(
        code="REPEATED_PRE_POST_MEAL_RISE",
        priority=2,
        icon="arrow-up-circle",
        title="Hausses répétées entre mesures avant et après repas",
        evidence=(
            f"{len(rises)} paires explicitement marquées pré/post-repas sur "
            f"{_event_days(involved)} jours; hausse moyenne descriptive +{avg_rise:.0f} mg/dL "
            "dans les 2 heures."
        ),
        content=(
            "Plusieurs paires explicitement enregistrées avant et après un repas montrent "
            "une hausse dans les deux heures. D'autres facteurs peuvent contribuer à ces "
            "variations; l'observation ne détermine ni la cause ni une conduite thérapeutique."
        ),
        title_darija="زيادات تكررات بين قياس قبل وبعد الماكلة",
        content_darija=(
            "كاينين قياسات مسجلين بوضوح قبل وبعد الماكلة وبانو فيهم زيادات متكررة. "
            "عوامل أخرى يقدرو يدخلو، وهاد الملاحظة ما كتحدد لا السبب لا العلاج."
        ),
        evidence_count=len(involved),
        distinct_days=_event_days(involved),
        data_scope="explicit_pre_post_meal_pairs",
    )


# Context-derived compatibility helpers remain callable, but are intentionally
# excluded from the summary/doctor engine. The dedicated personal-response
# service owns longitudinal context eligibility and avoids legacy negative
# controls. Food-text and post-meal heuristic observations also stay out of the
# active engine until the versioned evidence registry can govern them.
_ACTIVE_ENTRY_DETECTORS = (
    detect_dawn_phenomenon,
    detect_post_exercise_hypo,
    detect_somogyi_rebound,
)


def _build_patterns_data(patterns: list[ClinicalPattern]) -> str:
    """Evidence-only block injected into the narrator prompt."""
    return "\n".join(p.narration_evidence() for p in patterns)


def _parse_insights_json(
    text: str,
    patterns: list[ClinicalPattern],
    language: str = "fr",
) -> list[dict]:
    """Parse narrator JSON. Structured output is sanitized before display."""
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    pattern_map = {p.code: p for p in patterns}
    try:
        data = json.loads(clean)
        if not isinstance(data, list):
            raise ValueError("expected JSON array")
    except (json.JSONDecodeError, ValueError):
        logger.warning("ClinicalEngine: formatter returned non-JSON: %s", text[:120])
        return _format_fallback(patterns, language)

    result: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        code = item.get("code", "")
        pattern = pattern_map.get(code)
        if pattern is None or not item.get("content"):
            continue

        use_darija = language == "ar-MA"
        fallback_title = (
            pattern.title_darija or pattern.title
            if use_darija
            else pattern.title
        )
        fallback_action = (
            pattern.fallback_action_darija or pattern.fallback_action
            if use_darija
            else pattern.fallback_action
        )
        result.append(
            {
                "code": code,
                "priority": pattern.priority,
                "icon": pattern.icon,
                "title": item.get("title") or fallback_title,
                "content": item["content"],
                "action": item.get("action") or fallback_action,
            }
        )

    return sanitize_patient_visible(
        result if result else _format_fallback(patterns, language),
        language,
    )


def _format_with_llm(patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:
    """Narrate approved deterministic observations; never create clinical authority."""
    if not patterns:
        return []

    from companion.prompts import FORMAT_USER, get_format_system

    user_prompt = FORMAT_USER.format(patterns_data=_build_patterns_data(patterns))
    try:
        gateway = get_gateway_llm()
        response_text = gateway.complete(
            get_format_system(language),
            user_prompt,
            capability=Capability.SURFACE_DETERMINISTIC_PATTERN,
        ).content
        return _parse_insights_json(response_text, patterns, language)
    except Exception:
        logger.exception("ClinicalEngine: LLM formatter failed")
        return _format_fallback(patterns, language)


def _format_fallback(patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:
    """Deterministic observation-only fallback."""
    use_darija = language == "ar-MA"
    result = []
    for pattern in patterns:
        result.append(
            {
                "code": pattern.code,
                "priority": pattern.priority,
                "icon": pattern.icon,
                "title": (
                    pattern.title_darija or pattern.title
                    if use_darija
                    else pattern.title
                ),
                "content": (
                    pattern.fallback_content_darija or pattern.fallback_content
                    if use_darija
                    else pattern.fallback_content
                ),
                "action": (
                    pattern.fallback_action_darija or pattern.fallback_action
                    if use_darija
                    else pattern.fallback_action
                ),
            }
        )
    return sanitize_patient_visible(result, language)


def run_clinical_analysis(
    entries,
    kpis: AnalyticalKPIs,
    language: str = "fr",
) -> ClinicalReport:
    """Return KPI-backed and conservative deterministic observations."""
    entries = list(entries)
    patterns: list[ClinicalPattern] = []

    cgm_variability = _high_variability_from_kpis(kpis)
    if cgm_variability is not None:
        patterns.append(cgm_variability)

    for detector in _ACTIVE_ENTRY_DETECTORS:
        try:
            result = detector(entries)
            if result is not None:
                patterns.append(result)
        except Exception as exc:
            detector_name = getattr(detector, "__name__", repr(detector))
            logger.warning("ClinicalEngine: detector %s failed: %s", detector_name, exc)

    patterns.sort(key=lambda p: (p.priority, p.code))
    insights = _format_with_llm(patterns, language) if patterns else []
    return ClinicalReport(kpis=kpis, patterns=patterns, insights=insights)


from core.engine.base import BaseEngine  # noqa: E402


def _trend_line(trend: dict) -> str:
    """One-line descriptive week-over-week TIR summary."""
    curr = trend.get("current_week_tir")
    prev = trend.get("prev_week_tir")
    delta = trend.get("tir_delta")
    direction = trend.get("direction", "unknown")
    if curr is None:
        return ""
    if direction == "unknown" or prev is None:
        return f"TIR this week: {curr}%."
    arrow = {"up": "↑", "down": "↓", "stable": "→"}.get(direction, "")
    sign = "+" if delta is not None and delta >= 0 else ""
    return f"Week-over-week TIR: {prev}% → {curr}% ({sign}{delta}pp {arrow})."


class DiabetesEngine(BaseEngine):
    """Diabetes BaseEngine wrapper with deterministic observation authority."""

    def analyze(
        self,
        patient_id: int,
        language: str = "fr",
        days: int = 14,
    ) -> "DomainContext":
        from datetime import timedelta

        from django.db.models import Q
        from django.utils import timezone

        from core.contracts.domain_context import DomainContext
        from diabetes.models import LogEntry
        from diabetes.services.clinical.semantic_compressor import build_chat_context
        from diabetes.services.clinical.sql_analytics import compute_kpis, compute_trend

        kpis = compute_kpis(patient_id=patient_id, days=days)
        if not kpis.has_sufficient_data:
            return DomainContext.empty(language=language)

        since = timezone.now() - timedelta(days=days)
        entries = list(
            LogEntry.objects.filter(
                Q(logged_at__gte=since)
                | Q(logged_at__isnull=True, created_at__gte=since),
                patient_id=patient_id,
                blood_sugar__isnull=False,
            ).order_by("logged_at", "created_at")
        )

        report = run_clinical_analysis(entries, kpis, language=language)
        pivot = build_chat_context(kpis, report.patterns)
        trend = compute_trend(patient_id=patient_id)
        trend_text = _trend_line(trend)
        if trend_text:
            pivot = pivot + " " + trend_text if pivot else trend_text

        return DomainContext(
            kpi_summary={
                "avg_glucose": kpis.avg_glucose,
                "tir_pct": kpis.tir_pct,
                "cv_pct": kpis.cv_pct,
                "gmi": kpis.gmi,
                "tar_pct": kpis.tar_pct,
                "tbr_pct": kpis.tbr_pct,
                "log_count": kpis.log_count,
                "days_with_data": kpis.days_with_data,
            },
            detected_patterns=[p.code for p in report.patterns[:5]],
            insights=report.insights,
            pivot_text=pivot,
            language=language,
            has_sufficient_data=True,
            tone_signals={"primary": kpis.tir_pct, "stability": kpis.cv_pct},
            trend=trend,
            primary_label="TIR",
            patterns_detail=[
                {
                    "code": p.code,
                    "priority": p.priority,
                    "evidence": p.evidence,
                    "evidence_count": p.evidence_count,
                    "distinct_days": p.distinct_days,
                    "source_version": p.source_version,
                    "limitations": p.limitations,
                }
                for p in report.patterns
            ],
        )

    def evaluate_alert(self, entry, language: str = "fr") -> "DomainAlert | None":
        from core.contracts.alert import DomainAlert
        from diabetes.services.clinical.alerts import AlertLevel
        from diabetes.services.clinical.alerts import evaluate as evaluate_alert

        glucose = getattr(entry, "blood_sugar", None)
        if glucose is None:
            return None
        glucose = float(glucose)

        response = evaluate_alert(glucose)
        if response.level == AlertLevel.NONE:
            return None

        blocking = response.level in (AlertLevel.EMERGENCY, AlertLevel.CRITICAL)
        message = response.message_darija if language == "ar-MA" else response.message_fr
        return DomainAlert(
            severity=response.level.value,
            blocking=blocking,
            message=message,
            event_type="emergency",
            event_description=f"Glucose critique : {glucose} mg/dL",
            value=glucose,
        )
