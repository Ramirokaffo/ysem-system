from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .document_requirements import (
    DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS,
    PROGRAM_DOCUMENT_FIELD_NAMES,
    PROGRAM_DOCUMENTS_BY_FIELD,
)



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

    # Liste des diplomes
    DIPLOMAS_CHOICES = [
        ('BTS', 'BTS'),
        ('HND', 'HND'),
        ('Licence', 'Licence'),
        ('Master', 'Master'),
        ('Doctorat', 'Doctorat'),
    ]
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    academic_order = models.IntegerField(null=True, blank=False, verbose_name="Numero d'ordre académique")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    # Diplome minimum requis pour enseigner à ce niveau
    minimum_diploma = models.CharField(
        max_length=20,
        choices=DIPLOMAS_CHOICES,
        null=True,
        blank=True,
        verbose_name="Diplôme minimum requis pour enseigner à ce niveau",
        help_text="Le diplôme minimum requis pour un enseignant pour enseigner à ce niveau. Laisser vide si aucun diplôme n'est requis."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"
        ordering = ['academic_order', 'name']


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


class ProgramDocumentRequirement(models.Model):
    """Configuration des documents requis pour un programme."""

    program = models.OneToOneField(
        Program,
        on_delete=models.CASCADE,
        related_name='document_configuration',
        verbose_name='Programme',
    )
    acte_naissance = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['acte_naissance']['label'],
    )
    preuve_baccalaureat = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['preuve_baccalaureat']['label'],
    )
    certificat_nationalite = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['certificat_nationalite']['label'],
    )
    releve_notes_last_class = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['releve_notes_last_class']['label'],
    )
    justificatif_dernier_diplome = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['justificatif_dernier_diplome']['label'],
    )
    decharge_equivalence = models.BooleanField(
        default=False,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['decharge_equivalence']['label'],
    )
    bulletins_terminale = models.BooleanField(
        default=True,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['bulletins_terminale']['label'],
    )
    releve_notes_master1 = models.BooleanField(
        default=False,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['releve_notes_master1']['label'],
    )
    photocopie_bts_hnd = models.BooleanField(
        default=False,
        verbose_name=PROGRAM_DOCUMENTS_BY_FIELD['photocopie_bts_hnd']['label'],
    )
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name='dernière mise à jour')

    @classmethod
    def default_flags(cls):
        return {
            field_name: field_name in DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS
            for field_name in PROGRAM_DOCUMENT_FIELD_NAMES
        }

    @classmethod
    def get_for_program(cls, program):
        if not program:
            return None
        configuration, _ = cls.objects.get_or_create(
            program=program,
            defaults=cls.default_flags(),
        )
        return configuration

    def get_required_document_fields(self):
        return [
            field_name
            for field_name in PROGRAM_DOCUMENT_FIELD_NAMES
            if getattr(self, field_name)
        ]

    def get_required_documents(self):
        return [
            PROGRAM_DOCUMENTS_BY_FIELD[field_name]
            for field_name in self.get_required_document_fields()
        ]

    def __str__(self):
        return f"Documents requis - {self.program.name}"

    class Meta:
        verbose_name = 'Configuration des documents requis'
        verbose_name_plural = 'Configurations des documents requis'



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
    course_code = models.CharField(max_length=20, primary_key=True, verbose_name="Code du cours")
    label = models.CharField(max_length=200, verbose_name="Intitulé du cours")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    credit_count = models.IntegerField(verbose_name="Nombre de crédits")
    speciality = models.ForeignKey(Speciality, on_delete=models.SET_NULL, null=True, related_name='courses', verbose_name="Spécialité")
    subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, related_name='courses', verbose_name="Matière")
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, related_name='courses', verbose_name="Niveau")
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, related_name='courses', verbose_name="Programme")

    def __str__(self):
        return f"{self.course_code} - {self.label}"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"


class Subject(models.Model):
    """
    Modèle pour les matières
    """
    name = models.CharField(max_length=200, verbose_name="Nom de la matière")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    # course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

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
    
    @staticmethod
    def get_active_year():
        return AcademicYear.objects.filter(is_active=True).first()

    class Meta:
        verbose_name = "Année Académique"
        verbose_name_plural = "Années Académiques"
