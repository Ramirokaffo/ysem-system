from django.contrib import admin
from django.utils.html import format_html
from .models import Student, StudentLevel, StudentMetaData, OfficialDocument


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Administration des étudiants"""
    list_display = ['matricule', 'full_name', 'status', 'gender', 'school', 'program', 'start_level', 'current_level', 'created_at']
    list_filter = ['status', 'gender', 'school', 'program', 'start_level', 'lang', 'created_at']
    search_fields = ['matricule', 'firstname', 'lastname', 'email', 'phone_number']
    ordering = ['lastname', 'firstname']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'firstname', 'lastname', 'date_naiss', 'gender', 'lang', 'profile_photo', )
        }),
        ('Contact', {
            'fields': ('email', 'phone_number')
        }),
        ('Informations académiques', {
            'fields': ('school', 'program', 'start_level', 'status', 'metadata'),
        }),
        ('Parrain', {
            'fields': ('godfather',),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    def full_name(self, obj):
        return f"{obj.firstname} {obj.lastname}"
    full_name.short_description = 'Nom complet'

    def current_level(self, obj):
        active_level = obj.student_levels.filter(is_active=True).first()
        if active_level:
            return format_html('<strong>{}</strong>', active_level.level.name)
        return '-'
    current_level.short_description = 'Niveau actuel'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school', 'program', 'godfather')


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    """Administration des niveaux d'étudiants"""
    list_display = ['student_info', 'level', 'academic_year', 'speciality', 'is_active']
    list_filter = ['level', 'academic_year', 'speciality', 'is_active']
    search_fields = ['student__matricule', 'student__firstname', 'student__lastname']
    ordering = ['student__lastname', 'student__firstname']
    list_per_page = 25
    list_editable = ['is_active']
    save_on_top = True

    fieldsets = (
        ('Étudiant et niveau', {
            'fields': ('student', 'level', 'academic_year', 'speciality')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
    )

    def student_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            f"{obj.student.firstname} {obj.student.lastname}",
            obj.student.matricule
        )
    student_info.short_description = 'Étudiant'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'level', 'academic_year')


@admin.register(StudentMetaData)
class StudentMetaDataAdmin(admin.ModelAdmin):
    """Administration des métadonnées d'étudiants"""
    list_display = [
        'student', 'original_country',
        'residence_city', 'student_status', 
        'is_complete', 'is_online_registration'
    ]
    list_filter = [
        'original_country', 'original_region', 'is_complete',
        'mother_live_city', 'father_live_city', 'residence_city',
        'is_online_registration'
    ]
    search_fields = [
        'mother_full_name', 'father_full_name', 'mother_email', 'father_email',
        'original_country', 'residence_city', 'original_region', 'original_department',
        'original_district', 'residence_quarter', 'mother_occupation', 'father_occupation'
    ]
    ordering = ['original_country', 'original_region', 'mother_full_name']
    list_per_page = 25

    fieldsets = (
        ('Informations sur la mère', {
            'fields': (
                'mother_full_name', 'mother_live_city', 'mother_email',
                'mother_occupation', 'mother_phone_number'
            )
        }),
        ('Informations sur le père', {
            'fields': (
                'father_full_name', 'father_live_city', 'father_email',
                'father_occupation', 'father_phone_number'
            )
        }),
        ('Informations géographiques', {
            'fields': (
                'original_country', 'original_region', 'original_department',
                'original_district', 'residence_city', 'residence_quarter'
            )
        }),
        ('Statut du dossier', {
            'fields': ('is_complete',)
        }),
        ('Documents d\'inscription', {
            'fields': (
                'preuve_baccalaureat', 'acte_naissance',
                'releve_notes_last_class', 'justificatif_dernier_diplome',
                'bulletins_terminale'
            ),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description="Statut étudiant")
    def student_status(self, obj):
        return obj.student.status if hasattr(obj, 'student') and obj.student else "-"


@admin.register(OfficialDocument)
class OfficialDocumentAdmin(admin.ModelAdmin):
    """Administration des documents officiels"""
    list_display = ['student_info', 'type', 'status', 'withdrawn_date', 'returned_at', 'created_at']
    list_filter = ['type', 'status', 'created_at', 'withdrawn_date', 'returned_at']
    search_fields = [
        'student_level__student__matricule',
        'student_level__student__firstname',
        'student_level__student__lastname',
        'type'
    ]
    ordering = ['-created_at', 'student_level__student__lastname', 'student_level__student__firstname']
    list_per_page = 25
    date_hierarchy = 'created_at'
    save_on_top = True

    fieldsets = (
        ('Étudiant et document', {
            'fields': ('student_level', 'type')
        }),
        ('Statut', {
            'fields': ('status', 'withdrawn_date', 'returned_at')
        }),
        # ('Notes', {
        #     'fields': ('notes',),
        #     'classes': ('collapse',)
        # }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    def student_info(self, obj):
        student = obj.student_level.student
        return format_html(
            '<strong>{}</strong><br><small>{} - {}</small>',
            f"{student.firstname} {student.lastname}",
            student.matricule,
            obj.student_level.level.name
        )
    student_info.short_description = 'Étudiant'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_level__student', 'student_level__level'
        )