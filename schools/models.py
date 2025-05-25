from django.db import models


class School(models.Model):
    """
    Modèle pour les établissements scolaires
    """
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    level = models.CharField(max_length=100)  # Niveau de l'école (primaire, secondaire, supérieur)
    method_type = models.CharField(max_length=100, blank=True, null=True)

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
    method_type = models.CharField(max_length=100, blank=True, null=True)

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
    method_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.obtained_year}"

    class Meta:
        verbose_name = "Diplôme Secondaire"
        verbose_name_plural = "Diplômes Secondaires"
