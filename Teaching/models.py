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


    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Enseignants"
        verbose_name_plural = "Enseignants"



class TeachingMonitoring(models.Model):
    """
    Modèle pour le suivi de cours 
    """
    date = models.DateField(null=True)
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200)
    intitule_cours = models.CharField(max_length=200)
    cycle = models.CharField(max_length=200)
    niveau = models.IntegerField()
    totalChapterCount = models.IntegerField(verbose_name="chapitre prevu")
    chapitre_fait = models.IntegerField()
    contenu_seance_prevu = models.IntegerField()
    contenu_effectif_seance = models.IntegerField()
    taux_couverture_seance = models.DecimalField(max_digits = 10, decimal_places= 10)
    travaux_preparatoires = models.BooleanField (default=True)
    groupWork = models.BooleanField(default=True, verbose_name="travaux_equipe")
    classWork = models.BooleanField(default=True, verbose_name="travaux_salle")
    homeWork = models.BooleanField(default=True, verbose_name="travaux_maison")
    pedagogicActivities = models.BooleanField(default=True, verbose_name="activite_pedagogique")
    TDandTP = models.BooleanField(default=True, verbose_name= "TD et TP")
    projet_fin_cours = models.CharField(max_length=200)
    association_pratique_aux_enseigements = models.CharField(max_length=200)
    observation = models.CharField(max_length=200)
    solution = models.CharField(max_length=200, verbose_name="resolution")
    generalObservation = models.CharField(max_length=200, verbose_name="observation generale")


    def taux_couverture_seance(self):
        if self.contenu_seance_prevu == 0:
         return 0
        return round((self.contenu_effectif_seance / self.contenu_seance_prevu) * 100, 1)
    def couleur_barre(self):
        if self.taux_couverture_seance() < 50:
         return "bg-danger"
        elif self.taux_couverture_seance() < 80:
            return "bg-warning"
        return "bg-success"
    def statut_avancement(self):
        if self.contenu_effectif_seance == 0:
            return 'retard'
        elif self.contenu_effectif_seance < self.contenu_seance_prevu:
            return 'en_cours'
        else:
            return 'termine'
    def couleur_barre(self):
        statut = self.statut_avancement()
        return {
            'retard': 'bg-danger',
            'en_cours': 'bg-primary',
            'termine': 'bg-success'
        }.get(statut, 'bg-secondary')

    class Meta:
        verbose_name = "Suivi_Cours"
        verbose_name_plural = "Suivi_Cours"


class Evaluation(models.Model):
    """
    Modèle pour l'évaluation des enseignants' 
    """
    evaluationDat = models.DateField(null=True, verbose_name="date")
    nom_et_prenom_etudiant = models.CharField(max_length=200)
    cycle = models.CharField(max_length=200)
    niveau = models.IntegerField(default="")
    intitule_cours = models.CharField(max_length=200)
    support_cours_acessible = models.BooleanField(default=True)
    bonne_explication_cours = models.BooleanField(default=True)
    bonne_reponse_questions = models.BooleanField(default=True)
    courseMethodology = models.CharField(max_length=200, verbose_name= "methodologie_cours", default="")
    donne_TD = models.BooleanField(default=True)
    donne_projet = models.BooleanField(default=True)
    difficulte_rencontree = models.BooleanField(default=True)
    quelles_difficultes_rencontrees = models.CharField(max_length=200, default="")
    propositionEtudiants = models.CharField(max_length=200, default="")
    observationSSAC = models.CharField(max_length=200, default="")
    actionSSAC = models.CharField(max_length=200)
   
    


    # def __str__(self):
    #     return f"{self.nom_et_prenom_etudiant }"

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

