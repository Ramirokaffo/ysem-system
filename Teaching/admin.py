from django.contrib import admin
from .models import Lecturer, TeachingMonitoring, Evaluation
# Register your models here.



@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'firstname', 'lastname', 'date_naiss', 'grade', 'gender', 'lang', 'phone_number','email']
    search_fields = ['firstname']


@admin.register(TeachingMonitoring)
class TeachingMonitoringAdmin(admin.ModelAdmin):
    list_display = ['totalChapterCount', 'groupWork', 'classWork', 'homeWork', 'pedagogicActivities', 'TDandTP', 'observation', 'solution', 'generalObservation']
    search_fields = ['homeWork']


# @admin.register(Evaluation)
# class EvaluationAdmin(admin.ModelAdmin):
#     list_display = [
#         # 'evaluationDat', 
#                     'nom_et_prenom_etudiant', 'cycle', 'niveau', 'intitule_cours', 'support_cours_acessible', 'bonne_explication_cours', 'bonne_reponse_questions', 'donne_TD', 'donne_projet', 'difficulte_rencontree', 'quelles_difficultes_rencontrees', 'propositionEtudiants', 'observationSSAC', 'actionSSAC']
#     search_fields = ['propositionEtudiants']

