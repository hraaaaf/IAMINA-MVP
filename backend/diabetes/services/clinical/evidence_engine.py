"""Evidence-gated diabetes engine exposed to the shared ModuleRegistry.

The legacy analytical layer is intentionally left intact as a descriptive data
calculator. This wrapper owns the public authority boundary: invalid CGM
sufficiency cannot leak into patterns, tone selection, trend labels or LLM
context merely because many stored rows have ``source='cgm'``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from core.contracts.companion_context import (
    CompanionAfterVisit,
    CompanionChange,
    CompanionContext,
    CompanionPattern,
)
from core.contracts.domain_context import DomainContext
from diabetes.models import LogEntry
from diabetes.services.clinical.analysis_integrity import (
    run_clinical_analysis_with_integrity,
)
from diabetes.services.clinical.cgm_analytics import compute_verified_cgm_metrics
from diabetes.services.clinical.cgm_eligibility import assess_cgm_window
from diabetes.services.clinical.companion_overview import build_companion_overview
from diabetes.services.clinical.engine import DiabetesEngine
from diabetes.services.clinical.evidence_projection import (
    guard_normative_kpis,
    project_public_kpis,
)
from diabetes.services.clinical.evidence_registry import evidence_for_pattern
from diabetes.services.clinical.semantic_compressor import build_chat_context
from diabetes.services.clinical.sql_analytics import compute_kpis

logger = logging.getLogger(__name__)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class EvidenceGuardedDiabetesEngine(DiabetesEngine):
    """Diabetes engine whose patient/AI surface is constrained by evidence eligibility."""

    def analyze(
        self,
        patient_id: int,
        language: str = "fr",
        days: int = 14,
    ) -> DomainContext:
        window_end = timezone.now()
        window_start = window_end - timedelta(days=days)
        try:
            raw_kpis = compute_kpis(patient_id=patient_id, days=days)
        except Exception:
            logger.exception("EvidenceGuardedDiabetesEngine: KPI computation failed")
            return DomainContext.unavailable(
                language=language,
                degradation_codes=["kpi_compute_failed"],
            )

        if not raw_kpis.has_sufficient_data:
            return DomainContext.empty(language=language)

        try:
            cgm_window = assess_cgm_window(
                patient_id=patient_id,
                window_start=window_start,
                window_end=window_end,
            )
            cgm_metrics = None
            if cgm_window.verified:
                cgm_metrics = compute_verified_cgm_metrics(
                    patient_id=patient_id,
                    window_start=window_start,
                    window_end=window_end,
                )

            public_kpis = project_public_kpis(
                raw_kpis,
                cgm_window=cgm_window,
                cgm_metrics=cgm_metrics,
            )
            guarded_kpis = guard_normative_kpis(
                raw_kpis,
                cgm_window=cgm_window,
                cgm_metrics=cgm_metrics,
            )
            sufficiency = public_kpis["cgm_sufficiency"]
            cgm_verified = bool(
                isinstance(sufficiency, dict) and sufficiency.get("verified") is True
            )

            entries = list(
                LogEntry.objects.filter(
                    Q(logged_at__gte=window_start)
                    | Q(logged_at__isnull=True, created_at__gte=window_start),
                    patient_id=patient_id,
                    blood_sugar__isnull=False,
                ).order_by("logged_at", "created_at")
            )

            # Normative-pattern detectors see only evidence-eligible KPI fields. Entry
            # detectors remain available for explicitly descriptive observations.
            report, degradations = run_clinical_analysis_with_integrity(
                entries,
                guarded_kpis,
                language=language,
            )

            # The existing semantic compressor still evaluates legacy row-provenance
            # sufficiency and therefore remains conservative until a dedicated CGM-native
            # compressor contract is promoted.
            pivot = build_chat_context(raw_kpis, report.patterns)

            # Existing compute_trend is LogEntry-based. A valid CGM window must not
            # magically turn a mixed/manual trend into a CGM trend, so keep it closed
            # until a CGM-native trend implementation is separately governed.
            trend: dict[str, object] = {}

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
        except Exception:
            # Fail closed rather than letting a projection/query/compression failure look
            # like a clinically uneventful analysis. Exception details stay in server logs;
            # the public contract exposes only a stable PHI-free technical code.
            logger.exception("EvidenceGuardedDiabetesEngine: analysis pipeline failed")
            return DomainContext.unavailable(
                language=language,
                degradation_codes=["analysis_pipeline_failed"],
            )

        return DomainContext(
            kpi_summary=public_kpis,
            detected_patterns=[p.code for p in report.patterns[:5]],
            insights=report.insights,
            pivot_text=pivot,
            language=language,
            has_sufficient_data=True,
            # ANALYSIS-5 may expose certified CGM numbers, but target/population
            # applicability belongs to ANALYSIS-6. Keep tone selection neutral so a
            # promoted TIR/CV value cannot trigger "within/outside target" wording yet.
            tone_signals={
                "primary": None,
                "stability": None,
            },
            trend=trend,
            primary_label="TIR" if cgm_verified else "Recorded glucose",
            patterns_detail=pattern_details,
            analysis_status="partial" if degradations else "complete",
            analysis_degradations=degradations,
        )

    def companion_context(
        self,
        patient_id: int,
        language: str = "fr",
    ) -> CompanionContext:
        """Adapt the certified diabetes overview to the chassis contract."""
        overview = build_companion_overview(patient_id=patient_id)
        return CompanionContext(
            pattern_status=overview.pattern_status,
            review_status=overview.review_status,
            review_anchor_captured_at=_iso(overview.review_anchor_captured_at),
            patterns=tuple(
                CompanionPattern(
                    observation_key=item.observation_key,
                    current_state=item.current_state,
                    markers=tuple(item.markers),
                    evidence_density=item.evidence_density,
                    recurrence_count=item.recurrence_count,
                    baseline_direction=item.baseline_direction,
                    baseline_movement=item.baseline_movement,
                    first_observed_at=_iso(item.first_observed_at),
                    last_observed_at=_iso(item.last_observed_at),
                    evidence_id=item.evidence_id,
                    source_version=item.source_version,
                    limitations=tuple(item.limitations),
                )
                for item in overview.patterns
            ),
            changes_since_review=tuple(
                CompanionChange(
                    observation_key=item.observation_key,
                    change_kind=item.change_kind,
                    evidence_strength=item.evidence_strength,
                    missing_data=tuple(item.missing_data),
                    source_version=item.source_version,
                )
                for item in overview.changes_since_review
            ),
            after_visit=CompanionAfterVisit(
                status=overview.after_visit.status,
                anchor_id=overview.after_visit.anchor_id,
                occurred_at=_iso(overview.after_visit.occurred_at),
                source=overview.after_visit.source,
                fact_count=overview.after_visit.fact_count,
                latest_fact_at=_iso(overview.after_visit.latest_fact_at),
            ),
            safety_notice=overview.safety_notice,
            source_version=overview.source_version,
            language=language,
        )

    def offline_fallback(
        self,
        context: DomainContext,
        language: str = "fr",
    ) -> str:
        """Keep diabetes/TIR degraded wording inside the diabetes capsule."""
        is_ar = language in ("ar", "ar-MA")
        is_darija = language == "ar-MA"

        if context.analysis_status == "unavailable":
            if is_darija:
                return "التحليل ما متوفرش دابا. عاود جرّب من بعد شوية."
            if is_ar:
                return "التحليل غير متاح حالياً. حاول مجدداً بعد قليل."
            if language == "en":
                return "Analysis is temporarily unavailable. Please try again shortly."
            return "L’analyse est temporairement indisponible. Réessaie dans un instant."

        if not context.has_sufficient_data:
            if is_darija:
                return "ما عنديش داتا كافية دابا. كمّل تسجّل المقياسات ديالك !"
            if is_ar:
                return "لا تتوفر لديّ بيانات كافية حتى الآن. واصل تسجيل قياساتك !"
            if language == "en":
                return "Not enough data yet. Keep recording your measurements."
            return "Pas encore assez de données. Continue à enregistrer tes mesures !"

        tir = context.tone_signals.get("primary")
        if tir is None:
            return super().offline_fallback(context, language=language)

        if tir >= 70:
            if is_darija:
                return f"السكّر ديالك في الميزان — {tir:.0f}%! زوينة بزاف، كمّل هكاك."
            if is_ar:
                return f"نسبة وقتك في النطاق المستهدف {tir:.0f}% — ممتاز ! واصل هكذا."
            if language == "en":
                return f"Your TIR is {tir:.0f}% — within target. Keep it up."
            return f"Ton TIR est à {tir:.0f} % — tu es dans la cible ! Continue comme ça."
        if tir < 40:
            if is_darija:
                return f"TIR ديالك {tir:.0f}% دابا — هضر مع طبيبك باش تراجع الوضع."
            if is_ar:
                return f"نسبتك في النطاق المستهدف {tir:.0f}% — تحدث مع طبيبك لمراجعة الوضع."
            if language == "en":
                return f"Your TIR is {tir:.0f}% — discuss the situation with your clinician."
            return f"Ton TIR est à {tir:.0f} % — parle de la situation avec ton médecin."
        if is_darija:
            return f"TIR ديالك {tir:.0f}% — عاود جرّب من بعد شوية."
        if is_ar:
            return f"نسبتك في النطاق المستهدف {tir:.0f}% — حاول مجدداً بعد قليل."
        if language == "en":
            return f"Your TIR is {tir:.0f}% — please try again shortly."
        return f"Ton TIR est à {tir:.0f} % — réessaie dans un instant."
