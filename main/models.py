from django.db import models


class SystemSettings(models.Model):
    """
    Modèle pour stocker les paramètres système de YSEM
    """
    # Paramètres généraux
    institution_name = models.CharField(max_length=200, default="YSEM - École Supérieure")
    institution_code = models.CharField(max_length=50, default="YSEM001")
    address = models.TextField(default="Damas, Yaoundé, Cameroun")
    phone = models.CharField(max_length=20, default="+237 XXX XXX XXX")
    email = models.EmailField(default="contact@ysem.education")
    website = models.URLField(default="https://www.ysem.education")
    timezone = models.CharField(max_length=50, default="Africa/Douala")
    language = models.CharField(max_length=10, default="fr")

    # Paramètres académiques
    inscription_period = models.CharField(
        max_length=20,
        choices=[('open', 'Ouverte'), ('closed', 'Fermée'), ('limited', 'Limitée')],
        default='open'
    )
    auto_approval = models.BooleanField(default=True)
    require_documents = models.BooleanField(default=True)
    allow_external_registration = models.BooleanField(default=True)

    # Paramètres des programmes et niveaux
    auto_level_progression = models.BooleanField(default=True)
    allow_level_change = models.BooleanField(default=False)
    require_level_validation = models.BooleanField(default=True)
    allow_program_change = models.BooleanField(default=False)
    require_program_validation = models.BooleanField(default=True)

    # Paramètres utilisateurs
    default_role = models.CharField(max_length=20, default="student")
    session_timeout = models.IntegerField(default=30)  # en minutes
    view_documents = models.BooleanField(default=True)
    download_docs = models.BooleanField(default=True)
    update_profile = models.BooleanField(default=True)
    view_statistics = models.BooleanField(default=False)

    # Paramètres des documents
    max_file_size = models.IntegerField(default=5)  # en MB
    allowed_formats = models.CharField(max_length=100, default="PNG, JPG, PDF")
    student_card_enabled = models.BooleanField(default=True)
    transcript_enabled = models.BooleanField(default=True)
    certificate_enabled = models.BooleanField(default=True)
    diploma_enabled = models.BooleanField(default=True)
    require_original_docs = models.BooleanField(default=True)

    # Paramètres de notification
    email_enrollment = models.BooleanField(default=True)
    email_documents = models.BooleanField(default=True)
    email_deadlines = models.BooleanField(default=False)
    system_errors = models.BooleanField(default=True)
    system_updates = models.BooleanField(default=False)

    # Paramètres de gestion des données
    backup_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Quotidienne'), ('weekly', 'Hebdomadaire'), ('monthly', 'Mensuelle')],
        default='daily'
    )
    data_retention = models.IntegerField(default=7)  # en années
    audit_log = models.BooleanField(default=True)
    data_encryption = models.BooleanField(default=True)
    auto_cleanup = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètres Système"
        verbose_name_plural = "Paramètres Système"

    def __str__(self):
        return f"Paramètres système - {self.institution_name}"

    @classmethod
    def get_settings(cls):
        """Récupère les paramètres système (crée une instance par défaut si nécessaire)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule instance de paramètres
        self.pk = 1
        super().save(*args, **kwargs)
