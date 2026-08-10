"""Patient-scoped deterministic personal-response endpoint."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.personal_response import compute_personal_response

router = Router(tags=["personal-response"])


class PersonalResponsePatternOut(BaseModel):
    key: str
    kind: Literal["context", "meal"]
    observations: int
    distinct_days: int
    median_glucose_mg_dl: float
    window_median_glucose_mg_dl: float
    first_observed_at: datetime
    last_observed_at: datetime
    confidence: Literal["limited", "moderate", "strong"]


class PersonalResponseOut(BaseModel):
    status: Literal["ready", "insufficient_data"]
    window_days: int
    total_readings: int
    distinct_days: int
    window_median_glucose_mg_dl: float | None
    minimum_observations: int
    minimum_distinct_days: int
    confidence_definition: str
    causality_notice: str
    patterns: list[PersonalResponsePatternOut]


@router.get("/personal-response/", response=PersonalResponseOut)
def get_personal_response(request, days: int = 90):
    """Summarize repeated observations without causal or treatment inference."""
    result = compute_personal_response(
        patient_id=request.user.id,
        window_days=days,
    )
    return {
        "status": result.status,
        "window_days": result.window_days,
        "total_readings": result.total_readings,
        "distinct_days": result.distinct_days,
        "window_median_glucose_mg_dl": result.window_median_glucose_mg_dl,
        "minimum_observations": result.minimum_observations,
        "minimum_distinct_days": result.minimum_distinct_days,
        "confidence_definition": (
            "Product evidence grade based only on repeated observations and "
            "distinct days; it is not a probability, statistical significance "
            "test, diagnosis, or clinical confidence score."
        ),
        "causality_notice": (
            "Observed association in this journal only. It does not establish "
            "cause and must not be used as treatment or dosing advice."
        ),
        "patterns": [
            {
                "key": item.key,
                "kind": item.kind,
                "observations": item.observations,
                "distinct_days": item.distinct_days,
                "median_glucose_mg_dl": item.median_glucose_mg_dl,
                "window_median_glucose_mg_dl": item.window_median_glucose_mg_dl,
                "first_observed_at": item.first_observed_at,
                "last_observed_at": item.last_observed_at,
                "confidence": item.confidence,
            }
            for item in result.patterns
        ],
    }
