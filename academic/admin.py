from django.contrib import admin
from django.utils.html import format_html

from payments.models import PaymentInstallment
from .models import Speciality, Department, Level, Course, Program, AcademicYear, ProgramDocumentRequirement, Subject


class ProgramDocumentRequirementInline(admin.StackedInline):
    model = ProgramDocumentRequirement
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = 'Documents requis pour ce programme'
    fields = (
        'acte_naissance',
        'preuve_baccalaureat',
        'certificat_nationalite',
        'releve_notes_last_class',
        'justificatif_dernier_diplome',
        'decharge_equivalence',
        'bulletins_terminale',
        'releve_notes_master1',
        'photocopie_bts_hnd',
    )


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    """Administration des spécialités"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'program'),
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    # def departments_count(self, obj):
    #     count = obj.departments.count()
    #     if count > 0:
    #         return format_html('<strong>{}</strong> département{}', count, 's' if count > 1 else '')
    #     return '0 département'
    # departments_count.short_description = 'Départements'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Administration des départements"""
    list_display = ['label', 'created_at']
    list_filter = ['created_at']
    search_fields = ['label', 'description']
    ordering = ['label']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('label', 'description')
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    """Administration des niveaux"""
    list_display = ['name', 'courses_count', "academic_order", 'minimum_diploma', 'created_at']
    search_fields = ['name']
    ordering = ['academic_order', 'name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True
    list_filter = ['minimum_diploma']

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'academic_order', 'minimum_diploma')
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    def courses_count(self, obj):
        count = obj.courses.count()
        if count > 0:
            return format_html('<strong>{}</strong> cours', count)
        return '0 cours'
    courses_count.short_description = 'Cours'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Administration des matières"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Administration des cours"""
    list_display = ['course_code', 'label', 'subject', 'program', 'credit_count', 'level', 'created_at']
    list_filter = ['level', 'subject', 'program', 'credit_count', 'created_at']
    search_fields = ['course_code', 'label', 'level__name']
    ordering = ['level__name', 'course_code']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('course_code', 'label', 'level', 'subject', 'program', 'description')
        }),
        ('Crédits', {
            'fields': ('credit_count',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']


class PaymentInstallmentInline(admin.TabularInline):
    model = PaymentInstallment
    # extra = 0
    fields = ('name', 'academic_year', 'program', 'level', 'order_number', 'amount', 'due_date')
    readonly_fields = ('created_at', 'updated_at')
    can_delete = True
    show_change_link = True
    verbose_name_plural = 'Tranches de paiement'


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """Administration des programmes"""
    
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('name',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']
    inlines = [ProgramDocumentRequirementInline, PaymentInstallmentInline]


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Administration des années académiques"""
    list_display = ['name_display', 'period_display', 'is_active', 'duration_days']
    list_filter = ['is_active', 'start_at', 'end_at']
    search_fields = ['start_at', 'end_at']
    ordering = ['-start_at']
    list_per_page = 25
    list_editable = ['is_active']
    save_on_top = True
    inlines = [PaymentInstallmentInline]


    fieldsets = (
        ('Période académique', {
            'fields': ('start_at', 'end_at')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    def name_display(self, obj):
        return f"{obj.start_at.year}/{obj.end_at.year}"
    name_display.short_description = 'Année académique'

    def period_display(self, obj):
        return f"{obj.start_at.strftime('%d/%m/%Y')} - {obj.end_at.strftime('%d/%m/%Y')}"
    period_display.short_description = 'Période'

    def duration_days(self, obj):
        duration = (obj.end_at - obj.start_at).days
        return f"{duration} jours"
    duration_days.short_description = 'Durée'
