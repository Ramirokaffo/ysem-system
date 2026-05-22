from django.db import models

from lecturers.models import Lecturer
from academic.models import Subject
from accounts.models import BaseUser


class LecturerSubject(models.Model):
    """
    Modèle pour les matières enseignées par un enseignant
    """
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lecturer_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lecturer_subjects')
    practice_experience_years = models.IntegerField(default=0, verbose_name="Années d'expérience dans la pratique de cette discipline")
    teaching_experience_years = models.IntegerField(default=0, verbose_name="Années d'expérience dans l'enseignement de cette discipline")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    proof_document = models.FileField(upload_to='lecturers/subjects/proofs/', blank=True, null=True, verbose_name="Justificatif ou preuve d'expérience")

    class Meta:
        unique_together = ('lecturer', 'subject')
        verbose_name = "Matière enseignée"
        verbose_name_plural = "Matières enseignées"

    def __str__(self):
        return f"{self.lecturer.full_name()} - {self.subject.name}"


class LecturerCourse(models.Model):
    """
    Modèle pour les cours enseignés par un enseignant
    """
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lecturer_courses')
    course = models.ForeignKey('academic.Course', on_delete=models.CASCADE, related_name='lecturer_courses')
    is_validated = models.BooleanField(default=False, verbose_name="Validé pour enseigner ce cours")
    validated_by = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_courses', verbose_name="Validé par")
    validated_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    class Meta:
        unique_together = ('lecturer', 'course')
        verbose_name = "Cours enseigné"
        verbose_name_plural = "Cours enseignés"

    def __str__(self):
        return f"{self.lecturer.full_name()} - {self.course.label}"