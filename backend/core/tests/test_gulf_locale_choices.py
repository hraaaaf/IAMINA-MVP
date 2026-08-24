from django.core.exceptions import ValidationError

from core.models.locale import PatientLocalePreference
from core.models.patient import BasePatientProfile

GULF_DIALECTS = ("ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM")


def test_gulf_dialect_choices_are_canonical():
    choices = dict(PatientLocalePreference.DIALECT_CHOICES)
    for dialect in GULF_DIALECTS:
        assert dialect in choices


def test_unsupported_dialect_is_rejected(db, django_user_model):
    user = django_user_model.objects.create_user(username="locale-invalid-dialect")
    profile = BasePatientProfile.objects.create(patient=user)

    preference = PatientLocalePreference(
        profile=profile,
        response_language="ar",
        response_language_provenance="user_confirmed",
        dialect="ar-XX",
        dialect_provenance="user_confirmed",
    )

    try:
        preference.full_clean()
    except ValidationError as exc:
        assert "dialect" in exc.message_dict
    else:
        raise AssertionError("unsupported dialect must fail model validation")
