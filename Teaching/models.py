from django.db import models
from students.models import Student
from academic.models import Course, Level, AcademicYear

# Create your models here.

class Lecturer(models.Model):
    """
    Modèle pour les enseignants
    """
    matricule = models.CharField(max_length=50, primary_key=True, verbose_name="Matricule")
    firstname = models.CharField(max_length=100, verbose_name="Prénom")
    lastname = models.CharField(max_length=100, verbose_name="Nom de famille")
    date_naiss = models.DateField(verbose_name="Date de naissance")
    grade = models.CharField(max_length=50, verbose_name="Grade/Titre")
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name="Genre")
    lang = models.CharField(max_length=50, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')   
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Adresse email")

    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ['lastname', 'firstname']



class TeachingMonitoring(models.Model):
    """
    Modèle pour le suivi de cours
    """
    date = models.DateField(null=True, verbose_name="Date")

    # Relations avec les autres modèles
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='teaching_monitorings', verbose_name="Enseignant")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='teaching_monitorings', verbose_name="Cours")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='teaching_monitorings', verbose_name="Niveau")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teaching_monitorings', verbose_name="Année académique")
    cycle = models.CharField(max_length=200, blank=True, verbose_name="Projet fin de cours")

    # Champs de suivi
    totalChapterCount = models.IntegerField(verbose_name="Chapitres prévus")
    chapitre_fait = models.IntegerField(verbose_name="Chapitres faits")
    contenu_seance_prevu = models.IntegerField(verbose_name="Contenu séance prévu dans le plan")
    contenu_effectif_seance = models.IntegerField(verbose_name="Contenu effectif séance dans le cahier de texte")

    # Champs booléens pour les activités
    travaux_preparatoires = models.BooleanField(default=True, verbose_name="Travaux préparatoires")
    groupWork = models.BooleanField(default=True, verbose_name="Travaux en équipe")
    classWork = models.BooleanField(default=True, verbose_name="Travaux en salle")
    homeWork = models.BooleanField(default=True, verbose_name="Travaux maison")
    pedagogicActivities = models.BooleanField(default=True, verbose_name="Activités pédagogiques")
    TDandTP = models.BooleanField(default=True, verbose_name="TD et TP")

    # Champs texte pour observations
    projet_fin_cours = models.CharField(max_length=200, blank=True, verbose_name="Projet fin de cours")
    association_pratique_aux_enseigements = models.CharField(max_length=200, blank=True, verbose_name="Association pratique aux enseignements")
    observation = models.CharField(max_length=200, blank=True, verbose_name="Observation")
    solution = models.CharField(max_length=200, blank=True, verbose_name="Résolution")
    generalObservation = models.CharField(max_length=200, blank=True, verbose_name="Observation générale")


    def taux_couverture_seance(self):
        """Calcule le taux de couverture de la séance en pourcentage"""
        if self.contenu_seance_prevu == 0:
            return 0
        return round((self.contenu_effectif_seance / self.contenu_seance_prevu) * 100, 1)

    def taux_couverture_chapitre(self):
        """Calcule le taux de couverture des chapitres en pourcentage"""
        if self.totalChapterCount == 0:
            return 0
        return round((self.chapitre_fait / self.totalChapterCount) * 100, 1)

    def statut_avancement(self):
        """Détermine le statut d'avancement du cours"""
        if self.contenu_effectif_seance == 0:
            return 'retard'
        elif self.contenu_effectif_seance < self.contenu_seance_prevu:
            return 'en_cours'
        else:
            return 'termine'

    def couleur_barre(self):
        """Retourne la classe CSS pour la couleur de la barre de progression"""
        statut = self.statut_avancement()
        return {
            'retard': 'bg-danger',
            'en_cours': 'bg-warning',
            'termine': 'bg-success'
        }.get(statut, 'bg-secondary')

    def __str__(self):
        return f"{self.lecturer} - {self.course} ({self.level}) - {self.date}"

    class Meta:
        verbose_name = "Suivi de cours"
        verbose_name_plural = "Suivi des cours"
        ordering = ['-date', 'lecturer__lastname', 'lecturer__firstname']


class Evaluation(models.Model):
    """
    Modèle pour l'évaluation des enseignants'
    """
    evaluationDat = models.DateField(null=True, verbose_name="Date d'évaluation")

    # Relations avec les autres modèles
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='evaluations', verbose_name="Étudiant")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='evaluations', verbose_name="Cours")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='evaluations', verbose_name="Niveau")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='evaluations', verbose_name="Année académique")

    # Champs d'évaluation
    support_cours_acessible = models.BooleanField(default=True, verbose_name="Support de cours accessible")
    bonne_explication_cours = models.BooleanField(default=True, verbose_name="Bonne explication du cours")
    bonne_reponse_questions = models.BooleanField(default=True, verbose_name="Bonne réponse aux questions")
    courseMethodology = models.CharField(max_length=200, verbose_name="Méthodologie du cours", default="", blank=True)
    donne_TD = models.BooleanField(default=True, verbose_name="Donne des TD")
    donne_projet = models.BooleanField(default=True, verbose_name="Donne des projets")
    difficulte_rencontree = models.BooleanField(default=False, verbose_name="Difficultés rencontrées")

    # Champs de commentaires
    quelles_difficultes_rencontrees = models.TextField(blank=True, verbose_name="Quelles difficultés rencontrées")
    propositionEtudiants = models.TextField(blank=True, verbose_name="Propositions des étudiants")
    observationSSAC = models.TextField(blank=True, verbose_name="Observation SSAC")
    actionSSAC = models.TextField(verbose_name="Action SSAC")
   

    def __str__(self):
        return f"Évaluation de {self.student} - {self.course} ({self.academic_year})"

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-evaluationDat', 'student__lastname', 'student__firstname']

