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
    role = models.CharField(max_length=100, blank=True, null=True)
    method_type = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'accounts_baseuser'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

class Godfather(models.Model):
    """
    Modèle pour les parrains/tuteurs
    """
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='godfather_profile')
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    occupation = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Parrain"
        verbose_name_plural = "Parrains"



