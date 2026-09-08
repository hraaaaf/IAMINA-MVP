from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class LogEntry(models.Model):
    """A single health log entry from a patient."""

    SLEEP_CHOICES = [
        ('good', 'Bonne'),
        ('bad', 'Mauvaise'),
    ]

    EXERCISE_CHOICES = [
        ('yes', 'Oui'),
        ('no', 'Non'),
    ]

    STRESS_CHOICES = [
        ('yes', 'Oui'),
        ('no', 'Non'),
    ]

    FATIGUE_CHOICES = [
        ('ok', 'Bien'),
        ('tired', 'Fatigué(e)'),
    ]

    SICK_CHOICES = [
        ('no', 'Non'),
        ('yes', 'Oui'),
    ]

    GLYCEMIC_CONTEXT_CHOICES = [
        ('fasting', 'À jeun'),
        ('pre_meal', 'Avant repas'),
        ('post_meal', 'Après repas'),
        ('other', 'Autre contexte'),
    ]

    MEAL_TYPE_CHOICES = [
        ('fasting', 'À jeun'),
        ('breakfast', 'Petit-déjeuner'),
        ('lunch', 'Déjeuner'),
        ('snack', 'Collation'),
        ('dinner', 'Dîner'),
        ('iftar', 'Iftar'),
        ('suhoor', 'Suhoor'),
        ('other', 'Autre'),
    ]

    # Amina roadmap — see AMINA_MVP_PLAN.md §3.
    SOURCE_CHOICES = [
        ('manual', 'Manuel'),
        ('voice', 'Vocal'),
        ('cgm', 'CGM'),
        ('import', 'Import'),
        ('demo', 'Démo'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='log_entries'
    )

    # Automatic timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    # User-specified time (optional override)
    logged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Heure de la mesure (si differente de maintenant)"
    )

    # Measurement context is distinct from the optional meal category.
    glycemic_context = models.CharField(
        max_length=12,
        choices=GLYCEMIC_CONTEXT_CHOICES,
        blank=True,
        default='',
        help_text="Contexte de la mesure: à jeun, avant/après repas ou autre"
    )

    # Meal category. Legacy choices remain readable for existing records; new
    # Journal writes use breakfast/lunch/dinner/snack only until Ramadan v2.
    meal_type = models.CharField(
        max_length=10,
        choices=MEAL_TYPE_CHOICES,
        blank=True,
        default='',
        help_text="Type de repas"
    )

    # Core health data
    blood_sugar = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Blood sugar level (mg/dL)"
    )

    meal_description = models.TextField(
        blank=True,
        help_text="Texte libre décrivant le repas"
    )
    meal_items = models.JSONField(
        default=list,
        blank=True,
        help_text="IDs structurés des plats sélectionnés via le dictionnaire culinaire."
    )
    meal_portions = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Portions confirmées par le patient. Contient uniquement la saisie "
            "utilisateur (food_id, portion_id et/ou grammes), jamais un calcul "
            "nutritionnel présenté comme vérité persistée."
        ),
    )

    # Lifestyle tracking
    insulin_units = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Insulin units taken"
    )

    # Simple activity fields
    exercised = models.CharField(
        max_length=3,
        choices=EXERCISE_CHOICES,
        default='',
        blank=True,
        help_text="Exercice aujourd'hui ?"
    )

    sleep_quality = models.CharField(
        max_length=4,
        choices=SLEEP_CHOICES,
        default='',
        blank=True,
        help_text="Qualite du sommeil"
    )

    stressed = models.CharField(
        max_length=3,
        choices=STRESS_CHOICES,
        default='',
        blank=True,
        help_text="Niveau de stress"
    )

    fatigue_level = models.CharField(
        max_length=5,
        choices=FATIGUE_CHOICES,
        default='',
        blank=True,
        help_text="Niveau de fatigue aujourd'hui"
    )

    is_sick = models.CharField(
        max_length=3,
        choices=SICK_CHOICES,
        default='',
        blank=True,
        help_text="Malade ou pas bien aujourd'hui"
    )

    # Amina fields (nullable / defaulted — no behaviour change yet).
    source = models.CharField(
        max_length=16,
        choices=SOURCE_CHOICES,
        default='manual',
        help_text="Provenance de l'entrée — manuel, vocal, CGM, import ou démo."
    )
    # NOTE: daily_wellness removed (was empty blob — scalar columns are source of truth).
    # See migration 0014 for the drop.
    client_uuid = models.UUIDField(
        null=True, blank=True, db_index=True, unique=True,
        help_text=(
            "UUID généré côté client (Drift) pour l'idempotence du sync. "
            "Même UUID = même entrée."
        ),
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log Entry'
        verbose_name_plural = 'Log Entries'
        app_label = 'diabetes'
        constraints = [
            models.CheckConstraint(
                condition=Q(blood_sugar__gte=30) & Q(blood_sugar__lte=600),
                name='logentry_blood_sugar_range',
                violation_error_message='Blood sugar must be between 30 and 600 mg/dL.',
            ),
        ]

    @property
    def effective_time(self):
        """Return logged_at if set, otherwise created_at."""
        return self.logged_at or self.created_at

    def __str__(self):
        return f"{self.patient.username} - {self.effective_time.strftime('%Y-%m-%d %H:%M')} - {self.blood_sugar} mg/dL"
