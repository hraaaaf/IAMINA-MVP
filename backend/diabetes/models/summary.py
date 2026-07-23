from django.contrib.auth.models import User
from django.db import models


class AISummary(models.Model):
    """AI-generated summary for a patient."""

    LANGUAGE_CHOICES = [
        ('fr', 'French'),
        ('ar', 'Arabic'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_summaries'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='fr'
    )

    summary_text = models.TextField(
        help_text="AI-generated summary and recommendations"
    )

    logs_analyzed = models.IntegerField(
        default=0,
        help_text="Number of log entries analyzed"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Summary'
        verbose_name_plural = 'AI Summaries'
        app_label = 'diabetes'

    def __str__(self):
        return f"{self.patient.username} - {self.created_at.strftime('%Y-%m-%d')} - {self.language}"
