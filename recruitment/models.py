from django.db import models

from Teaching.models import Lecturer
from academic.models import Subject


# class LecturerSubject(models.Model):
#     """
#     Modèle pour les matières enseignées par un enseignant
#     """
#     lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lecturer_subjects')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lecturer_subjects')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
#     last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

#     class Meta:
#         unique_together = ('lecturer', 'subject')
#         verbose_name = "Matière enseignée"
#         verbose_name_plural = "Matières enseignées"

#     def __str__(self):
#         return f"{self.lecturer.get_full_name()} - {self.subject.name}"

