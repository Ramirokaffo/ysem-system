from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    CATEGORY_CHOICES = [
        ("model", "Modèle"),
        ("auth", "Authentification"),
        ("business", "Métier"),
        ("m2m", "Relation M2M"),
    ]
    ACTION_CHOICES = [
        ("create", "Création"),
        ("update", "Modification"),
        ("delete", "Suppression"),
        ("m2m_add", "Ajout M2M"),
        ("m2m_remove", "Suppression M2M"),
        ("m2m_clear", "Vidage M2M"),
        ("login", "Connexion"),
        ("logout", "Déconnexion"),
        ("login_failed", "Échec de connexion"),
        ("password_change", "Changement de mot de passe"),
        ("bulk_update", "Mise à jour en masse"),
        ("bulk_delete", "Suppression en masse"),
    ]

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    message = models.TextField(blank=True)

    actor_type = models.CharField(max_length=30, blank=True)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_agent_id = models.PositiveIntegerField(null=True, blank=True)
    actor_identifier = models.CharField(max_length=255, blank=True)
    actor_display = models.CharField(max_length=255, blank=True)

    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    target_object_id = models.CharField(max_length=64, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    target_app_label = models.CharField(max_length=100, blank=True)
    target_model = models.CharField(max_length=100, blank=True)

    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    changes = models.JSONField(default=dict, blank=True)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Entrée de journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["category", "action"]),
            models.Index(fields=["target_app_label", "target_model", "target_object_id"]),
        ]

    def __str__(self):
        target = self.target_repr or self.actor_display or self.actor_identifier or "sans cible"
        return f"{self.get_action_display()} - {target}"
