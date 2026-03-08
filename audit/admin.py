from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "category", "action", "actor_display", "target_model", "target_repr"]
    list_filter = ["category", "action", "actor_type", "target_app_label", "target_model", "created_at"]
    search_fields = ["actor_identifier", "actor_display", "target_object_id", "target_repr", "message"]
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
