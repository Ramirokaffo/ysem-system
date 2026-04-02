from django.db import models

from students.models import StudentLevel



class Scholarship(models.Model):
    """
    Modèle pour les bourses d'études
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    eligibility_criteria = models.TextField(blank=True, null=True)
    application_deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Bourse d'étude"
        verbose_name_plural = "Bourses d'études"


class StudentScholarship(models.Model):
    """
    Modèle pour les bourses d'études associées aux niveaux universitaires des étudiants
    """
    student_level = models.ForeignKey(
        StudentLevel,
        on_delete=models.CASCADE,
        related_name='scholarships',
        blank=True,
        null=True,
        verbose_name="Niveau étudiant",
    )
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, related_name='student_scholarships', blank=True, null=True, verbose_name="Bourse d'étude")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de suppression")