"""
diabetes.models.patient — DiabetesProfile

Diabetes-specific extension of core.BasePatientProfile.
Identity fields (firebase_uid, preferred_language, etc.) now live on
core.BasePatientProfile, linked via the base_profile OneToOneField.

Created in P2 of the IAmina Platform Transformation Plan (ADR-0008).
"""
from django.db import models


class DiabetesProfile(models.Model):
    """
    Diabetes module extension.

    Linked to core.BasePatientProfile via base_profile (OneToOneField).
    Access identity fields via: profile.base_profile.firebase_uid, etc.
    Access via reverse: base_profile_instance.diabetes_profile.

    Clinical identity fields are nullable by design. Authentication may create the
    extension shell, but must never guess a diabetes diagnosis or treatment. NULL
    means "not yet declared/validated", not a clinical default.
    """

    DIABETES_TYPE_CHOICES = [
        ('type1', 'Type 1'),
        ('type2', 'Type 2'),
        ('gestational', 'Gestationnel'),
        ('prediabetes', 'Prediabete'),
    ]

    TREATMENT_TYPE_CHOICES = [
        ('insulin_pump', 'Pompe a insuline'),
        ('insulin_injections', "Injections d'insuline"),
        ('oral_meds', 'Medicaments oraux'),
        ('diet_exercise', 'Regime et exercice'),
        # Legacy value kept for data compatibility
        ('insulin', 'Insuline'),
    ]

    UNIT_CHOICES = [
        ('mg_dl', 'mg/dL'),
        ('mmol_l', 'mmol/L'),
    ]

    base_profile = models.OneToOneField(
        "core.BasePatientProfile",
        on_delete=models.CASCADE,
        related_name="diabetes_profile",
    )

    diabetes_type = models.CharField(
        max_length=20,
        choices=DIABETES_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Patient-declared/validated type of diabetes. NULL = unknown.",
    )

    treatment_type = models.CharField(
        max_length=20,
        choices=TREATMENT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Patient-declared current treatment approach. NULL = unknown.",
    )

    target_range_low = models.IntegerField(
        default=70,
        help_text="Lower target glucose (mg/dL)",
    )

    target_range_high = models.IntegerField(
        default=180,
        help_text="Upper target glucose (mg/dL)",
    )

    unit_preference = models.CharField(
        max_length=6,
        choices=UNIT_CHOICES,
        default='mg_dl',
        help_text="Preferred glucose unit",
    )

    ramadan_start_date = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Patient-declared start of an optional Ramadan journal context. "
            "NULL means no period is configured."
        ),
    )

    ramadan_end_date = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Patient-declared end of an optional Ramadan journal context. "
            "NULL means no period is configured."
        ),
    )

    class Meta:
        app_label = 'diabetes'
        # Keep the original table name — the SeparateDatabaseAndState migration
        # preserved the existing diabetes_patientprofile table rather than renaming it.
        db_table = 'diabetes_patientprofile'
        verbose_name = 'Diabetes Profile'
        verbose_name_plural = 'Diabetes Profiles'

    def __str__(self):
        diabetes_label = (
            self.get_diabetes_type_display()
            if self.diabetes_type
            else "clinical profile incomplete"
        )
        return f"{self.base_profile.patient.username} - {diabetes_label}"

    @property
    def clinical_profile_complete(self) -> bool:
        """True only when core diabetes identity fields were actually provided."""
        return bool(self.diabetes_type and self.treatment_type)

    # ── Convenience accessors for backward-compat code paths ─────────────────
    # These proxy to base_profile so callers that do profile.preferred_language
    # still work without changes during the P2→P3 transition window.

    @property
    def patient(self):
        return self.base_profile.patient

    @property
    def patient_id(self):
        return self.base_profile.patient_id

    @property
    def firebase_uid(self):
        return self.base_profile.firebase_uid

    @firebase_uid.setter
    def firebase_uid(self, value):
        self.base_profile.firebase_uid = value

    @property
    def preferred_language(self):
        return self.base_profile.preferred_language

    @preferred_language.setter
    def preferred_language(self, value):
        self.base_profile.preferred_language = value

    @property
    def ai_consent_given_at(self):
        return self.base_profile.ai_consent_given_at

    @ai_consent_given_at.setter
    def ai_consent_given_at(self, value):
        self.base_profile.ai_consent_given_at = value

    @property
    def premium_valid_until(self):
        return self.base_profile.premium_valid_until

    @premium_valid_until.setter
    def premium_valid_until(self, value):
        self.base_profile.premium_valid_until = value

    @property
    def gender(self):
        return self.base_profile.gender

    @gender.setter
    def gender(self, value):
        self.base_profile.gender = value

    @property
    def date_of_birth(self):
        return self.base_profile.date_of_birth

    @date_of_birth.setter
    def date_of_birth(self, value):
        self.base_profile.date_of_birth = value

    @property
    def weight(self):
        return self.base_profile.weight

    @weight.setter
    def weight(self, value):
        self.base_profile.weight = value

    @property
    def height(self):
        return self.base_profile.height

    @height.setter
    def height(self, value):
        self.base_profile.height = value

    @property
    def created_at(self):
        return self.base_profile.created_at

    @property
    def updated_at(self):
        return self.base_profile.updated_at

    def save(self, *args, **kwargs):
        """
        Save DiabetesProfile fields only.

        Identity field setters (firebase_uid, preferred_language, etc.) write
        to base_profile in-memory. Callers are responsible for saving base_profile
        explicitly when identity fields have been mutated via setters.
        Use profile.base_profile.save() for identity field persistence.
        """
        super().save(*args, **kwargs)


# ── Backward-compatibility alias ─────────────────────────────────────────────
# All existing code that does `from diabetes.models import PatientProfile`
# continues to work. Removed in P3 when all import sites are migrated.
PatientProfile = DiabetesProfile