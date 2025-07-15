# from django.db.models import Count
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError



class Department(models.Model):
    """
    Modèle pour les départements
    """
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"


class Level(models.Model):
    """
    Modèle pour les niveaux d'études
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"



class Program(models.Model):
    """
    Modèle pour les programmes d'études
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Programme"
        verbose_name_plural = "Programmes"



class Speciality(models.Model):
    """
    Modèle pour les spécialités académiques
    """
    name = models.CharField(max_length=200)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, related_name='specialities')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='specialities')
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Spécialité"
        verbose_name_plural = "Spécialités"


class Course(models.Model):
    """
    Modèle pour les cours
    """
    course_code = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    credit_count = models.IntegerField()
    speciality = models.ForeignKey(Speciality, on_delete=models.SET_NULL, null=True, related_name='courses')
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, related_name='courses')
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, related_name='courses')

    def __str__(self):
        return f"{self.course_code} - {self.label}"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"



class AcademicYear(models.Model):
    """
    Modèle pour les années académiques
    """
    name = models.CharField(max_length=100, blank=True, editable=False)
    is_active = models.BooleanField(default=False, verbose_name="Année Académique Active")
    start_at = models.DateField()
    end_at = models.DateField()
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def save(self, *args, **kwargs):
        self.name = f"{self.start_at.year}/{self.end_at.year}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.start_at.year}/{self.end_at.year}"

    class Meta:
        verbose_name = "Année Académique"
        verbose_name_plural = "Années Académiques"
