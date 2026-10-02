"""Deterministic read-only routing for patient-owned application context.

This family answers factual questions from persisted IAmina sources without any
LLM authority. It never diagnoses, recommends treatment, or infers missing data.
"""
from __future__ import annotations

import re
from datetime import timedelta
from enum import StrEnum

from django.db.models import Q
from django.utils import timezone

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from diabetes.models import CGMReadingRecord, DiabetesProfile, LabReport, LogEntry
from diabetes.services.clinical.paired_meal_response import compute_paired_meal_response
from diabetes.services.clinical.proactive_preview import preview_proactive_insights


class WholeAppIntent(StrEnum):
    DIABETES_TYPE = "profile_diabetes_type"
    TREATMENT = "profile_treatment"
    TARGETS = "profile_targets"
    MEAL_HISTORY = "journal_meal_history"
    EXACT_GLUCOSE = "journal_exact_glucose"
    SLEEP_HISTORY = "journal_sleep_history"
    STRESS_HISTORY = "journal_stress_history"
    LATEST_LAB = "document_latest_lab"
    IMPORTED_MEDICATIONS = "document_imported_medications"
    LATEST_CGM = "cgm_latest_reading"
    PROACTIVE_PENDING = "proactive_pending"
    PAIRED_MEALS = "paired_meal_history"


_PATTERNS: tuple[tuple[WholeAppIntent, re.Pattern[str]], ...] = (
    (
        WholeAppIntent.IMPORTED_MEDICATIONS,
        re.compile(
            r"(?:m[eé]dicament|medication|medications|دواء|أدوية).{0,40}"
            r"(?:document|rapport|ordonnance|import|extrait|extracted|مستند|تقرير)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.PAIRED_MEALS,
        re.compile(
            r"(?:pr[eé][ -]?post|avant.{0,12}apr[eè]s|pre.{0,12}post|"
            r"[eé]pisode.{0,12}repas|paired.{0,12}meal)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.LATEST_CGM,
        re.compile(
            r"(?:derni[eè]re|latest|last).{0,24}(?:cgm|capteur|sensor).{0,20}"
            r"(?:mesure|lecture|reading|glucose)?|"
            r"(?:cgm|capteur|sensor).{0,24}(?:derni[eè]re|latest|last).{0,16}"
            r"(?:mesure|lecture|reading)?",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.DIABETES_TYPE,
        re.compile(
            r"(?:quel|what).{0,12}(?:type).{0,12}(?:diab[eè]te|diabetes)|"
            r"(?:type).{0,12}(?:diab[eè]te|diabetes).{0,18}(?:enregistr|record)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.TREATMENT,
        re.compile(
            r"(?:quel|what).{0,16}(?:traitement|treatment).{0,20}"
            r"(?:enregistr|profil|record|profile)?|"
            r"(?:traitement|treatment).{0,20}(?:enregistr|profil|record|profile)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.TARGETS,
        re.compile(
            r"(?:objectif|cible|target|plage).{0,24}(?:glyc[eé]mi|glucose|enregistr|configur)|"
            r"(?:quels?|what).{0,18}(?:objectifs?|targets?).{0,18}(?:glyc[eé]mi|glucose)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.MEAL_HISTORY,
        re.compile(
            r"(?:qu['’ ]?est[- ]?ce que|quoi|what).{0,16}(?:mang[eé]|eat|ate)|"
            r"(?:mang[eé]|repas|meal).{0,22}(?:hier|yesterday|journal|histor)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.EXACT_GLUCOSE,
        re.compile(
            r"(?:glyc[eé]mie|glucose|sucre).{0,32}(?:hier|yesterday).{0,16}\d{1,2}\s*h|"
            r"(?:hier|yesterday).{0,22}\d{1,2}\s*h.{0,24}(?:glyc[eé]mie|glucose|sucre)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.SLEEP_HISTORY,
        re.compile(
            r"(?:sommeil|dormi|dormir|sleep|slept).{0,28}(?:semaine|week|histor|journal)|"
            r"(?:comment|how).{0,18}(?:dormi|slept|sommeil|sleep)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.STRESS_HISTORY,
        re.compile(
            r"(?:stress|stress[eé]|stressed).{0,28}(?:semaine|week|histor|journal)|"
            r"(?:est[- ]?ce que|was i).{0,18}(?:stress|stressed)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.LATEST_LAB,
        re.compile(
            r"(?:dernier|derni[eè]re|latest|last).{0,24}"
            r"(?:rapport|bilan|labo|laboratoire|lab|document)|"
            r"(?:rapport|bilan|labo|laboratoire|lab|document).{0,24}"
            r"(?:dernier|derni[eè]re|latest|last)",
            re.IGNORECASE,
        ),
    ),
    (
        WholeAppIntent.PROACTIVE_PENDING,
        re.compile(
            r"(?:observation|insight|alerte|suggestion).{0,24}"
            r"(?:attente|pending|proactiv)|"
            r"(?:proactiv).{0,24}(?:attente|pending|observation|insight)",
            re.IGNORECASE,
        ),
    ),
)

_FORBIDDEN = (
    "diagnose_from_patient_data",
    "infer_causality",
    "calculate_insulin_dose",
    "change_treatment",
    "invent_missing_patient_data",
)

_LIMITATIONS = (
    "read_only_patient_owned_data",
    "descriptive_only",
    "no_diagnosis_or_treatment_change",
)


def classify_whole_app_context(message: str) -> WholeAppIntent | None:
    text = (message or "").strip()
    if not text:
        return None
    for intent, pattern in _PATTERNS:
        if pattern.search(text):
            return intent
    return None


def _decision(intent: WholeAppIntent, language: str) -> AdviceDecision:
    return AdviceDecision(
        intent=intent.value,
        authority_level=AdviceAuthorityLevel.L1_EDUCATION,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id=f"diabetes.context.{intent.value}",
        rule_version="1",
        allowed_actions=("read_patient_owned_data", "describe_persisted_facts"),
        forbidden_actions=_FORBIDDEN,
        evidence_refs=("product.patient-owned-persisted-data.v1",),
        limitations=_LIMITATIONS,
        language=language,
    )


def _profile(patient_id: int) -> DiabetesProfile | None:
    return (
        DiabetesProfile.objects.select_related("base_profile")
        .filter(base_profile__patient_id=patient_id)
        .first()
    )


def _fmt_number(value: object) -> str:
    if value is None:
        return ""
    number = float(value)
    return f"{number:.1f}".rstrip("0").rstrip(".")


def _event_time(entry: LogEntry):
    return entry.logged_at or entry.created_at


def _window_logs(patient_id: int, days: int) -> list[LogEntry]:
    cutoff = timezone.now() - timedelta(days=days)
    return list(
        LogEntry.objects.filter(patient_id=patient_id)
        .filter(
            Q(logged_at__gte=cutoff)
            | Q(logged_at__isnull=True, created_at__gte=cutoff)
        )
        .order_by("-logged_at", "-created_at", "-id")
    )


def _reply_diabetes_type(patient_id: int) -> str:
    profile = _profile(patient_id)
    if profile is None or not profile.diabetes_type:
        return "Aucun type de diabète n’est enregistré dans ton profil."
    return f"Le type de diabète enregistré dans ton profil est : {profile.get_diabetes_type_display()}."


def _reply_treatment(patient_id: int) -> str:
    profile = _profile(patient_id)
    if profile is None or not profile.treatment_type:
        return "Aucun type de traitement n’est enregistré dans ton profil."
    return f"Le traitement enregistré dans ton profil est : {profile.get_treatment_type_display()}."


def _reply_targets(patient_id: int) -> str:
    profile = _profile(patient_id)
    if profile is None:
        return "Je ne trouve pas de profil diabète enregistré."
    low = profile.target_range_low
    high = profile.target_range_high
    provenance = profile.target_range_provenance
    if provenance == "clinician_confirmed":
        goal = (
            f" Objectif TIR confirmé : {_fmt_number(profile.target_time_in_range_goal_pct)} %."
            if profile.target_time_in_range_goal_pct is not None
            else ""
        )
        return (
            f"La plage glycémique configurée est {low}–{high} mg/dL, "
            f"avec provenance clinicien confirmée.{goal}"
        )
    return (
        f"La plage glycémique configurée est {low}–{high} mg/dL. "
        f"Sa provenance est « {provenance} » : je la décris comme un réglage enregistré, "
        "pas comme un objectif clinique confirmé."
    )


def _reply_meal_history(patient_id: int, message: str) -> str:
    target_date = timezone.localdate() - timedelta(days=1) if re.search(
        r"\b(?:hier|yesterday)\b", message, re.IGNORECASE
    ) else timezone.localdate()
    entries = [
        row
        for row in _window_logs(patient_id, 2)
        if timezone.localtime(_event_time(row)).date() == target_date
        and (row.meal_type or row.meal_description or row.meal_items)
    ]
    if not entries:
        return f"Je ne trouve aucun repas enregistré le {target_date.isoformat()}."
    chunks: list[str] = []
    for row in sorted(entries, key=_event_time)[:6]:
        at = timezone.localtime(_event_time(row)).strftime("%H:%M")
        detail = (row.meal_description or "").strip()
        if not detail and row.meal_items:
            detail = ", ".join(str(item) for item in row.meal_items[:4])
        if not detail:
            detail = row.get_meal_type_display() if row.meal_type else "repas sans détail"
        chunks.append(f"{at} — {detail}")
    return f"Repas enregistrés le {target_date.isoformat()} : " + " ; ".join(chunks) + "."


def _reply_exact_glucose(patient_id: int, message: str) -> str:
    hour_match = re.search(r"\b([01]?\d|2[0-3])\s*h\b", message, re.IGNORECASE)
    target_date = timezone.localdate() - timedelta(days=1) if re.search(
        r"\b(?:hier|yesterday)\b", message, re.IGNORECASE
    ) else timezone.localdate()
    if hour_match is None:
        return "Je peux relire une mesure précise si tu indiques une heure enregistrée, par exemple « hier à 20h »."
    hour = int(hour_match.group(1))
    candidates = [
        row
        for row in _window_logs(patient_id, 2)
        if timezone.localtime(_event_time(row)).date() == target_date
        and timezone.localtime(_event_time(row)).hour == hour
    ]
    if not candidates:
        return (
            f"Je ne trouve aucune glycémie enregistrée le {target_date.isoformat()} "
            f"entre {hour:02d}:00 et {hour:02d}:59."
        )
    row = min(
        candidates,
        key=lambda item: abs(timezone.localtime(_event_time(item)).minute),
    )
    at = timezone.localtime(_event_time(row)).strftime("%H:%M")
    return (
        f"Le {target_date.isoformat()} à {at}, la glycémie enregistrée est "
        f"{_fmt_number(row.blood_sugar)} mg/dL."
    )


def _reply_sleep(patient_id: int) -> str:
    rows = [row for row in _window_logs(patient_id, 7) if row.sleep_quality]
    if not rows:
        return "Je ne trouve aucune qualité de sommeil enregistrée sur les 7 derniers jours."
    good = sum(row.sleep_quality == "good" for row in rows)
    bad = sum(row.sleep_quality == "bad" for row in rows)
    return (
        f"Sur les 7 derniers jours, {len(rows)} entrées renseignent le sommeil : "
        f"{good} « bon » et {bad} « mauvais ». C’est un résumé descriptif du journal."
    )


def _reply_stress(patient_id: int) -> str:
    rows = [row for row in _window_logs(patient_id, 7) if row.stressed]
    if not rows:
        return "Je ne trouve aucune donnée de stress enregistrée sur les 7 derniers jours."
    yes = sum(row.stressed == "yes" for row in rows)
    no = sum(row.stressed == "no" for row in rows)
    return (
        f"Sur les 7 derniers jours, {len(rows)} entrées renseignent le stress : "
        f"{yes} « oui » et {no} « non ». C’est un résumé descriptif du journal."
    )


def _reply_latest_lab(patient_id: int) -> str:
    report = LabReport.objects.filter(patient_id=patient_id).order_by("-created_at").first()
    if report is None:
        return "Je ne trouve aucun rapport de laboratoire ou document médical confirmé."
    values: list[str] = []
    for label, value, unit in (
        ("HbA1c", report.hba1c_pct, "%"),
        ("glycémie à jeun", report.fasting_glucose_mgdl, "mg/dL"),
        ("cholestérol total", report.total_cholesterol_mgdl, "mg/dL"),
        ("HDL", report.hdl_mgdl, "mg/dL"),
        ("LDL", report.ldl_mgdl, "mg/dL"),
        ("triglycérides", report.triglycerides_mgdl, "mg/dL"),
        ("créatinine", report.creatinine_umol, "µmol/L"),
    ):
        if value is not None:
            values.append(f"{label} {_fmt_number(value)} {unit}")
    date_label = report.report_date.isoformat() if report.report_date else report.created_at.date().isoformat()
    suffix = " ; ".join(values) if values else "aucune valeur structurée persistée"
    return (
        f"Dernier document confirmé : {report.get_document_type_display()}, date {date_label}. "
        f"Données structurées : {suffix}."
    )


def _reply_imported_medications(patient_id: int) -> str:
    has_reports = LabReport.objects.filter(patient_id=patient_id).exists()
    prefix = (
        "Des documents confirmés existent. "
        if has_reports
        else "Je ne trouve aucun document confirmé. "
    )
    return (
        prefix
        + "Les médicaments extraits sont actuellement disponibles dans la prévisualisation "
        "du document avant confirmation, mais ils ne sont pas persistés comme liste structurée "
        "dans LabReport. Je ne peux donc pas relire une liste historique fiable sans inventer."
    )


def _reply_latest_cgm(patient_id: int) -> str:
    row = (
        CGMReadingRecord.objects.filter(patient_id=patient_id)
        .order_by("-recorded_at", "-id")
        .first()
    )
    if row is None:
        return "Je ne trouve aucune lecture CGM enregistrée."
    at = timezone.localtime(row.recorded_at).strftime("%Y-%m-%d %H:%M")
    trend = f", tendance « {row.trend} »" if row.trend else ""
    return (
        f"Dernière lecture CGM enregistrée : {row.glucose_mg_dl} mg/dL "
        f"le {at}, source {row.source}{trend}."
    )


def _reply_proactive(patient_id: int) -> str:
    preview = preview_proactive_insights(patient_id=patient_id)
    if preview.item is None:
        return (
            f"Insights proactifs : statut « {preview.status} », "
            f"{preview.pending_count} observation(s) en attente."
        )
    item = preview.item
    return (
        f"Insights proactifs : {preview.pending_count} observation(s) en attente. "
        f"Prochaine observation gouvernée : {item.observation_key}, état « {item.state} », "
        f"{item.observations} observation(s) sur {item.distinct_days} jour(s). "
        f"Étape autorisée : {item.allowed_next_step}."
    )


def _reply_paired_meals(patient_id: int) -> str:
    result = compute_paired_meal_response(patient_id=patient_id, window_days=90)
    if not result.pairs:
        return (
            "Je ne trouve aucun épisode repas pré/post complet relié par le même "
            "meal_episode_id sur les 90 derniers jours."
        )
    pair = result.pairs[-1]
    return (
        f"Sur 90 jours : {result.complete_pair_count} paire(s) pré/post complète(s). "
        f"Exemple enregistré : {pair.meal_type}, {_fmt_number(pair.pre_glucose_mg_dl)} → "
        f"{_fmt_number(pair.post_glucose_mg_dl)} mg/dL en {_fmt_number(pair.elapsed_minutes)} min "
        f"(delta descriptif {_fmt_number(pair.delta_mg_dl)} mg/dL, sans causalité déduite)."
    )


def resolve_whole_app_context(
    patient_id: int,
    message: str,
    *,
    language: str = "fr",
) -> AdviceResolution | None:
    intent = classify_whole_app_context(message)
    if intent is None:
        return None

    reply_by_intent = {
        WholeAppIntent.DIABETES_TYPE: lambda: _reply_diabetes_type(patient_id),
        WholeAppIntent.TREATMENT: lambda: _reply_treatment(patient_id),
        WholeAppIntent.TARGETS: lambda: _reply_targets(patient_id),
        WholeAppIntent.MEAL_HISTORY: lambda: _reply_meal_history(patient_id, message),
        WholeAppIntent.EXACT_GLUCOSE: lambda: _reply_exact_glucose(patient_id, message),
        WholeAppIntent.SLEEP_HISTORY: lambda: _reply_sleep(patient_id),
        WholeAppIntent.STRESS_HISTORY: lambda: _reply_stress(patient_id),
        WholeAppIntent.LATEST_LAB: lambda: _reply_latest_lab(patient_id),
        WholeAppIntent.IMPORTED_MEDICATIONS: lambda: _reply_imported_medications(patient_id),
        WholeAppIntent.LATEST_CGM: lambda: _reply_latest_cgm(patient_id),
        WholeAppIntent.PROACTIVE_PENDING: lambda: _reply_proactive(patient_id),
        WholeAppIntent.PAIRED_MEALS: lambda: _reply_paired_meals(patient_id),
    }
    return AdviceResolution(
        decision=_decision(intent, language),
        reply=reply_by_intent[intent](),
    )


__all__ = [
    "WholeAppIntent",
    "classify_whole_app_context",
    "resolve_whole_app_context",
]
