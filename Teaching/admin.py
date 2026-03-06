from django.contrib import admin
from django.utils.html import format_html
from .models import Lecturer, TeachingMonitoring, Evaluation


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    """Administration des enseignants"""
    list_display = ['matricule', 'full_name', 'grade', 'gender', 'contact_info', 'lang', 'marital_status', 'has_health_problem']
    list_filter = ['grade', 'gender', 'lang', 'marital_status', 'has_health_problem']
    search_fields = ['matricule', 'firstname', 'lastname', 'email', 'phone_number']
    ordering = ['lastname', 'firstname']
    list_per_page = 25

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('firstname', 'lastname', 'date_naiss', 'place_of_birth', 'gender', 'address', 'photo', 'signature'),
        }),
        ('Informations professionnelles', {
            'fields': ('grade', 'lang', 'marital_status', 'has_health_problem', 'health_problem_description')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'phone_number_2')
        }),
        ('Informations complémentaires', {
            'fields': ('nic', 'niu', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email', 'emergency_contact_relationship'),
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

