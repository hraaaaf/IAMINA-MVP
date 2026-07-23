from django.contrib.auth.models import User
from django.db import models


class DemoFeedback(models.Model):
    """Patient feedback collected after viewing AI insights."""

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='demo_feedbacks'
    )

    was_surprised = models.BooleanField(
        null=True,
        blank=True,
        help_text="Was the patient surprised by the insights?"
    )

    comment = models.TextField(
        blank=True,
        default='',
        help_text="Patient's free-text reaction"
    )

    scenario_id = models.CharField(
        max_length=1,
        blank=True,
        default='',
        help_text="Which demo scenario was shown (A-E)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Demo Feedback'
        verbose_name_plural = 'Demo Feedbacks'
        app_label = 'diabetes'

    def __str__(self):
        surprised = "surprised" if self.was_surprised else "not surprised"
        return f"{self.patient.username} - {self.created_at.strftime('%Y-%m-%d')} - {surprised}"
