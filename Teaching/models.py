from django.db import models
from academic.models import Course

# Create your models here.

class Lecturer(models.Model):
    """
    Modèle pour les enseignants
    """
    matricule = models.CharField(max_length=50, primary_key=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    date_naiss = models.DateField()
    grade = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    lang = models.CharField(max_length=50, default='fr')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Relations
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    """godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
"""

    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Enseignants"
        verbose_name_plural = "Enseignants"



class TeachingMonitoring(models.Model):
    """
    Modèle pour le suivi de cours 
    """
    totalChapterCount = models.IntegerField()
    groupWork = models.BooleanField(default=True)
    classWork = models.BooleanField(default=True)
    homeWork = models.BooleanField(default=True)
    pedagogicActivities = models.BooleanField(default=True)
    TDandTP = models.BooleanField(default=True)
    TDandTPContent = models.CharField(max_length=200)
    observation = models.CharField(max_length=200)
    solution = models.CharField(max_length=200)
    generalObservation = models.CharField(max_length=200)

    # Relations
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    """godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
"""

    def __str__(self):
        return f"{self.course_code }"

    class Meta:
        verbose_name = "Suivi_Cours"
        verbose_name_plural = "Suivi_Cours"


class Evaluation(models.Model):
    """
    Modèle pour l'évaluation des enseignants' 
    """
    courseSupportAvailable = models.BooleanField(default=True)
    goodExplanation = models.BooleanField(default=True)
    goodQuestionAnswer = models.BooleanField(default=True)
    courseMethodology = models.CharField(max_length=200)
    giveWork = models.BooleanField(default=True)
    difficulty = models.BooleanField(default=True)
    anyDifficulty = models.BooleanField(default=True)
    difficulties = models.CharField(max_length=200)
    ssacAction = models.CharField(max_length=200)
    ssacObservation = models.CharField(max_length=200)
    studentProposition = models.CharField(max_length=200)


    # Relations
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    """godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
"""

    def __str__(self):
        return f"{self.course_code }"

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

