"""Evidence-gated diabetes engine exposed to the shared ModuleRegistry.

The legacy analytical layer is intentionally left intact as a descriptive data
calculator. This wrapper owns the public authority boundary: invalid CGM
sufficiency cannot leak into patterns, tone selection, trend labels or LLM
context merely because many stored rows have ``source='cgm'``.
"""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from core.contracts.domain_context import DomainContext
from diabetes.models import LogEntry
from diabetes.services.clinical.engine import DiabetesEngine, run_clinical_analysis
from diabetes.services.clinical.evidence_projection import (
    guard_normative_kpis,
    project_public_kpis,
)
from diabetes.services.clinical.evidence_registry import evidence_for_pattern
from diabetes.services.clinical.semantic_compressor import build_chat_context
from diabetes.services.clinical.sql_analytics import compute_kpis, compute_trend


class EvidenceGuardedDiabetesEngine(DiabetesEngine):
    """Diabetes engine whose patient/AI surface is constrained by evidence eligibility."""

    def analyze(
        self,
        patient_id: int,
        language: str = "fr",
        days: int = 14,
    ) -> DomainContext:
        raw_kpis = compute_kpis(patient_id=patient_id, days=days)
        if not raw_kpis.has_sufficient_data:
            return DomainContext.empty(language=language)

        public_kpis = project_public_kpis(raw_kpis)
        guarded_kpis = guard_normative_kpis(raw_kpis)
        sufficiency = public_kpis["cgm_sufficiency"]
        cgm_verified = bool(
            isinstance(sufficiency, dict) and sufficiency.get("verified") is True
        )

        since = timezone.now() - timedelta(days=days)
        entries = list(
            LogEntry.objects.filter(
                Q(logged_at__gte=since)
                | Q(logged_at__isnull=True, created_at__gte=since),
                patient_id=patient_id,
                blood_sugar__isnull=False,
            ).order_by("logged_at", "created_at")
        )

        # Normative-pattern detectors see only evidence-eligible KPI fields. Entry
        # detectors remain available for explicitly descriptive observations.
        report = run_clinical_analysis(entries, guarded_kpis, language=language)

        # The compressor receives raw descriptive values but performs the same
        # centralized CGM sufficiency assessment before emitting normative wording.
        pivot = build_chat_context(raw_kpis, report.patterns)

        # Existing compute_trend names its row-fraction metric "TIR". Until true
        # CGM coverage is verified, do not expose that object as a clinical trend.
        trend = compute_trend(patient_id=patient_id) if cgm_verified else {}

        pattern_details: list[dict[str, object]] = []
        for pattern in report.patterns:
            evidence = evidence_for_pattern(pattern.code)
            pattern_details.append(
                {
                    "code": pattern.code,
                    "priority": pattern.priority,
                    "evidence": pattern.evidence,
                    "evidence_count": pattern.evidence_count,
                    "distinct_days": pattern.distinct_days,
                    "source_version": pattern.source_version,
                    "limitations": pattern.limitations,
                    "evidence_id": evidence.evidence_id,
                    "evidence_metadata": evidence.to_metadata(),
                }
            )

        return DomainContext(
            kpi_summary=public_kpis,
            detected_patterns=[p.code for p in report.patterns[:5]],
            insights=report.insights,
            pivot_text=pivot,
            language=language,
            has_sufficient_data=True,
            tone_signals={
                "primary": public_kpis["tir_pct"],
                "stability": public_kpis["cv_pct"],
            },
            trend=trend,
            primary_label="TIR" if cgm_verified else "Recorded glucose",
            patterns_detail=pattern_details,
        )