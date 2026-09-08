from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator, model_validator

from diabetes.contracts import log_entry as log_input

# ── Shared constraint ─────────────────────────────────────────────────────────
# Canonical persisted glucose range. UnitGuard uses the same contract before
# Pydantic receives the normalized mg/dL value.
_BloodSugar = Annotated[
    float,
    Field(ge=log_input.GLUCOSE_MIN_MG_DL, le=log_input.GLUCOSE_MAX_MG_DL),
]
_InsulinUnits = Annotated[float, Field(ge=0.0)]
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
    ramadan_start_date: Optional[date] = None
    ramadan_end_date: Optional[date] = None


class _CanonicalLogInputMixin:
    @field_validator("logged_at", check_fields=False)
    @classmethod
    def validate_canonical_logged_at(cls, value: datetime | None):
        return log_input.validate_logged_at(value)

    @staticmethod
    def _validate_choice(value: str | None, allowed: tuple[str, ...], field_name: str):
        if value is not None and value not in allowed:
            raise ValueError(f"Unsupported {field_name} value.")
        return value

    @field_validator("glycemic_context", check_fields=False)
    @classmethod
    def validate_glycemic_context(cls, value: str | None):
        return cls._validate_choice(
            value,
            log_input.GLYCEMIC_CONTEXT_VALUES,
            "glycemic_context",
        )

    @field_validator("meal_type", check_fields=False)
    @classmethod
    def validate_meal_type(cls, value: str | None):
        return cls._validate_choice(value, log_input.MEAL_TYPE_VALUES, "meal_type")

    @field_validator("exercised", check_fields=False)
    @classmethod
    def validate_exercised(cls, value: str | None):
        return cls._validate_choice(value, log_input.EXERCISE_VALUES, "exercised")

    @field_validator("sleep_quality", check_fields=False)
    @classmethod
    def validate_sleep_quality(cls, value: str | None):
        return cls._validate_choice(value, log_input.SLEEP_VALUES, "sleep_quality")

    @field_validator("stressed", check_fields=False)
    @classmethod
    def validate_stressed(cls, value: str | None):
        return cls._validate_choice(value, log_input.STRESS_VALUES, "stressed")

    @field_validator("fatigue_level", check_fields=False)
    @classmethod
    def validate_fatigue_level(cls, value: str | None):
        return cls._validate_choice(value, log_input.FATIGUE_VALUES, "fatigue_level")

    @field_validator("is_sick", check_fields=False)
    @classmethod
    def validate_is_sick(cls, value: str | None):
        return cls._validate_choice(value, log_input.SICK_VALUES, "is_sick")

    @field_validator("source", check_fields=False)
    @classmethod
    def validate_source(cls, value: str | None):
        return cls._validate_choice(value, log_input.SOURCE_VALUES, "source")


class LogEntrySchema(_CanonicalLogInputMixin, Schema):
    id: int
    logged_at: Optional[datetime]
    glycemic_context: str = ""
    meal_type: str
    meal_episode_id: Optional[UUID] = None
    blood_sugar: float
    meal_description: str = ""
    meal_items: List[str] = Field(default_factory=list)
    meal_portions: List[MealPortionSchema] = Field(default_factory=list)
    insulin_units: Optional[float] = None
    exercised: str = ""
    sleep_quality: str = ""
    stressed: str = ""
    fatigue_level: str = ""
    is_sick: str = ""
    source: str = "manual"
    client_uuid: Optional[UUID] = None
    created_at: datetime


class LogEntryCreateSchema(_CanonicalLogInputMixin, Schema):
    logged_at: Optional[datetime] = None
    glycemic_context: str = ""
    meal_type: str = ""
    meal_episode_id: Optional[UUID] = None
    blood_sugar: _BloodSugar
    meal_description: str = ""
    meal_items: List[_MealItem] = Field(default_factory=list, max_length=20)
    meal_portions: List[MealPortionSchema] = Field(default_factory=list, max_length=20)
    insulin_units: Optional[_InsulinUnits] = None
    exercised: str = ""
    sleep_quality: str = ""
    stressed: str = ""
    fatigue_level: str = ""
    is_sick: str = ""
    source: str = "manual"
    client_uuid: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_portion_links(self):
        validate_meal_portion_links(self.meal_items, self.meal_portions)
        return self

    @model_validator(mode="after")
    def validate_meal_episode_link(self):
        log_input.validate_meal_episode_link(
            self.meal_episode_id,
            glycemic_context=self.glycemic_context,
            meal_type=self.meal_type,
        )
        return self


class LogEntryUpdateSchema(_CanonicalLogInputMixin, Schema):
    """Partial update — all fields optional. Only supplied fields are written."""

    logged_at: Optional[datetime] = None
    glycemic_context: Optional[str] = None
    meal_type: Optional[str] = None
    meal_episode_id: Optional[UUID] = None
    blood_sugar: Optional[_BloodSugar] = None
    meal_description: Optional[str] = None
    meal_items: Optional[List[_MealItem]] = Field(default=None, max_length=20)
    meal_portions: Optional[List[MealPortionSchema]] = Field(default=None, max_length=20)
    insulin_units: Optional[_InsulinUnits] = None
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
