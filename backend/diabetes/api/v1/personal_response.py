"""Patient-scoped deterministic personal-response endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.observation_memory import refresh_personal_response_memory
from diabetes.services.clinical.paired_meal_response import compute_paired_meal_response
from diabetes.services.clinical.personal_response import compute_personal_response

router = Router(tags=["personal-response"])


class PersonalResponsePatternOut(BaseModel):
    key: str
    kind: Literal["context", "meal"]
    observations: int
    distinct_days: int
    median_glucose_mg_dl: float
    window_median_glucose_mg_dl: float
    confidence: Literal["limited", "moderate", "strong"]


class PersonalResponseOut(BaseModel):
    status: Literal["ready", "insufficient_data"]
    data_scope: Literal["server_synced_logs"]
    window_days: int
    total_readings: int
    distinct_days: int
    window_median_glucose_mg_dl: float | None
    minimum_observations: int
    minimum_distinct_days: int
    confidence_definition: str
    causality_notice: str
    patterns: list[PersonalResponsePatternOut]


class PairedMealEpisodeOut(BaseModel):
    episode_id: UUID
    meal_type: str
    pre_at: datetime
    post_at: datetime
    pre_glucose_mg_dl: float
    post_glucose_mg_dl: float
    delta_mg_dl: float
    elapsed_minutes: float


class PairedMealPatternOut(BaseModel):
    meal_type: str
    pairs: int
    distinct_days: int
    median_pre_glucose_mg_dl: float
    median_post_glucose_mg_dl: float
    median_delta_mg_dl: float
    evidence_density: Literal["limited", "moderate", "strong"]
    evidence_id: str


class PairedMealResponseOut(BaseModel):
    status: Literal["ready", "insufficient_data"]
    data_scope: Literal["server_synced_logs_explicit_meal_episodes"]
    window_days: int
    explicit_episode_count: int
    complete_pair_count: int
    incomplete_or_invalid_episode_count: int
    pairing_definition: str
    interpretation_notice: str
    evidence_id: str
    limitations: list[str]
    pairs: list[PairedMealEpisodeOut]
    patterns: list[PairedMealPatternOut]


@router.get("/personal-response/", response=PersonalResponseOut)
def get_personal_response(request, days: int = 90):
    """Summarize repeated observations without causal or prescriptive inference."""
    result = compute_personal_response(
        patient_id=request.user.id,
        window_days=days,
    )
    refresh_personal_response_memory(patient_id=request.user.id)
    return {
        "status": result.status,
        "data_scope": "server_synced_logs",
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
            "cause and does not authorize a clinical action."
        ),
        "patterns": [
            {
                "key": item.key,
                "kind": item.kind,
                "observations": item.observations,
                "distinct_days": item.distinct_days,
                "median_glucose_mg_dl": item.median_glucose_mg_dl,
                "window_median_glucose_mg_dl": item.window_median_glucose_mg_dl,
                "confidence": item.confidence,
            }
            for item in result.patterns
        ],
    }


@router.get("/personal-response/paired-meals/", response=PairedMealResponseOut)
def get_paired_meal_response(request, days: int = 90):
    """Return exact linked pre→post meal episodes and repeated patterns."""
    result = compute_paired_meal_response(
        patient_id=request.user.id,
        window_days=days,
    )
    return {
        "status": result.status,
        "data_scope": "server_synced_logs_explicit_meal_episodes",
        "window_days": result.window_days,
        "explicit_episode_count": result.explicit_episode_count,
        "complete_pair_count": result.complete_pair_count,
        "incomplete_or_invalid_episode_count": result.incomplete_or_invalid_episode_count,
        "pairing_definition": (
            "A pair exists only when one pre_meal and one later post_meal reading "
            "share the exact same explicit meal_episode_id and meal_type. No pair "
            "is inferred from clock-time proximity."
        ),
        "interpretation_notice": (
            "The pre-to-post delta is descriptive journal evidence only. It does "
            "not establish cause, outcome, or a clinical action."
        ),
        "evidence_id": result.evidence_id,
        "limitations": list(result.limitations),
        "pairs": list(result.pairs),
        "patterns": list(result.patterns),
    }
