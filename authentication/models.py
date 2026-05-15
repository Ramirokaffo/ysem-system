import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


TWO_FACTOR_CHALLENGE_TTL = timedelta(minutes=15)
TWO_FACTOR_MAX_ATTEMPTS = 5
TWO_FACTOR_CODE_LENGTH = 6


class LoginHistory(models.Model):
    """
    Historique des tentatives de connexion (succès, échec, déconnexion) pour
    tous les acteurs du système (utilisateur Django, étudiant, agent).

    Sert de base à la mise en place future d'une double authentification
    ciblée lorsqu'un acteur se connecte depuis un appareil inconnu.
    """

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_LOGGED_OUT = "logged_out"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Connexion réussie"),
        (STATUS_FAILED, "Échec de connexion"),
        (STATUS_LOGGED_OUT, "Déconnexion"),
    ]

    CHANNEL_CHOICES = [
        ("web", "Application web"),
        ("student_portal", "Portail étudiant"),
        ("api", "API / Mobile"),
    ]

    ACTOR_TYPE_CHOICES = [
        ("user", "Utilisateur"),
        ("student", "Étudiant"),
        ("agent", "Agent"),
        ("anonymous", "Anonyme"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_history",
    )
    actor_type = models.CharField(max_length=20, choices=ACTOR_TYPE_CHOICES, default="anonymous")
    actor_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Identifiant interne lorsque l'acteur n'est pas un BaseUser (étudiant, agent...).",
    )
    actor_identifier = models.CharField(max_length=255, blank=True)
    actor_display = models.CharField(max_length=255, blank=True)

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="web")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    failure_reason = models.CharField(max_length=100, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_family = models.CharField(max_length=100, blank=True)
    browser_family = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os_family = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    device_label = models.CharField(max_length=255, blank=True)
    device_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)

    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_raw = models.JSONField(default=dict, blank=True)

    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    login_at = models.DateTimeField(default=timezone.now, db_index=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    is_known_device = models.BooleanField(default=False)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Historique de connexion"
        verbose_name_plural = "Historiques de connexion"
        ordering = ["-login_at", "-id"]
        indexes = [
            models.Index(fields=["actor_type", "actor_id"]),
            models.Index(fields=["user", "device_fingerprint"]),
            models.Index(fields=["status", "login_at"]),
        ]

    def __str__(self):
        who = self.actor_display or self.actor_identifier or "anonyme"
        return f"{who} - {self.get_status_display()} - {self.login_at:%Y-%m-%d %H:%M}"

    @staticmethod
    def compute_fingerprint(*, user_agent: str = "", os_family: str = "", browser_family: str = "", device_family: str = "") -> str:
        raw = "|".join([
            (os_family or "").lower(),
            (browser_family or "").lower(),
            (device_family or "").lower(),
            (user_agent or "")[:300],
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()



class TwoFactorChallenge(models.Model):
    """
    Défi de double authentification ciblée envoyé par email.

    Créé soit lors d'une connexion nécessitant la 2FA (utilisateur l'a activée
    ou appareil inconnu), soit lors du basculement du paramètre 2FA depuis le
    profil. Le défi est validé via un code à saisir ou un lien direct.
    """

    PURPOSE_LOGIN = "login"
    PURPOSE_TOGGLE = "toggle_2fa"
    PURPOSE_CHOICES = [
        (PURPOSE_LOGIN, "Connexion"),
        (PURPOSE_TOGGLE, "Modification du statut 2FA"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_challenges",
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_LOGIN)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    code_hash = models.CharField(max_length=64)

    requested_state = models.BooleanField(
        null=True,
        blank=True,
        help_text="Pour un défi 'toggle_2fa', valeur cible de two_factor_enabled après validation.",
    )
    next_url = models.CharField(max_length=500, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Défi de double authentification"
        verbose_name_plural = "Défis de double authentification"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "purpose", "consumed_at"]),
        ]

    def __str__(self):
        return f"{self.get_purpose_display()} - {self.user_id} - {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(32)[:64]

    @classmethod
    def generate_code(cls, length: int = TWO_FACTOR_CODE_LENGTH) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @classmethod
    def hash_code(cls, code: str) -> str:
        return hashlib.sha256((code or "").encode("utf-8")).hexdigest()

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def is_locked(self) -> bool:
        return self.attempts >= TWO_FACTOR_MAX_ATTEMPTS

    def is_usable(self) -> bool:
        return not self.is_consumed() and not self.is_expired() and not self.is_locked()

    def check_code(self, code: str) -> bool:
        return secrets.compare_digest(self.code_hash, self.hash_code(code))

    def mark_consumed(self):
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed_at"])
