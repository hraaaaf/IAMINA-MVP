"""Registered diabetes alert authority.

Adds the minimum patient-scoped history required by the deterministic alert
state machine while preserving the evidence-gated analysis authority.
"""
from __future__ import annotations

import logging

from django.db.models.functions import Coalesce

from core.contracts.alert import DomainAlert
from diabetes.models import LogEntry

from .alerts import AlertLevel, evaluate
from .evidence_engine import EvidenceGuardedDiabetesEngine

logger = logging.getLogger(__name__)


class EvidenceGuardedAlertingDiabetesEngine(EvidenceGuardedDiabetesEngine):
    """Evidence-gated public engine with reachable deterministic alert branches."""

    @staticmethod
    def _recent_glucose_values(entry) -> list[float]:
        patient_id = getattr(entry, "patient_id", None)
        effective_time = getattr(entry, "effective_time", None)
        if patient_id is None or effective_time is None:
            return []

        try:
            queryset = (
                LogEntry.objects.filter(patient_id=patient_id)
                .annotate(_effective_time=Coalesce("logged_at", "created_at"))
                .filter(_effective_time__lt=effective_time)
            )
            entry_pk = getattr(entry, "pk", None)
            if entry_pk is not None:
                queryset = queryset.exclude(pk=entry_pk)
            values = queryset.order_by("-_effective_time", "-pk").values_list(
                "blood_sugar",
                flat=True,
            )[:2]
            return [float(value) for value in values]
        except Exception:
            logger.exception(
                "Alerting authority history query failed; evaluating current reading only."
            )
            return []

    def evaluate_alert(self, entry, language: str = "fr") -> DomainAlert | None:
        glucose = getattr(entry, "blood_sugar", None)
        if glucose is None:
            return None
        glucose = float(glucose)

        response = evaluate(
            glucose,
            recent_readings=self._recent_glucose_values(entry),
        )
        if response.level == AlertLevel.NONE:
            return None

        blocking = response.level in (AlertLevel.EMERGENCY, AlertLevel.CRITICAL)
        message = (
            response.message_darija
            if language in ("ar-MA", "ar")
            else response.message_fr
        )
        return DomainAlert(
            severity=response.level.value,
            blocking=blocking,
            message=message,
            event_type="emergency" if blocking else "alert",
            event_description="Deterministic glucose safety alert.",
            value=glucose,
        )
