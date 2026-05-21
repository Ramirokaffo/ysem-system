from django.contrib import admin
from django.utils.html import format_html
from .models import TeachingMonitoring, Evaluation

@admin.register(TeachingMonitoring)
class TeachingMonitoringAdmin(admin.ModelAdmin):
    """Administration du suivi pédagogique"""
    list_display = ['id', 'totalChapterCount', 'groupWork', 'classWork', 'homeWork']
    search_fields = ['homeWork', 'observation', 'generalObservation']
    list_per_page = 25

    fieldsets = (
        ('Activités pédagogiques', {
            'fields': ('totalChapterCount', 'groupWork', 'classWork', 'homeWork', 'pedagogicActivities', 'TDandTP')
        }),
        ('Observations', {
            'fields': ('observation', 'solution', 'generalObservation')
        }),
    )


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Administration des évaluations"""
    list_display = ['id', 'evaluationDat', 'student', 'course', 'level', 'academic_year']
    list_filter = ['level', 'academic_year', 'course', 'support_cours_acessible', 'bonne_explication_cours']
    search_fields = ['student__firstname', 'student__lastname', 'student__matricule', 'course__label']
    list_per_page = 25
    raw_id_fields = ['student', 'course']

    fieldsets = (
        ('Informations générales', {
            'fields': ('evaluationDat', 'academic_year')
        }),
        ('Étudiant et cours', {
            'fields': ('student', 'course', 'level')
        }),
        ('Évaluation du cours', {
            'fields': ('support_cours_acessible', 'bonne_explication_cours', 'bonne_reponse_questions', 'donne_TD', 'donne_projet', 'courseMethodology')
        }),
        ('Difficultés', {
            'fields': ('difficulte_rencontree', 'quelles_difficultes_rencontrees')
        }),
        ('Observations et actions', {
            'fields': ('propositionEtudiants', 'observationSSAC', 'actionSSAC')
        }),
    )

