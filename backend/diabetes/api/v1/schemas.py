from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, model_validator

# ── Shared constraint ─────────────────────────────────────────────────────────
# Physiological range accepted at the API boundary (30–600 mg/dL).
# Values outside this range are clinically implausible at the sensor/manual level.
_BloodSugar = Annotated[float, Field(ge=30.0, le=600.0)]
_MealItem = Annotated[str, Field(min_length=1, max_length=80)]


class MealPortionSchema(Schema):
    """Patient-confirmed portion input; never a server-authored nutrition claim."""

    food_id: Annotated[str, Field(min_length=1, max_length=80)]
    portion_id: Optional[Annotated[str, Field(min_length=1, max_length=80)]] = None
    grams: Optional[Annotated[float, Field(gt=0.0, le=3000.0)]] = None

    @model_validator(mode="after")
    def require_one_quantity_representation(self):
        if self.portion_id is None and self.grams is None:
            raise ValueError("portion_id or grams is required")
        return self


def validate_meal_portion_links(
    meal_items: List[str],
    meal_portions: List[MealPortionSchema],
) -> None:
    """Keep confirmed portion rows one-to-one with selected structured foods."""

    selected = set(meal_items)
    seen: set[str] = set()
    for portion in meal_portions:
        if portion.food_id not in selected:
            raise ValueError("meal portion food_id must exist in meal_items")
        if portion.food_id in seen:
            raise ValueError("only one meal portion is allowed per food_id")
        seen.add(portion.food_id)


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
    meal_portions: List[MealPortionSchema] = Field(default_factory=list)
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
    meal_portions: List[MealPortionSchema] = Field(default_factory=list, max_length=20)
    insulin_units: Optional[float] = None
    exercised: str = "no"
    sleep_quality: str = "good"
    stressed: str = "no"
    fatigue_level: str = "ok"
    is_sick: str = "no"
    source: str = "manual"
    client_uuid: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_portion_links(self):
        validate_meal_portion_links(self.meal_items, self.meal_portions)
        return self


class LogEntryUpdateSchema(Schema):
    """Partial update — all fields optional. Only supplied fields are written."""

    logged_at: Optional[datetime] = None
    glycemic_context: Optional[str] = None
    meal_type: Optional[str] = None
    blood_sugar: Optional[_BloodSugar] = None
    meal_description: Optional[str] = None
    meal_items: Optional[List[_MealItem]] = Field(default=None, max_length=20)
    meal_portions: Optional[List[MealPortionSchema]] = Field(default=None, max_length=20)
    insulin_units: Optional[float] = None
    exercised: Optional[str] = None
    sleep_quality: Optional[str] = None
    stressed: Optional[str] = None
    fatigue_level: Optional[str] = None
    is_sick: Optional[str] = None

    @model_validator(mode="after")
    def validate_portion_links_when_complete(self):
        if self.meal_items is not None and self.meal_portions is not None:
            validate_meal_portion_links(self.meal_items, self.meal_portions)
        return self


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
