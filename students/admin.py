from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Student, StudentLevel, StudentMetaData, OfficialDocument


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Administration des étudiants"""
    list_display = ['matricule', 'full_name', 'status', 'gender', 'school', 'program', 'current_level', 'created_at']
    list_filter = ['status', 'gender', 'school', 'program', 'lang', 'created_at']
    search_fields = ['matricule', 'firstname', 'lastname', 'email', 'phone_number']
    ordering = ['lastname', 'firstname']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'firstname', 'lastname', 'date_naiss', 'gender', 'lang')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number')
        }),
        ('Informations académiques', {
            'fields': ('school', 'program', 'status')
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
    list_display = ['student_info', 'level', 'academic_year', 'is_active']
    list_filter = ['level', 'academic_year', 'is_active']
    search_fields = ['student__matricule', 'student__firstname', 'student__lastname']
    ordering = ['student__lastname', 'student__firstname']
    list_per_page = 25
    list_editable = ['is_active']

    fieldsets = (
        ('Étudiant et niveau', {
            'fields': ('student', 'level', 'academic_year')
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
    list_display = ['id', 'original_country', 'residence_city', 'original_region']
    list_filter = ['original_country', 'original_region']
    search_fields = ['original_country', 'residence_city', 'original_region']
    ordering = ['original_country', 'original_region']
    list_per_page = 25

    fieldsets = (
        ('Informations géographiques', {
            'fields': ('original_country', 'original_region', 'residence_city')
        }),
    )


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
    ordering = ['-created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Étudiant et document', {
            'fields': ('student_level', 'type')
        }),
        ('Statut', {
            'fields': ('status', 'withdrawn_date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
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