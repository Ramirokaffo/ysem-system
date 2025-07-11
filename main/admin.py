from django.contrib import admin
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Administration des paramètres système
    """
    list_display = ['institution_name', 'institution_code', 'language', 'timezone', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('institution_name', 'institution_code', 'address', 'phone', 'email', 'website', 'timezone', 'language')
        }),
        ('Paramètres académiques', {
            'fields': ('inscription_period', 'auto_approval', 'require_documents', 'allow_external_registration')
        }),
        ('Programmes et niveaux', {
            'fields': ('auto_level_progression', 'allow_level_change', 'require_level_validation',
                      'allow_program_change', 'require_program_validation')
        }),
        ('Utilisateurs', {
            'fields': ('default_role', 'session_timeout', 'view_documents', 'download_docs',
                      'update_profile', 'view_statistics')
        }),
        ('Documents', {
            'fields': ('max_file_size', 'allowed_formats', 'student_card_enabled', 'transcript_enabled',
                      'certificate_enabled', 'diploma_enabled', 'require_original_docs')
        }),
        ('Notifications', {
            'fields': ('email_enrollment', 'email_documents', 'email_deadlines', 'system_errors', 'system_updates')
        }),
        ('Gestion des données', {
            'fields': ('backup_frequency', 'data_retention', 'audit_log', 'data_encryption', 'auto_cleanup')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Empêcher la création de multiples instances
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression des paramètres système
        return False
