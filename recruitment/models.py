from django.db import models

from lecturers.models import Lecturer
from academic.models import Subject
from accounts.models import BaseUser


class LecturerSubject(models.Model):
    """
    Modèle pour les matières enseignées par un enseignant
    """
    STATUS_CHOICES = [
        ('pending', 'En attente de validation'),
        ('validated', 'Validée'),
        ('refused', 'Refusée'),
    ]

    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lecturer_subjects', verbose_name="Enseignant")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lecturer_subjects', verbose_name="Matière")
    practice_experience_years = models.IntegerField(default=0, verbose_name="Années d'expérience dans la pratique de cette discipline")
    teaching_experience_years = models.IntegerField(default=0, verbose_name="Années d'expérience dans l'enseignement de cette discipline")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut de validation de cette matière")
    validated_by = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_subjects', verbose_name="Validée par")
    validated_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")
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
    STATUS_CHOICES = [
        ('pending', 'En attente de validation'),
        ('validated', 'Validée'),
        ('refused', 'Refusée'),
    ]
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lecturer_courses')
    course = models.ForeignKey('academic.Course', on_delete=models.CASCADE, related_name='lecturer_courses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut de validation de ce cours")
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


class LecturerRefusalReason(models.Model):
    """
    Motif de refus d'un dossier de candidature enseignant.

    Un dossier peut être refusé plusieurs fois (après resoumission), d'où la
    relation un-à-plusieurs conservant l'historique des motifs.
    """
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='refusal_reasons')
    reason = models.TextField(verbose_name="Motif de refus")
    can_be_resubmitted = models.BooleanField(default=False, verbose_name="Resoumission autorisée")
    created_by = models.ForeignKey(BaseUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecturer_refusals', verbose_name="Refusé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date du refus")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Motif de refus"
        verbose_name_plural = "Motifs de refus"

    def __str__(self):
        return f"Refus de {self.lecturer.full_name()} le {self.created_at:%d/%m/%Y}"