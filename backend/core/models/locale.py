"""Canonical patient locale preferences with per-dimension provenance."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db import models

from core.models.patient import BasePatientProfile


class PatientLocalePreference(models.Model):
    """One authoritative cross-cutting locale record per patient profile."""

    PROVENANCE_CHOICES = [
        ("user_confirmed", "User confirmed"),
        ("suggested", "Suggested"),
        ("defaulted", "Defaulted"),
    ]
    LANGUAGE_CHOICES = [("fr", "French"), ("ar", "Modern Standard Arabic"), ("en", "English")]
    SCRIPT_CHOICES = [("latin", "Latin"), ("arabic", "Arabic")]
    TRANSLITERATION_CHOICES = [("none", "None"), ("latin_arabic", "Arabic in Latin script")]
    DIALECT_CHOICES = [
        ("ar-MA", "Moroccan Darija"),
        ("ar-SA", "Saudi Arabic"),
        ("ar-AE", "Emirati Arabic"),
        ("ar-KW", "Kuwaiti Arabic"),
        ("ar-QA", "Qatari Arabic"),
        ("ar-OM", "Omani Arabic"),
    ]
    GLUCOSE_UNIT_CHOICES = [("mg/dL", "mg/dL"), ("mmol/L", "mmol/L")]

    profile = models.OneToOneField(
        BasePatientProfile,
        on_delete=models.CASCADE,
        related_name="locale_preference",
    )

    country_code = models.CharField(max_length=2, null=True, blank=True)
    country_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    ui_language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, default="fr")
    ui_language_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    response_language = models.CharField(max_length=8, choices=LANGUAGE_CHOICES, null=True, blank=True)
    response_language_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    script_preference = models.CharField(max_length=8, choices=SCRIPT_CHOICES, null=True, blank=True)
    script_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    transliteration_preference = models.CharField(
        max_length=16,
        choices=TRANSLITERATION_CHOICES,
        default="none",
    )
    transliteration_provenance = models.CharField(
        max_length=16,
        choices=PROVENANCE_CHOICES,
        default="defaulted",
    )

    dialect = models.CharField(max_length=8, choices=DIALECT_CHOICES, null=True, blank=True)
    dialect_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    glucose_unit = models.CharField(max_length=8, choices=GLUCOSE_UNIT_CHOICES, default="mg/dL")
    glucose_unit_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    timezone = models.CharField(max_length=64, null=True, blank=True)
    timezone_provenance = models.CharField(max_length=16, choices=PROVENANCE_CHOICES, default="defaulted")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        verbose_name = "Patient Locale Preference"
        verbose_name_plural = "Patient Locale Preferences"

    def clean(self) -> None:
        errors: dict[str, str] = {}
        if self.country_code:
            normalized = self.country_code.upper()
            if len(normalized) != 2 or not normalized.isalpha():
                errors["country_code"] = "Use an ISO 3166-1 alpha-2 country code."
            self.country_code = normalized
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError:
                errors["timezone"] = "Use a valid IANA timezone identifier."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
