from django.contrib.auth.models import User
from django.db import models


class AIChatMessage(models.Model):
    """
    AIChatMessage (Phase 6)
    ======================
    Stores conversational history for IAmina.
    Used for conversational memory and audit logging.
    """

    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'IAmina'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Rôle dans la conversation (user/assistant)"
    )
    message = models.TextField(help_text="Contenu du message")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Prompt Versioning (Day 5 task 10)
    # Stores the SHA-256 hash of the prompt template used for this turn.
    prompt_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Hash SHA-256 du prompt template utilisé"
    )

    class Meta:
        ordering = ['created_at']
        app_label = 'diabetes'
        verbose_name = 'Message Chat IA'
        verbose_name_plural = 'Messages Chat IA'

    def __str__(self):
        return f"{self.patient.username} | {self.role}: {self.message[:30]}..."
