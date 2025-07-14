from django.contrib import admin
from django.utils.html import format_html
from .models import Lecturer, TeachingMonitoring, Evaluation


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    """Administration des enseignants"""
    list_display = ['matricule', 'full_name', 'grade', 'gender', 'contact_info', 'lang']
    list_filter = ['grade', 'gender', 'lang']
    search_fields = ['matricule', 'firstname', 'lastname', 'email', 'phone_number']
    ordering = ['lastname', 'firstname']
    list_per_page = 25

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'firstname', 'lastname', 'date_naiss', 'gender')
        }),
        ('Informations professionnelles', {
            'fields': ('grade', 'lang')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'address')
        }),
    )

    def full_name(self, obj):
        return f"{obj.firstname} {obj.lastname}"
    full_name.short_description = 'Nom complet'

    def contact_info(self, obj):
        contact = []
        if obj.email:
            contact.append(f"📧 {obj.email}")
        if obj.phone_number:
            contact.append(f"📞 {obj.phone_number}")
        return format_html('<br>'.join(contact)) if contact else '-'
    contact_info.short_description = 'Contact'


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
    list_display = ['id', 'nom_et_prenom_etudiant', 'cycle', 'niveau', 'intitule_cours']
    list_filter = ['cycle', 'niveau', 'support_cours_acessible', 'bonne_explication_cours']
    search_fields = ['nom_et_prenom_etudiant', 'intitule_cours', 'propositionEtudiants']
    list_per_page = 25

    fieldsets = (
        ('Étudiant et cours', {
            'fields': ('nom_et_prenom_etudiant', 'cycle', 'niveau', 'intitule_cours')
        }),
        ('Évaluation du cours', {
            'fields': ('support_cours_acessible', 'bonne_explication_cours', 'bonne_reponse_questions', 'donne_TD', 'donne_projet')
        }),
        ('Difficultés', {
            'fields': ('difficulte_rencontree', 'quelles_difficultes_rencontrees')
        }),
        ('Observations et actions', {
            'fields': ('propositionEtudiants', 'observationSSAC', 'actionSSAC')
        }),
    )

