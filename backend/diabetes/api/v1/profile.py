"""
Patient profile under /api/v1/profile.
GET   /api/v1/profile  — read current profile
PATCH /api/v1/profile  — partial update (language, units, targets, weight/height)
"""

from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, field_validator

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile

from .schemas import PatientProfileSchema

router = Router(tags=["profile"])

_VALID_LANGUAGES = {"fr", "ar-MA", "ar"}
_VALID_UNITS     = {"mg_dl", "mmol_l"}


class ProfilePatchSchema(BaseModel):
    """All fields optional — only provided fields are updated."""
    preferred_language: Optional[str]   = None
    unit_preference:    Optional[str]   = None
    target_range_low:   Optional[float] = None
    target_range_high:  Optional[float] = None
    weight:             Optional[float] = None
    height:             Optional[int]   = None

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in _VALID_LANGUAGES:
            raise ValueError(f"preferred_language must be one of {_VALID_LANGUAGES}")
        return v

    @field_validator("unit_preference")
    @classmethod
    def validate_unit(cls, v):
        if v is not None and v not in _VALID_UNITS:
            raise ValueError(f"unit_preference must be one of {_VALID_UNITS}")
        return v

    @field_validator("target_range_low")
    @classmethod
    def validate_low(cls, v):
        if v is not None and not (40.0 <= v <= 200.0):
            raise ValueError("target_range_low must be between 40 and 200 mg/dL")
        return v

    @field_validator("target_range_high")
    @classmethod
    def validate_high(cls, v):
        if v is not None and not (100.0 <= v <= 400.0):
            raise ValueError("target_range_high must be between 100 and 400 mg/dL")
        return v


def _get_diabetes_profile(user) -> DiabetesProfile:
    """Resolve DiabetesProfile for a user, raise 404 if not found."""
    try:
        base = BasePatientProfile.objects.select_related("diabetes_profile").get(patient=user)
        return base.diabetes_profile
    except BasePatientProfile.DoesNotExist:
        raise HttpError(404, "Profile not found")
    except DiabetesProfile.DoesNotExist:
        raise HttpError(404, "Diabetes profile not found")


@router.get("/profile", response=PatientProfileSchema)
def get_profile(request):
    return _get_diabetes_profile(request.user)


@router.patch("/profile", response=PatientProfileSchema)
def patch_profile(request, data: ProfilePatchSchema):
    """
    Partial update — only fields explicitly provided are written.
    Validates language choices, unit choices, and physiological glucose bounds.
    Invalidates IAmina session cache when target range or language changes.
    """
    profile = _get_diabetes_profile(request.user)
    base = profile.base_profile

    # Separate fields by model
    _BASE_FIELDS = {"preferred_language", "weight", "height"}
    _DIABETES_FIELDS = {"unit_preference", "target_range_low", "target_range_high"}

    base_changed = []
    diabetes_changed = []
    needs_cache_invalidation = False

    for field, value in data.model_dump(exclude_none=True).items():
        if field in _BASE_FIELDS:
            setattr(base, field, value)
            base_changed.append(field)
        elif field in _DIABETES_FIELDS:
            setattr(profile, field, value)
            diabetes_changed.append(field)
        if field in ("target_range_low", "target_range_high", "preferred_language"):
            needs_cache_invalidation = True

    if base_changed:
        base.save(update_fields=base_changed)
    if diabetes_changed:
        profile.save(update_fields=diabetes_changed)

    if needs_cache_invalidation:
        from diabetes.services.session_cache import invalidate
        invalidate(request.user.id)

    return profile
