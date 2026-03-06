from datetime import datetime

from django.db import models
from students.models import Student
from academic.models import Course, Level, AcademicYear

# Create your models here.

class Lecturer(models.Model):
    """
    Modèle pour les enseignants
    """
    matricule = models.CharField(blank=True, unique=True, primary_key=True, max_length=50, verbose_name="Matricule")
    firstname = models.CharField(blank=True, null=True, max_length=100, verbose_name="Prénom")
    lastname = models.CharField(blank=True, null=True, max_length=100, verbose_name="Nom de famille")
    date_naiss = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    place_of_birth = models.CharField(blank=True, null=True, max_length=100, verbose_name="Lieu de naissance")
    grade = models.CharField(blank=True, null=True, max_length=50, verbose_name="Grade/Titre")
    gender = models.CharField(blank=True, null=True, max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name="Genre")
    lang = models.CharField(blank=True, null=True, max_length=50, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')   
    phone_number = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de téléphone")
    phone_number_2 = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de téléphone secondaire")
    email = models.EmailField(blank=True, null=True, verbose_name="Adresse email")
    nationality = models.CharField(blank=True, null=True, max_length=50, verbose_name="Nationalité")
    number_of_dependent_children = models.IntegerField(blank=True, null=True, verbose_name="Nombre d'enfants à charge")
    marital_status = models.CharField(blank=True, null=True, max_length=20, choices=[('single', 'Célibataire'), ('married', 'Marié(e)'), ('divorced', 'Divorcé(e)'), ('widowed', 'Veuf/Veuve')], verbose_name="Statut marital")
    has_health_problem = models.BooleanField(default=False, verbose_name="Avez-vous des problèmes de santé?")
    health_problem_description = models.TextField(blank=True, null=True, verbose_name="Description des problèmes de santé")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse de résidence")

    nic = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de CNI")
    niu = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro d'Identification Unique")
    
    emergency_contact_name = models.CharField(blank=True, null=True, max_length=100, verbose_name="Contact d'urgence - Nom")
    emergency_contact_phone = models.CharField(blank=True, null=True, max_length=20, verbose_name="Contact d'urgence - Téléphone")
    emergency_contact_email = models.EmailField(blank=True, null=True, verbose_name="Contact d'urgence - Email")
    emergency_contact_relationship = models.CharField(blank=True, null=True, max_length=50, verbose_name="Contact d'urgence - Relation")
    photo = models.ImageField(upload_to='lecturers/photos/', blank=True, null=True, verbose_name="Photo de profil")
    signature = models.ImageField(upload_to='lecturers/signatures/', blank=True, null=True, verbose_name="Signature")

    highest_diploma_obtained = models.CharField(blank=True, null=True, max_length=100, verbose_name="Dernier diplôme obtenu")
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le matricule si ce n'est pas déjà fait
        if not self.matricule:
            self.auto_generate_matricule()
        super().save(*args, **kwargs)

    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    def auto_generate_matricule(self):
        """Génère automatiquement un matricule unique pour l'enseignant"""
        if not self.matricule:
            prefix = "LEC"
            last_lecturer = Lecturer.objects.order_by('-matricule').first()
            if last_lecturer and last_lecturer.matricule.startswith(prefix):
                # Ignorer le préfixe et l'année
                last_number = int(last_lecturer.matricule[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            # Ajouter l'année en cours pour garantir l'unicité
            today = datetime.today()
            self.matricule = f"{prefix}{today.year}{new_number:04d}"

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

