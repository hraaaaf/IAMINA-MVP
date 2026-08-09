from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field

# ── Shared constraint ─────────────────────────────────────────────────────────
# Physiological range accepted at the API boundary (30–600 mg/dL).
# Values outside this range are clinically implausible at the sensor/manual level.
_BloodSugar = Annotated[float, Field(ge=30.0, le=600.0)]
_MealItem = Annotated[str, Field(min_length=1, max_length=80)]


class PatientProfileSchema(Schema):
    diabetes_type: Optional[str] = None
    treatment_type: Optional[str] = None
    clinical_profile_complete: bool = False
    target_range_low: float
    target_range_high: float
    unit_preference: str
    preferred_language: str = "ar-MA"
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class LogEntrySchema(Schema):
    id: int
    logged_at: Optional[datetime]
    glycemic_context: str = ""
    meal_type: str
    blood_sugar: float
    meal_description: str = ""
    meal_items: List[str] = Field(default_factory=list)
    insulin_units: Optional[float] = None
    exercised: str = "no"
    sleep_quality: str = "good"
    stressed: str = "no"
    fatigue_level: str = "ok"
    is_sick: str = "no"
    source: str = "manual"
    client_uuid: Optional[UUID] = None
    created_at: datetime


class LogEntryCreateSchema(Schema):
    logged_at: Optional[datetime] = None
    glycemic_context: str = ""
    meal_type: str = ""
    blood_sugar: _BloodSugar
    meal_description: str = ""
    meal_items: List[_MealItem] = Field(default_factory=list, max_length=20)
    insulin_units: Optional[float] = None
    exercised: str = "no"
    sleep_quality: str = "good"
    stressed: str = "no"
    fatigue_level: str = "ok"
    is_sick: str = "no"
    source: str = "manual"
    client_uuid: Optional[UUID] = None


class LogEntryUpdateSchema(Schema):
    """Partial update — all fields optional. Only supplied fields are written."""

    logged_at: Optional[datetime] = None
    glycemic_context: Optional[str] = None
    meal_type: Optional[str] = None
    blood_sugar: Optional[_BloodSugar] = None
    meal_description: Optional[str] = None
    meal_items: Optional[List[_MealItem]] = Field(default=None, max_length=20)
    insulin_units: Optional[float] = None
    exercised: Optional[str] = None
    sleep_quality: Optional[str] = None
    stressed: Optional[str] = None
    fatigue_level: Optional[str] = None
    is_sick: Optional[str] = None


class PaginatedLogsResponse(Schema):
    """Paginated wrapper for GET /logs. Use ?page=N&page_size=M (defaults: 1, 50)."""

    total: int
    page: int
    page_size: int
    items: List["LogEntrySchema"]


class BatchSyncResponse(Schema):
    synced_ids: List[UUID]
    errors: List[str] = []


class Error(Schema):
    message: str
