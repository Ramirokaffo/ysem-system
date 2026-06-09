from django.conf import settings
from django.db import models


class EmailLog(models.Model):
    """Historique des emails composés et envoyés depuis le système."""

    subject = models.CharField(max_length=255, verbose_name="Objet")
    body = models.TextField(verbose_name="Contenu (HTML)")
    recipients = models.TextField(verbose_name="Destinataires")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='composed_emails',
        verbose_name="Expéditeur",
    )
    success_count = models.PositiveIntegerField(default=0, verbose_name="Envois réussis")
    failure_count = models.PositiveIntegerField(default=0, verbose_name="Envois échoués")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")

    class Meta:
        verbose_name = "Email envoyé"
        verbose_name_plural = "Emails envoyés"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.created_at:%d/%m/%Y %H:%M})"

    @property
    def recipients_list(self):
        return [r.strip() for r in (self.recipients or '').split(',') if r.strip()]
