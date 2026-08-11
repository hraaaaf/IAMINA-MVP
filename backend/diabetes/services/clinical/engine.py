"""
IAmina Clinical Engine - Hybrid Architecture
============================================
Step 1: Pure Python rules detect clinical patterns mathematically.
Step 2: The capability-aware LLM gateway reformulates approved patterns for presentation.
Step 3: Fallback to template messages if no API key is available.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import TYPE_CHECKING

from core.contracts.capabilities import Capability
from core.llm_gateway import get_gateway_llm
from core.medical_safety import sanitize_patient_visible

from .sql_analytics import AnalyticalKPIs

if TYPE_CHECKING:
    from core.contracts.alert import DomainAlert
    from core.contracts.domain_context import DomainContext

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. DATA STRUCTURES
# ─────────────────────────────────────────────


@dataclass
class ClinicalPattern:
    """A detected clinical pattern with context data for LLM formatting."""

    code: str  # Internal code, e.g. "DAWN_PHENOMENON"
    priority: int  # 1 = critical, 2 = important, 3 = informational
    icon: str  # Bootstrap icon name
    title: str  # Short 1-line title (French)
    evidence: str  # Raw numbers / evidence (shown to LLM — always French/English)
    fallback_content: str  # French text used if no API key
    fallback_action: str  # French recommendation text
    # ── Darija (ar-MA) overrides — used when patient preferred_language == "ar-MA" ──
    title_darija: str = ""
    fallback_content_darija: str = ""
    fallback_action_darija: str = ""


@dataclass
class ClinicalReport:
    """Full clinical analysis report returned by the engine."""

    kpis: AnalyticalKPIs  # All KPIs computed by SQL
    patterns: list[ClinicalPattern] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)  # Final formatted insights


# ─────────────────────────────────────────────
# 3. PATTERN DETECTION RULES ENGINE
# ─────────────────────────────────────────────


def _morning_entries(entries):
    """Returns entries logged between 5 AM and 10 AM."""
    return [e for e in entries if 5 <= e.effective_time.hour <= 10]


def _night_entries(entries):
    """Returns entries logged between 10 PM and 2 AM."""
    return [e for e in entries if e.effective_time.hour >= 22 or e.effective_time.hour <= 2]


def detect_dawn_phenomenon(entries) -> ClinicalPattern | None:
    """
    Dawn Phenomenon: High morning glucose (>140) while night glucose was normal (<130).
    Requires at least 3 paired observations.
    """
    morning = _morning_entries(entries)
    night = _night_entries(entries)

    if len(morning) < 3 or len(night) < 2:
        return None

    avg_morning = mean(float(e.blood_sugar) for e in morning)
    avg_night = mean(float(e.blood_sugar) for e in night)

    if avg_morning > 145 and avg_night < 130 and (avg_morning - avg_night) > 30:
        return ClinicalPattern(
            code="DAWN_PHENOMENON",
            priority=2,
            icon="sunrise",
            title="Phénomène de l'Aube détecté",
            evidence=f"Glycémie moyenne le matin : {avg_morning:.0f} mg/dL vs {avg_night:.0f} mg/dL la nuit.",
            fallback_content=(
                f"Vos glycémies matinales ({avg_morning:.0f} mg/dL en moyenne) sont "
                f"significativement plus élevées que vos relevés nocturnes ({avg_night:.0f} mg/dL), "
                "sans hypoglycémie nocturne identifiée. Ce pattern est caractéristique du "
                "phénomène de l'aube, une poussée hormonale matinale (cortisol) naturelle mais "
                "qui peut déséquilibrer votre glycémie."
            ),
            fallback_action="Discutez avec votre médecin d'un ajustement de votre dose d'insuline basale nocturne.",
            title_darija="سكّر الصباح عالي (phénomène de l'aube)",
            fallback_content_darija=(
                f"سكّر ديالك فالصباح ({avg_morning:.0f} mg/dL) كيكون عالي بزاف "
                f"على سكّر الليل ({avg_night:.0f} mg/dL). "
                "هاد شي كيوقع حيت الجسم كيدير هورمونات فالصباح اللي كيزيدو السكّر — "
                "عادي وكيوقع مع بزاف دالناس اللي عندهم السكّر."
            ),
            fallback_action_darija=(
                "هضر مع طبيب ديالك على هاد النمط — هي معلومة مهمة اللي تعاونو يفهم واش وقع."
            ),
        )
    return None


def detect_post_exercise_hypo(entries) -> ClinicalPattern | None:
    """
    Post-Exercise Hypoglycemia: Hypo (<70) within 8h of an exercise session.
    """
    exercise_days = set()
    for e in entries:
        if e.exercised == "yes":
            exercise_days.add(e.effective_time.date())

    hypo_after_exercise = []
    for e in entries:
        if float(e.blood_sugar) < 72 and e.effective_time.date() in exercise_days:
            hypo_after_exercise.append(e)

    if len(hypo_after_exercise) >= 2:
        avg_hypo = mean(float(e.blood_sugar) for e in hypo_after_exercise)
        return ClinicalPattern(
            code="POST_EXERCISE_HYPO",
            priority=1,
            icon="activity",
            title="Hypoglycémies post-effort récurrentes",
            evidence=f"{len(hypo_after_exercise)} épisodes < 72 mg/dL les jours d'activité physique. Moyenne : {avg_hypo:.0f} mg/dL.",
            fallback_content=(
                f"IAmina a détecté {len(hypo_after_exercise)} épisodes hypoglycémiques "
                f"(< 72 mg/dL, moyenne {avg_hypo:.0f} mg/dL) survenant les jours où vous "
                "pratiquez une activité physique. Ce pattern suggère que l'effort augmente "
                "votre sensibilité à l'insuline sans compensation glucidique adaptée."
            ),
            fallback_action="Consommez une collation de 20g de glucides lents (ex: avoine, pain complet) avant de dormir les soirs d'entraînement.",
            title_darija="السكّر حابط بعد الرياضة",
            fallback_content_darija=(
                f"IAmina لقات {len(hypo_after_exercise)} مرّة سكّر ديالك حابط لتحت "
                f"(< 72 mg/dL، معدّل {avg_hypo:.0f} mg/dL) في النهار اللي درتي فيه الرياضة. "
                "الرياضة كتزيد الحساسية للأنسولين — هاد شي عادي وكيوقع مع بزاف دالناس."
            ),
            fallback_action_darija=(
                "حاول تاكل شي حاجة صغيرة — خبز أو فاكهة — بعد الرياضة. "
                "ولا إلا درتي رياضة فالعشية، تاكل شي حاجة قبل النعاس."
            ),
        )
    return None


def detect_stress_correlation(entries) -> ClinicalPattern | None:
    """
    Stress hyperglycemia: Stressed days have significantly higher glucose.
    """
    stressed = [e for e in entries if e.stressed == "yes"]
    calm = [e for e in entries if e.stressed == "no"]

    if len(stressed) < 2 or len(calm) < 2:
        return None

    avg_stressed = mean(float(e.blood_sugar) for e in stressed)
    avg_calm = mean(float(e.blood_sugar) for e in calm)
    delta = avg_stressed - avg_calm

    if delta > 25:
        return ClinicalPattern(
            code="STRESS_HYPERGLYCEMIA",
            priority=2,
            icon="emoji-dizzy",
            title="Corrélation stress → hyperglycémie",
            evidence=f"Jours stressés : {avg_stressed:.0f} mg/dL vs jours calmes : {avg_calm:.0f} mg/dL (différence : +{delta:.0f} mg/dL).",
            fallback_content=(
                f"Sur {len(stressed)} journées stressantes, votre glycémie moyenne atteint "
                f"{avg_stressed:.0f} mg/dL, contre {avg_calm:.0f} mg/dL les jours calmes. "
                f"Cette différence de +{delta:.0f} mg/dL est directement liée aux hormones "
                "du stress (cortisol, adrénaline) qui stimulent la production de glucose par le foie."
            ),
            fallback_action="Pratiquez 5 minutes de cohérence cardiaque avant les réunions ou situations de stress identifiées. Cela peut réduire votre pic glycémique.",
            title_darija="السكّر كيعلى مع الستريس",
            fallback_content_darija=(
                f"في النهارات اللي كنتي فيهم مع الستريس، سكّر ديالك كان {avg_stressed:.0f} mg/dL — "
                f"وفالنهارات الهادية كان {avg_calm:.0f} mg/dL. "
                f"فرق +{delta:.0f} mg/dL — هاد شي من هورمونات الستريس اللي كتزعزع السكّر."
            ),
            fallback_action_darija=(
                "5-10 دالدقائق دالنفس العميق أو promenade قصيرة قبل situation الستريس — كتنفع بزاف."
            ),
        )
    return None


def detect_sleep_impact(entries) -> ClinicalPattern | None:
    """
    Poor sleep → higher next-morning glucose.
    """
    bad_sleep_mornings = []
    good_sleep_mornings = []

    # Group by day
    by_day = defaultdict(list)
    for e in entries:
        by_day[e.effective_time.date()].append(e)

    sorted_days = sorted(by_day.keys())
    for i, day in enumerate(sorted_days[1:], 1):
        prev_day = sorted_days[i - 1]
        prev_entries = by_day[prev_day]
        curr_morning = [e for e in by_day[day] if 5 <= e.effective_time.hour <= 10]

        if not curr_morning:
            continue

        morning_avg = mean(float(e.blood_sugar) for e in curr_morning)
        had_bad_sleep = any(e.sleep_quality == "bad" for e in prev_entries)

        if had_bad_sleep:
            bad_sleep_mornings.append(morning_avg)
        else:
            good_sleep_mornings.append(morning_avg)

    if len(bad_sleep_mornings) >= 2 and len(good_sleep_mornings) >= 2:
        avg_bad = mean(bad_sleep_mornings)
        avg_good = mean(good_sleep_mornings)
        delta = avg_bad - avg_good

        if delta > 20:
            return ClinicalPattern(
                code="SLEEP_IMPACT",
                priority=2,
                icon="moon-stars",
                title="Le manque de sommeil aggrave la glycémie",
                evidence=f"Lendemain d'une mauvaise nuit : {avg_bad:.0f} mg/dL vs bonne nuit : {avg_good:.0f} mg/dL (delta : +{delta:.0f} mg/dL).",
                fallback_content=(
                    f"Le lendemain d'une nuit de mauvaise qualité, votre glycémie matinale "
                    f"atteint en moyenne {avg_bad:.0f} mg/dL — soit +{delta:.0f} mg/dL de plus "
                    f"qu'après une nuit réparatrice ({avg_good:.0f} mg/dL). "
                    "Le manque de sommeil réduit la sensibilité à l'insuline et augmente le cortisol."
                ),
                fallback_action="Priorisez 7 à 8 heures de sommeil. Même une amélioration partielle du sommeil peut réduire notablement votre HbA1c sur le long terme.",
                title_darija="النعاس ماشي مزيان → السكّر عالي فالصباح",
                fallback_content_darija=(
                    f"بعد ليلة ماشي مزيانة، سكّر ديالك فالصباح كيكون {avg_bad:.0f} mg/dL — "
                    f"{delta:.0f} mg/dL زيادة على ليلة مزيانة ({avg_good:.0f} mg/dL). "
                    "النعاس القليل كيقلّص الحساسية للأنسولين وكيزيد الكورتيزول."
                ),
                fallback_action_darija=(
                    "حاول تنعس 7 ل-8 ساعات. حتى إلا ما وصلتيش، شي تحسين صغير كتنفع بزاف على السكّر."
                ),
            )
    return None


def detect_high_variability(entries) -> ClinicalPattern | None:
    """
    High glycemic variability: Coefficient of Variation (CV) > 36% (ADA threshold).
    CV = SD / mean × 100 — normalises for different mean glucose levels.
    A patient at mean=100 with SD=40 (CV=40%) is riskier than mean=200 with SD=55 (CV=27.5%).
    """
    if len(entries) < 5:
        return None

    values = [float(e.blood_sugar) for e in entries]
    sd = stdev(values)
    avg = mean(values)

    if avg == 0:
        return None

    cv = (sd / avg) * 100  # Coefficient of Variation (ADA threshold: >36% = unstable)

    if cv > 36:
        return ClinicalPattern(
            code="HIGH_VARIABILITY",
            priority=1,
            icon="graph-up-arrow",
            title="Variabilité glycémique élevée détectée",
            evidence=f"Écart-type : {sd:.0f} mg/dL, CV : {cv:.0f}%. Cible recommandée : CV < 36%.",
            fallback_content=(
                f"Votre variabilité glycémique est élevée (écart-type : {sd:.0f} mg/dL, "
                f"CV : {cv:.0f}%). Un CV > 36% est associé à un risque accru d'hypoglycémies "
                "non détectées et de complications cardiovasculaires, indépendamment de la "
                "moyenne glycémique."
            ),
            fallback_action="Discutez avec votre médecin pour identifier les causes de ces variations : timing des doses, types d'aliments, ou ajustement de la basale.",
            title_darija="السكّر ماشي مستقرّ (CV مرتفع)",
            fallback_content_darija=(
                f"سكّر ديالك كيتبدّل بزاف (SD: {sd:.0f} mg/dL، CV: {cv:.0f}%). "
                f"إلا CV > 36%، كيكون خطر دالهيبو الخفية ومشكلات دالقلب — "
                "حتى إلا المعدّل دالسكّر مزيان."
            ),
            fallback_action_darija=(
                "هضر مع طبيب ديالك باش نشوفو سبب هاد التبدّلات — "
                "فالماكلة، في التوقيت، أو في شي حاجة أخرى."
            ),
        )
    return None


def detect_food_sensitivity(entries) -> ClinicalPattern | None:
    """
    Food Sensitivity: Glucose peaks (>185 mg/dL) after specific high-carb meals.
    Targets include common Moroccan high-GI foods alongside universal ones.

    SAFETY NOTE: fallback_action MUST NOT prescribe insulin doses or dose changes.
    Any insulin adjustment must be discussed exclusively with the treating physician.
    """
    targets = [
        # Universal
        "pizza",
        "pasta",
        "pâtes",
        "riz",
        "burger",
        "fast food",
        "baguette",
        "pain blanc",
        # Moroccan — high glycemic index
        "couscous",
        "harira",
        "msemen",
        "batbout",
        "seffa",
        "chebakia",
        "rfissa",
        "pastilla",
        "briouats",
        "ktefa",
        "sellou",
        "kaab ghzal",
        # Moroccan sweets / drinks
        "atay",
        "jus d'orange",
        "cornes de gazelle",
    ]
    sensitivity_logs = []

    for e in entries:
        desc = (e.meal_description or "").lower()
        if any(t in desc for t in targets) and float(e.blood_sugar) > 185:
            sensitivity_logs.append(e)

    if len(sensitivity_logs) >= 2:
        # Most frequent offending meal (not simply the first chronological entry)
        from collections import Counter

        meal_counts = Counter(
            (e.meal_description or "repas riche en glucides").strip().lower()
            for e in sensitivity_logs
        )
        top_culprit = meal_counts.most_common(1)[0][0] or "repas riche en glucides"

        return ClinicalPattern(
            code="FOOD_SENSITIVITY",
            priority=2,
            icon="egg-fried",
            title="Sensibilité aux glucides rapides identifiée",
            evidence=f"{len(sensitivity_logs)} pics détectés après des repas comme : {top_culprit}.",
            fallback_content=(
                f"IAmina a identifié {len(sensitivity_logs)} épisodes d'hyperglycémie "
                "marqués survenant systématiquement après des repas riches en glucides "
                f"(ex: {top_culprit}). Votre glycémie réagit fortement à ce type de charge "
                "glucidique — des ajustements alimentaires ou de timing pourraient aider."
            ),
            # ⚠️  SAFETY: must never suggest an insulin dose change — that is the physician's role.
            fallback_action=(
                "Essayez de manger ce type de repas plus lentement, d'ajouter des légumes "
                "ou des protéines pour ralentir l'absorption du glucose, et de faire une "
                "marche de 10-15 minutes après le repas. Parlez à votre médecin ou "
                "diététicien des ajustements possibles pour ces repas spécifiques."
            ),
            title_darija="السكّر كيطلع بزاف بعد شي ماكلة",
            fallback_content_darija=(
                f"IAmina لقات {len(sensitivity_logs)} مرّة سكّر ديالك طلع بزاف "
                f"بعد ماكلة بحال {top_culprit}. "
                "هاد الماكلة كتزعزم السكّر عندك — تزيد تاكل شوية شوية وتزيد خضرة أو بروتين."
            ),
            # ⚠️  SAFETY: la même règle s'applique en Darija
            fallback_action_darija=(
                "حاول تاكل شوية شوية وتزيد خضرة أو بروتين مع هاد الماكلة. "
                "promenade 10-15 دالدقائق من بعد الماكلة — كتنفع بزاف. "
                "هضر مع طبيب أو diététicien ديالك على هاد الماكلة بالذات."
            ),
        )
    return None


def detect_somogyi_rebound(entries) -> ClinicalPattern | None:
    """
    Somogyi Effect: Hypo at night (<70) followed by hyper in the morning (>160).
    """
    # Requires sorted data
    sorted_logs = sorted(entries, key=lambda x: x.effective_time)
    rebounds = 0

    for i in range(len(sorted_logs) - 1):
        curr = sorted_logs[i]
        nxt = sorted_logs[i + 1]

        # Hypo at night
        is_night_hypo = (curr.effective_time.hour >= 22 or curr.effective_time.hour <= 4) and float(
            curr.blood_sugar
        ) < 72
        # Hyper in the morning (within 10 hours)
        is_morning_hyper = (5 <= nxt.effective_time.hour <= 11) and float(nxt.blood_sugar) > 165

        time_diff = nxt.effective_time - curr.effective_time
        if is_night_hypo and is_morning_hyper and time_diff.total_seconds() < 36000:
            rebounds += 1

    if rebounds >= 2:  # ≥ 2 events required — one could be coincidence (P1 fix)
        return ClinicalPattern(
            code="SOMOGYI_REBOUND",
            priority=1,
            icon="lightning-charge",
            title="Effet rebond (Somogyi) détecté",
            evidence=f"Hypoglycémie nocturne suivie d'une réaction hyperglycémique matinale ({rebounds} fois).",
            fallback_content=(
                "Votre corps semble réagir violemment à vos baisses de sucre nocturnes. "
                "Pour compenser une hypoglycémie durant la nuit, votre foie libère du glucose "
                "en urgence, provoquant un pic glycémique au réveil. C'est l'effet Somogyi."
            ),
            fallback_action="Ne corrigez pas l'hyperglycémie du matin trop agressivement. Traitez plutôt la cause en ajustant votre insuline basale du soir avec votre médecin.",
            title_darija="السكّر حابط فاللّيل، طلع فالصباح (effet Somogyi)",
            fallback_content_darija=(
                f"الجسم ديالك كيرد من نقص السكّر فاللّيل بزيادة بزاف فالصباح "
                f"({rebounds} مرّة). "
                "هاد هو 'effet Somogyi' — الكبد كيحل غلوكوز كيفما السكّر هبط فاللّيل."
            ),
            fallback_action_darija=(
                "ماتصرّرش السكّر فالصباح بشورة. هضر مع طبيب ديالك على هاد النمط دالليل."
            ),
        )
    return None


def detect_fatigue_correlation(entries) -> ClinicalPattern | None:
    """
    Fatigue correlation: days where fatigue_level is not 'ok' show significantly
    higher glucose than non-fatigue days (delta > 20 mg/dL).
    Requires at least 2 fatigue days and 2 non-fatigue days.
    """
    fatigue_days = [e for e in entries if getattr(e, "fatigue_level", "ok") != "ok"]
    normal_days = [e for e in entries if getattr(e, "fatigue_level", "ok") == "ok"]

    if len(fatigue_days) < 2 or len(normal_days) < 2:
        return None

    avg_fatigue = mean(float(e.blood_sugar) for e in fatigue_days)
    avg_normal = mean(float(e.blood_sugar) for e in normal_days)
    delta = avg_fatigue - avg_normal

    if delta > 20:
        return ClinicalPattern(
            code="FATIGUE_CORRELATION",
            priority=2,
            icon="battery-half",
            title="La fatigue aggrave la glycémie",
            evidence=(
                f"Jours avec fatigue : {avg_fatigue:.0f} mg/dL vs jours normaux : "
                f"{avg_normal:.0f} mg/dL (différence : +{delta:.0f} mg/dL)."
            ),
            fallback_content=(
                f"Sur {len(fatigue_days)} journées avec fatigue, votre glycémie moyenne "
                f"atteint {avg_fatigue:.0f} mg/dL, contre {avg_normal:.0f} mg/dL les jours "
                f"sans fatigue. Cette différence de +{delta:.0f} mg/dL suggère que la fatigue "
                "perturbe la régulation glycémique, possiblement via le cortisol ou un "
                "sommeil non récupérateur."
            ),
            fallback_action=(
                "Notez les heures de sommeil et la qualité de repos. Si la fatigue est "
                "chronique, consultez votre médecin pour évaluer un lien avec votre "
                "traitement ou d'autres causes sous-jacentes."
            ),
            title_darija="التعب كيزيد السكّر",
            fallback_content_darija=(
                f"فالنهارات اللي كنتي فيهم تعبانة، سكّر ديالك كان {avg_fatigue:.0f} mg/dL — "
                f"وفالنهارات العادية كان {avg_normal:.0f} mg/dL. "
                f"فرق +{delta:.0f} mg/dL — التعب كيزعزع السكّر عبر الكورتيزول."
            ),
            fallback_action_darija=(
                "دوّن ساعات النعاس وجودتو. إلا التعب كيتكرّر، هضر مع طبيب ديالك."
            ),
        )
    return None


def detect_illness_impact(entries) -> ClinicalPattern | None:
    """
    ADA Sick Day Rules pattern: sick days (is_sick == 'yes') with significantly
    higher glucose vs healthy days (delta > 40 mg/dL).
    Escalated to priority=1 when delta > 80 mg/dL (severe hyperglycemia risk).
    Requires at least 2 sick days and 2 healthy days.
    """
    sick_entries = [e for e in entries if getattr(e, "is_sick", "no") == "yes"]
    healthy_entries = [e for e in entries if getattr(e, "is_sick", "no") == "no"]

    if len(sick_entries) < 2 or len(healthy_entries) < 2:
        return None

    avg_sick = mean(float(e.blood_sugar) for e in sick_entries)
    avg_healthy = mean(float(e.blood_sugar) for e in healthy_entries)
    delta = avg_sick - avg_healthy

    if delta <= 40:
        return None

    priority = 1 if delta > 80 else 2

    return ClinicalPattern(
        code="ILLNESS_IMPACT",
        priority=priority,
        icon="thermometer-half",
        title="Impact de la maladie sur la glycémie",
        evidence=(
            f"Jours de maladie : {avg_sick:.0f} mg/dL vs jours sains : "
            f"{avg_healthy:.0f} mg/dL (différence : +{delta:.0f} mg/dL)."
        ),
        fallback_content=(
            f"Lors de vos {len(sick_entries)} journées de maladie, votre glycémie "
            f"a atteint {avg_sick:.0f} mg/dL en moyenne, soit +{delta:.0f} mg/dL "
            f"de plus que les jours sains ({avg_healthy:.0f} mg/dL). "
            "La maladie (infection, fièvre) augmente la résistance à l'insuline et "
            "stimule la production hépatique de glucose — règles ADA Sick Day."
        ),
        fallback_action=(
            "Mesurez votre glycémie toutes les 2-4 heures lors des épisodes de maladie. "
            "Maintenez une hydratation suffisante et consultez votre médecin si la glycémie "
            "dépasse 300 mg/dL ou si des corps cétoniques sont détectés."
        ),
        title_darija="المرض كيزيد السكّر بزاف",
        fallback_content_darija=(
            f"فالنهارات اللي كنتي فيهم مريضة، سكّر ديالك وصل {avg_sick:.0f} mg/dL — "
            f"+{delta:.0f} mg/dL زيادة على النهارات الصحيحة ({avg_healthy:.0f} mg/dL). "
            "المرض كيزيد مقاومة الأنسولين — هاد هو قاعدة ADA Sick Day."
        ),
        fallback_action_darija=(
            "قيس السكّر كل 2-4 ساعات وأنتي مريضة. إلا السكّر فاق 300 mg/dL، هضري فوراً مع طبيب ديالك."
        ),
    )


def detect_postmeal_spike(entries) -> ClinicalPattern | None:
    """
    Post-meal spike: glucose rises > 60 mg/dL within 2 hours of a logged meal.
    Requires at least 2 paired readings (pre-meal + post-meal on the same day).
    """
    from collections import defaultdict
    from datetime import timedelta

    meal_entries = [
        e for e in entries if getattr(e, "meal_type", None) and float(e.blood_sugar) > 0
    ]
    if len(meal_entries) < 2:
        return None

    # Group by date to find same-day pairs
    by_date = defaultdict(list)
    for e in sorted(entries, key=lambda x: x.effective_time):
        day = e.effective_time.date()
        by_date[day].append(e)

    spike_events = []
    for day, day_entries in by_date.items():
        # Look for a meal-tagged entry followed by a higher reading within 2 h
        for i, base in enumerate(day_entries):
            if not getattr(base, "meal_type", None):
                continue
            base_val = float(base.blood_sugar)
            for later in day_entries[i + 1 :]:
                delta_h = (later.effective_time - base.effective_time).total_seconds() / 3600
                if delta_h > 2:
                    break
                rise = float(later.blood_sugar) - base_val
                if rise > 60:
                    spike_events.append(rise)
                    break

    if len(spike_events) >= 2:
        avg_rise = mean(spike_events)
        return ClinicalPattern(
            code="POSTMEAL_SPIKE",
            priority=2,
            icon="arrow-up-circle",
            title="Pics post-prandiaux récurrents détectés",
            evidence=(
                f"{len(spike_events)} épisodes — hausse moyenne de +{avg_rise:.0f} mg/dL "
                "dans les 2 h après le repas."
            ),
            fallback_content=(
                f"IAmina a détecté {len(spike_events)} hausses de glycémie importantes "
                f"(+{avg_rise:.0f} mg/dL en moyenne) dans les 2 heures suivant un repas. "
                "Ces pics post-prandiaux répétés augmentent le stress oxydatif et le risque "
                "cardiovasculaire indépendamment de l'HbA1c."
            ),
            fallback_action=(
                "Essayez de prendre l'insuline rapide 10-15 minutes avant de manger, "
                "de réduire les glucides à index glycémique élevé, ou de marcher "
                "15 minutes après le repas."
            ),
            title_darija="السكّر كيطلع بزاف بعد الماكلة",
            fallback_content_darija=(
                f"IAmina لقات {len(spike_events)} مرّة سكّر ديالك طلع "
                f"+{avg_rise:.0f} mg/dL في الساعتين من بعد الماكلة. "
                "هاد الـpics كيزيدو الخطر على القلب والعروق — حتى إلا المعدّل دالسكّر مزيان."
            ),
            fallback_action_darija=(
                "حاول تاكل شوية شوية وتزيد خضرة أو بروتين مع الوجبة. "
                "promenade 15 دالدقائق من بعد الماكلة — كتنفع بزاف."
            ),
        )
    return None


# ─────────────────────────────────────────────
# 4. LLM REFORMULATOR (JSON contract)
# ─────────────────────────────────────────────


def _build_patterns_data(patterns: list[ClinicalPattern]) -> str:
    """Compact evidence block injected into FORMAT_USER."""
    lines = []
    for p in patterns:
        lines.append(f"[{p.code}] {p.title} — {p.evidence}")
    return "\n".join(lines)


def _parse_insights_json(
    text: str, patterns: list[ClinicalPattern], language: str = "fr"
) -> list[dict]:
    """Parse JSON array from LLM formatter. Fallback if malformed."""
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    pattern_map = {p.code: p for p in patterns}

    try:
        data = json.loads(clean)
        if not isinstance(data, list):
            raise ValueError("expected JSON array")
    except (json.JSONDecodeError, ValueError):
        logger.warning("ClinicalEngine: formatter returned non-JSON: %s", text[:120])
        return _format_fallback(patterns, language)

    result = []
    for item in data:
        code = item.get("code", "")
        pattern = pattern_map.get(code)
        if pattern and item.get("content"):
            # Title: use LLM output if provided, else pick by language
            use_darija = language == "ar-MA"
            title = item.get("title") or (
                (pattern.title_darija or pattern.title) if use_darija else pattern.title
            )
            fallback_action = (
                (pattern.fallback_action_darija or pattern.fallback_action)
                if use_darija
                else pattern.fallback_action
            )
            result.append(
                {
                    "code": code,
                    "priority": pattern.priority,
                    "icon": pattern.icon,
                    "title": title,
                    "content": item["content"],
                    "action": item.get("action", fallback_action),
                }
            )

    return sanitize_patient_visible(
        result if result else _format_fallback(patterns, language),
        language,
    )


def _format_with_llm(patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:
    """Reformat detected patterns into empathetic insights via JSON contract.
    Language is injected so the LLM reformulates in the patient's language."""
    if not patterns:
        return []

    from companion.prompts import FORMAT_USER, get_format_system

    patterns_data = _build_patterns_data(patterns)
    user_prompt = FORMAT_USER.format(patterns_data=patterns_data)

    try:
        # PHI-AUDIT(P1.3): verified no PHI in prompts at this callsite.
        # FORMAT_USER contains only clinical pattern codes + evidence text (no name, CIN, DOB).
        # get_format_system() injects language label only.
        # The formatter keeps its endpoint-specific JSON schema while provider access goes
        # through the shared capability-aware gateway.
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
    """Template-based fallback when no API is available.
    Uses Darija strings when language == 'ar-MA' and the override is set;
    falls back to French otherwise."""
    use_darija = language == "ar-MA"
    result = []
    for p in patterns:
        result.append(
            {
                "code": p.code,
                "priority": p.priority,
                "icon": p.icon,
                "title": (p.title_darija or p.title) if use_darija else p.title,
                "content": (p.fallback_content_darija or p.fallback_content)
                if use_darija
                else p.fallback_content,
                "action": (p.fallback_action_darija or p.fallback_action)
                if use_darija
                else p.fallback_action,
            }
        )
    return sanitize_patient_visible(result, language)


# ─────────────────────────────────────────────
# 5. MAIN ENGINE ENTRYPOINT
# ─────────────────────────────────────────────


def run_clinical_analysis(entries, kpis: AnalyticalKPIs, language: str = "fr") -> ClinicalReport:
    """
    Main entry point for the clinical analysis engine.

    Args:
        entries:  QuerySet or list of LogEntry objects.
        kpis:     Pre-computed SQL KPIs from sql_analytics.compute_kpis().
        language: Patient preferred_language code (e.g. 'fr', 'ar-MA', 'ar').
                  Drives fallback text language and LLM reformulation language.
    """
    entries = list(entries)

    if not entries:
        return ClinicalReport(kpis=kpis)

    # ── Pattern Detection ──
    detectors = [
        detect_dawn_phenomenon,
        detect_post_exercise_hypo,
        detect_stress_correlation,
        detect_sleep_impact,
        detect_high_variability,
        detect_food_sensitivity,
        detect_somogyi_rebound,
        detect_postmeal_spike,
        detect_fatigue_correlation,
        detect_illness_impact,
    ]

    patterns = []
    for detector in detectors:
        try:
            result = detector(entries)
            if result:
                patterns.append(result)
        except Exception as e:
            detector_name = getattr(detector, "__name__", repr(detector))
            logger.warning(f"ClinicalEngine: Detector {detector_name} failed: {e}")

    # Sort by priority (1 = most critical first)
    patterns.sort(key=lambda p: p.priority)

    # ── LLM Formatting ──
    insights = _format_with_llm(patterns, language) if patterns else []

    return ClinicalReport(
        kpis=kpis,
        patterns=patterns,
        insights=insights,
    )


# ─────────────────────────────────────────────
# 6. DIABETESENGINE — BaseEngine WRAPPER (DA-03 S1)
# ─────────────────────────────────────────────

from core.engine.base import BaseEngine  # noqa: E402 — intentional bottom import to avoid circular


def _trend_line(trend: dict) -> str:
    """One-line English summary of week-over-week TIR for the pivot text."""
    curr = trend.get("current_week_tir")
    prev = trend.get("prev_week_tir")
    delta = trend.get("tir_delta")
    direction = trend.get("direction", "unknown")
    if curr is None:
        return ""
    if direction == "unknown" or prev is None:
        return f"TIR this week: {curr}%."
    arrow = {"up": "↑", "down": "↓", "stable": "→"}.get(direction, "")
    sign = "+" if delta >= 0 else ""
    return f"Week-over-week TIR: {prev}% → {curr}% ({sign}{delta}pp {arrow})."


class DiabetesEngine(BaseEngine):
    """
    Concrete :class:`BaseEngine` for diabetes (P4.5 single clinical contract).

    analyze() fetches its own LogEntry data + SQL KPIs, runs the detector suite,
    and returns an enriched :class:`DomainContext` consumed by both narrate() and
    the companion runtime. evaluate_alert() wraps the offline glucose safety gate.
    """

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
                Q(logged_at__gte=since) | Q(logged_at__isnull=True, created_at__gte=since),
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
                {"code": p.code, "priority": p.priority, "evidence": p.evidence}
                for p in report.patterns
            ],
        )

    def evaluate_alert(self, entry, language: str = "fr") -> "DomainAlert | None":
        from core.contracts.alert import DomainAlert
        from diabetes.services.clinical.alerts import AlertLevel
        from diabetes.services.clinical.alerts import evaluate as evaluate_alert

        g = getattr(entry, "blood_sugar", None)
        if g is None:
            return None
        g = float(g)

        resp = evaluate_alert(g)
        if resp.level == AlertLevel.NONE:
            return None

        blocking = resp.level in (AlertLevel.EMERGENCY, AlertLevel.CRITICAL)
        message = resp.message_darija if language == "ar-MA" else resp.message_fr
        return DomainAlert(
            severity=resp.level.value,
            blocking=blocking,
            message=message,
            event_type="emergency",
            event_description=f"Glucose critique : {g} mg/dL",
            value=g,
        )
