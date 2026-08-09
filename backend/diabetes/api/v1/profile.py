"""
Patient profile and patient-owned AI media consent management.

GET    /api/v1/profile
PATCH  /api/v1/profile
GET    /api/v1/profile/ai-media-consents
PUT    /api/v1/profile/ai-media-consents/{purpose}/{modality}
DELETE /api/v1/profile/ai-media-consents/{purpose}/{modality}
"""
from datetime import date, datetime
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, field_validator, model_validator

from core.ai_egress import grant_media_consent, revoke_media_consent
from core.models import AIMediaConsentGrant, BasePatientProfile
from diabetes.models import DiabetesProfile

from .schemas import PatientProfileSchema

router = Router(tags=["profile"])

_VALID_LANGUAGES = {"fr", "ar-MA", "ar"}
_VALID_UNITS = {"mg_dl", "mmol_l"}
_VALID_DIABETES_TYPES = {value for value, _ in DiabetesProfile.DIABETES_TYPE_CHOICES}
_VALID_TREATMENTS = {value for value, _ in DiabetesProfile.TREATMENT_TYPE_CHOICES}
_VALID_GENDERS = {value for value, _ in BasePatientProfile.GENDER_CHOICES}
_NON_NULLABLE_PATCH_FIELDS = {
    "preferred_language",
    "unit_preference",
    "target_range_low",
    "target_range_high",
}

# Consumer-facing options intentionally enumerate only raw-media operations that
# already exist in the central egress registry. The central grant helper remains
# authoritative and rejects any pair that drifts from the egress policy.
_MEDIA_CONSENT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("document_ingest", "document"),
    ("document_ingest", "image"),
    ("glucometer_ocr", "image"),
    ("meal_vision", "image"),
    ("voice_chat", "audio"),
    ("voice_transcription", "audio"),
)
_MEDIA_CONSENT_OPTION_SET = frozenset(_MEDIA_CONSENT_OPTIONS)


class ProfilePatchSchema(BaseModel):
    """All fields optional; supplied values are treated as patient declarations."""

    preferred_language: Optional[str] = None
    diabetes_type: Optional[str] = None
    treatment_type: Optional[str] = None
    unit_preference: Optional[str] = None
    target_range_low: Optional[float] = None
    target_range_high: Optional[float] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    weight: Optional[float] = None
    height: Optional[int] = None
    ramadan_start_date: Optional[date] = None
    ramadan_end_date: Optional[date] = None

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in _VALID_LANGUAGES:
            raise ValueError(f"preferred_language must be one of {_VALID_LANGUAGES}")
        return v

    @field_validator("diabetes_type")
    @classmethod
    def validate_diabetes_type(cls, v):
        if v is not None and v not in _VALID_DIABETES_TYPES:
            raise ValueError(f"diabetes_type must be one of {_VALID_DIABETES_TYPES}")
        return v

    @field_validator("treatment_type")
    @classmethod
    def validate_treatment_type(cls, v):
        if v is not None and v not in _VALID_TREATMENTS:
            raise ValueError(f"treatment_type must be one of {_VALID_TREATMENTS}")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v is not None and v not in _VALID_GENDERS:
            raise ValueError(f"gender must be one of {_VALID_GENDERS}")
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

    @model_validator(mode="after")
    def reject_explicit_null_for_non_nullable_fields(self):
        """Omission is allowed in PATCH; explicit null is not for required DB fields."""
        invalid = sorted(
            field
            for field in self.model_fields_set & _NON_NULLABLE_PATCH_FIELDS
            if getattr(self, field) is None
        )
        if invalid:
            raise ValueError(f"Fields cannot be null: {', '.join(invalid)}")
        return self

    @model_validator(mode="after")
    def validate_ramadan_period_pair(self):
        """Ramadan context is explicit: persist a complete pair or clear both."""
        fields = {"ramadan_start_date", "ramadan_end_date"}
        touched = fields & self.model_fields_set
        if not touched:
            return self
        if touched != fields:
            raise ValueError(
                "ramadan_start_date and ramadan_end_date must be patched together"
            )
        start = self.ramadan_start_date
        end = self.ramadan_end_date
        if (start is None) != (end is None):
            raise ValueError("Ramadan period must contain both dates or clear both")
        if start is not None and end is not None and start > end:
            raise ValueError(
                "ramadan_start_date must be on or before ramadan_end_date"
            )
        return self


class MediaConsentStateSchema(BaseModel):
    purpose: str
    modality: str
    active: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


def _get_base_profile(user) -> BasePatientProfile:
    try:
        return BasePatientProfile.objects.get(patient=user)
    except BasePatientProfile.DoesNotExist as exc:
        raise HttpError(404, "Profile not found") from exc


def _get_diabetes_profile(user) -> DiabetesProfile:
    """Resolve DiabetesProfile for a user, raise 404 if not found."""
    try:
        base = BasePatientProfile.objects.select_related("diabetes_profile").get(patient=user)
        return base.diabetes_profile
    except BasePatientProfile.DoesNotExist as exc:
        raise HttpError(404, "Profile not found") from exc
    except DiabetesProfile.DoesNotExist as exc:
        raise HttpError(404, "Diabetes profile not found") from exc


def _validate_media_consent_option(purpose: str, modality: str) -> None:
    if (purpose, modality) not in _MEDIA_CONSENT_OPTION_SET:
        raise HttpError(422, "Unsupported media consent purpose/modality pair")


def _media_consent_state(
    purpose: str,
    modality: str,
    grant: AIMediaConsentGrant | None,
) -> dict:
    return {
        "purpose": purpose,
        "modality": modality,
        "active": grant is not None and grant.revoked_at is None,
        "granted_at": grant.granted_at if grant is not None else None,
        "revoked_at": grant.revoked_at if grant is not None else None,
    }


@router.get("/profile", response=PatientProfileSchema)
def get_profile(request):
    return _get_diabetes_profile(request.user)


@router.patch("/profile", response=PatientProfileSchema)
def patch_profile(request, data: ProfilePatchSchema):
    """Persist only explicitly supplied patient-declared profile fields."""
    profile = _get_diabetes_profile(request.user)
    base = profile.base_profile

    base_fields = {
        "preferred_language",
        "gender",
        "date_of_birth",
        "weight",
        "height",
    }
    diabetes_fields = {
        "diabetes_type",
        "treatment_type",
        "unit_preference",
        "target_range_low",
        "target_range_high",
        "ramadan_start_date",
        "ramadan_end_date",
    }

    base_changed: list[str] = []
    diabetes_changed: list[str] = []
    needs_cache_invalidation = False

    for field, value in data.model_dump(exclude_unset=True).items():
        if field in base_fields:
            setattr(base, field, value)
            base_changed.append(field)
        elif field in diabetes_fields:
            setattr(profile, field, value)
            diabetes_changed.append(field)

        if field in {
            "target_range_low",
            "target_range_high",
            "preferred_language",
            "diabetes_type",
            "treatment_type",
        }:
            needs_cache_invalidation = True

    if base_changed:
        base.save(update_fields=base_changed)
    if diabetes_changed:
        profile.save(update_fields=diabetes_changed)

    if needs_cache_invalidation:
        from diabetes.services.session_cache import invalidate

        invalidate(request.user.id)

    return profile


@router.get("/profile/ai-media-consents", response=list[MediaConsentStateSchema])
def list_ai_media_consents(request):
    """Return every supported raw-media consent option for the authenticated patient."""
    _get_base_profile(request.user)
    grants = {
        (grant.purpose, grant.modality): grant
        for grant in AIMediaConsentGrant.objects.filter(patient=request.user)
    }
    return [
        _media_consent_state(purpose, modality, grants.get((purpose, modality)))
        for purpose, modality in _MEDIA_CONSENT_OPTIONS
    ]


@router.put(
    "/profile/ai-media-consents/{purpose}/{modality}",
    response=MediaConsentStateSchema,
)
def grant_ai_media_consent(request, purpose: str, modality: str):
    """Grant or reactivate one exact raw-media purpose/modality permission."""
    _validate_media_consent_option(purpose, modality)
    base = _get_base_profile(request.user)
    if base.ai_consent_given_at is None:
        raise HttpError(409, "Global AI consent is required before media consent")

    grant = grant_media_consent(request.user.id, purpose, modality)
    return _media_consent_state(purpose, modality, grant)


@router.delete(
    "/profile/ai-media-consents/{purpose}/{modality}",
    response=MediaConsentStateSchema,
)
def revoke_ai_media_consent(request, purpose: str, modality: str):
    """Revoke one exact raw-media permission; repeated revocation is idempotent."""
    _validate_media_consent_option(purpose, modality)
    _get_base_profile(request.user)
    revoke_media_consent(request.user.id, purpose, modality)
    grant = AIMediaConsentGrant.objects.filter(
        patient=request.user,
        purpose=purpose,
        modality=modality,
    ).first()
    return _media_consent_state(purpose, modality, grant)