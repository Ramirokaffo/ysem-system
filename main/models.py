from django.db import models


class SystemSettings(models.Model):
    """
    Modèle pour stocker les paramètres système de YSEM
    """
    # Paramètres généraux
    institution_name = models.CharField(max_length=200, default="YSEM - École Supérieure", verbose_name="Nom de l'institution")
    institution_code = models.CharField(max_length=50, default="YSEM001", verbose_name="Code de l'institution")
    address = models.TextField(default="Damas, Yaoundé, Cameroun", verbose_name="Adresse")
    phone = models.CharField(max_length=20, default="+237 XXX XXX XXX", verbose_name="Téléphone")
    email = models.EmailField(default="contact@ysem.education", verbose_name="Email")
    website = models.URLField(default="https://www.ysem.education", verbose_name="Site web")
    timezone = models.CharField(max_length=50, default="Africa/Douala", verbose_name="Fuseau horaire")
    language = models.CharField(max_length=10, default="fr", verbose_name="Langue")

    # Paramètres académiques
    inscription_period = models.CharField(
        max_length=20,
        choices=[('open', 'Ouverte'), ('closed', 'Fermée'), ('limited', 'Limitée')],
        default='open',
        verbose_name="Période d'inscription"
    )
    auto_approval = models.BooleanField(default=True, verbose_name="Approbation automatique")
    require_documents = models.BooleanField(default=True, verbose_name="Exiger les documents")
    allow_external_registration = models.BooleanField(default=True, verbose_name="Autoriser l'inscription externe")

    # Paramètres des programmes et niveaux
    auto_level_progression = models.BooleanField(default=True, verbose_name="Progression automatique de niveau")
    allow_level_change = models.BooleanField(default=False, verbose_name="Autoriser le changement de niveau")
    require_level_validation = models.BooleanField(default=True, verbose_name="Exiger la validation de niveau")
    allow_program_change = models.BooleanField(default=False, verbose_name="Autoriser le changement de programme")
    require_program_validation = models.BooleanField(default=True, verbose_name="Exiger la validation de programme")

    # Paramètres utilisateurs
    default_role = models.CharField(max_length=20, default="student", verbose_name="Rôle par défaut")
    session_timeout = models.IntegerField(default=30, verbose_name="Délai d'expiration de session (minutes)")
    view_documents = models.BooleanField(default=True, verbose_name="Voir les documents")
    download_docs = models.BooleanField(default=True, verbose_name="Télécharger les documents")
    update_profile = models.BooleanField(default=True, verbose_name="Mettre à jour le profil")
    view_statistics = models.BooleanField(default=False, verbose_name="Voir les statistiques")

    # Paramètres des documents
    max_file_size = models.IntegerField(default=5, verbose_name="Taille maximale de fichier (MB)")
    allowed_formats = models.CharField(max_length=100, default="PNG, JPG, PDF", verbose_name="Formats autorisés")
    student_card_enabled = models.BooleanField(default=True, verbose_name="Carte d'étudiant activée")
    transcript_enabled = models.BooleanField(default=True, verbose_name="Relevé de notes activé")
    certificate_enabled = models.BooleanField(default=True, verbose_name="Certificat activé")
    diploma_enabled = models.BooleanField(default=True, verbose_name="Diplôme activé")
    require_original_docs = models.BooleanField(default=True, verbose_name="Exiger les documents originaux")

    # Paramètres de notification
    email_enrollment = models.BooleanField(default=True, verbose_name="Email d'inscription")
    email_documents = models.BooleanField(default=True, verbose_name="Email de documents")
    email_deadlines = models.BooleanField(default=False, verbose_name="Email d'échéances")
    system_errors = models.BooleanField(default=True, verbose_name="Erreurs système")
    system_updates = models.BooleanField(default=False, verbose_name="Mises à jour système")

    # Paramètres de gestion des données
    backup_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Quotidienne'), ('weekly', 'Hebdomadaire'), ('monthly', 'Mensuelle')],
        default='daily',
        verbose_name="Fréquence de sauvegarde"
    )
    data_retention = models.IntegerField(default=7, verbose_name="Rétention des données (années)")
    audit_log = models.BooleanField(default=True, verbose_name="Journal d'audit")
    data_encryption = models.BooleanField(default=True, verbose_name="Chiffrement des données")
    auto_cleanup = models.BooleanField(default=False, verbose_name="Nettoyage automatique")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

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
