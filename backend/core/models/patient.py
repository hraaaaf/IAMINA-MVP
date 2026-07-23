"""
core.models.patient — BasePatientProfile

Chassis-owned identity fields. Every patient in the IAmina platform is anchored
here regardless of which modules they have activated.

Created in P2 of the IAmina Platform Transformation Plan (ADR-0008).
"""
from django.contrib.auth.models import User
from django.db import models


class BasePatientProfile(models.Model):
    """
    Platform chassis identity anchor.

    Owns all cross-cutting patient identity fields:
    auth bridge (firebase_uid), language, RGPD consent, monetisation,
    and biometrics (gender, DOB, weight, height).

    Module-specific fields live in their respective extension models
    (e.g. diabetes.DiabetesProfile) linked via OneToOneField.
    """

    LANGUAGE_CHOICES = [
        ('fr',    'Français'),
        ('ar-MA', 'Darija (dialecte marocain)'),
        ('ar',    'Arabe classique (Fusha)'),
    ]

    GENDER_CHOICES = [
        ('male',   'Homme'),
        ('female', 'Femme'),
    ]

    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='base_profile',
    )

    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Firebase Auth UID — chassis-level auth bridge.",
    )

    preferred_language = models.CharField(
        max_length=8,
        choices=LANGUAGE_CHOICES,
        default='ar-MA',
        help_text="UI language preference.",
    )

    ai_consent_given_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the patient explicitly consented to AI analysis. NULL = no consent.",
    )

    premium_valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End of paid Premium access.",
    )

    gender = models.CharField(
        max_length=6,
        choices=GENDER_CHOICES,
        default='female',
        help_text="Genre",
    )

    date_of_birth = models.DateField(
        help_text="Date de naissance",
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Weight in kg",
    )

    height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Height in cm",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Base Patient Profile'
        verbose_name_plural = 'Base Patient Profiles'

    def __str__(self):
        return f"BasePatientProfile({self.patient.username})"
