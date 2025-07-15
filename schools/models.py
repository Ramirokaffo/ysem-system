from django.db import models


class School(models.Model):
    """
    Modèle pour les établissements scolaires
    """
    LEVEL_CHOICE = [
        ('primary', 'Primaire'),
        ('secondary', 'Secondaire'),
        ('higher', 'Supérieur'),
    ]
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    level = models.CharField(max_length=100, choices=LEVEL_CHOICE) # Niveau de l'école (primaire, secondaire, supérieur)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "École"
        verbose_name_plural = "Écoles"


class UniversityLevel(models.Model):
    """
    Modèle pour les niveaux universitaires
    """
    level_name = models.CharField(max_length=100)
    diploma_name = models.CharField(max_length=200, blank=True, null=True)
    speciality = models.CharField(max_length=200, blank=True, null=True)
    academic_year = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.level_name

    class Meta:
        verbose_name = "Niveau Universitaire"
        verbose_name_plural = "Niveaux Universitaires"


class SecondaryDiploma(models.Model):
    """
    Modèle pour les diplômes du secondaire
    """
    name = models.CharField(max_length=200)
    serie = models.CharField(max_length=100, blank=True, null=True)
    obtained_year = models.IntegerField()
    mention = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return f"{self.name} - {self.obtained_year}"

    class Meta:
        verbose_name = "Diplôme Secondaire"
        verbose_name_plural = "Diplômes Secondaires"
