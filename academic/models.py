from django.db import models


class Speciality(models.Model):
    """
    Modèle pour les spécialités académiques
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    method_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Spécialité"
        verbose_name_plural = "Spécialités"


class Department(models.Model):
    """
    Modèle pour les départements
    """
    id = models.IntegerField(primary_key=True)
    label = models.CharField(max_length=200)
    method_type = models.CharField(max_length=100, blank=True, null=True)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"


class Level(models.Model):
    """
    Modèle pour les niveaux d'études
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"


class Course(models.Model):
    """
    Modèle pour les cours
    """
    course_code = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    credit_count = models.IntegerField()
    method_type = models.CharField(max_length=100, blank=True, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return f"{self.course_code} - {self.label}"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"


class Program(models.Model):
    """
    Modèle pour les programmes d'études
    """
    id = models.IntegerField(primary_key=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    method_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = "Programme"
        verbose_name_plural = "Programmes"


class AcademicYear(models.Model):
    """
    Modèle pour les années académiques
    """
    id = models.IntegerField(primary_key=True)
    start_at = models.DateField()
    end_at = models.DateField()
    method_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.start_at.year}/{self.end_at.year}"

    class Meta:
        verbose_name = "Année Académique"
        verbose_name_plural = "Années Académiques"
