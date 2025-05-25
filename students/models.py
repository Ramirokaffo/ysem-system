from django.db import models
from accounts.models import BaseUser, Godfather
from academic.models import Level, Program
from schools.models import School


class StudentMetaData(models.Model):
    """
    Métadonnées pour les étudiants (informations complémentaires)
    """
    mother_live_city = models.CharField(max_length=100, blank=True, null=True)
    mother_email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100)
    lang = models.CharField(max_length=50, default='fr')
    original_region = models.CharField(max_length=100, blank=True, null=True)
    original_department = models.CharField(max_length=100, blank=True, null=True)
    original_district = models.CharField(max_length=100, blank=True, null=True)
    residence_city = models.CharField(max_length=100, blank=True, null=True)
    residence_quarter = models.CharField(max_length=100, blank=True, null=True)
    mother_occupation = models.CharField(max_length=200, blank=True, null=True)
    father_full_name = models.CharField(max_length=200, blank=True, null=True)
    mother_phone_number = models.CharField(max_length=20, blank=True, null=True)
    last_alias = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Métadonnées - {self.country}"

    class Meta:
        verbose_name = "Métadonnées Étudiant"
        verbose_name_plural = "Métadonnées Étudiants"


class Student(models.Model):
    """
    Modèle principal pour les étudiants
    """
    matricule = models.CharField(max_length=50, primary_key=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    date_naiss = models.DateField()
    status = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    lang = models.CharField(max_length=50, default='fr')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Relations
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"


class StudentLevel(models.Model):
    """
    Modèle pour associer les étudiants aux niveaux (relation many-to-many avec attributs)
    """
    name = models.CharField(max_length=100)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_levels')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='student_levels')

    def __str__(self):
        return f"{self.student.matricule} - {self.level.name}"

    class Meta:
        verbose_name = "Niveau Étudiant"
        verbose_name_plural = "Niveaux Étudiants"
        unique_together = ['student', 'level']
