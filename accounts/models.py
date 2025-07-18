from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseUser(AbstractUser):
    """
    Extension du modèle User de Django pour ajouter des champs personnalisés
    Inclut les propriétés du personnel (Staff) pour simplifier l'architecture
    """
    # Champs personnels de base
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        blank=True,
        null=True
    )
    role = models.CharField(max_length=100, blank=True, null=True, default="student",
        choices=[
            ('scholar', 'Scolarité'),
            ('planning', 'Planification'),
            ('teaching', 'Suivie des Enseignements'),
            ("student", "Étudiant"),
            ("super_admin", "Administrateur"),
            # ("agent", "Agent de prospection")
        ],
    )

    class Meta:
        db_table = 'accounts_baseuser'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def is_scholar_admin(self):
        return self.role == "scholar"

    def is_study_admin(self):
        return self.role == "teaching"

    def is_planning_admin(self):
        return self.role == "planning"


class Godfather(models.Model):
    """
    Modèle pour les parrains/tuteurs
    """
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='godfather_profile')
    full_name = models.CharField(max_length=200)
    occupation = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Parrain"
        verbose_name_plural = "Parrains"



