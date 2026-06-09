from django.contrib import admin

from .models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'success_count', 'failure_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('subject', 'recipients', 'body')
    readonly_fields = (
        'subject', 'body', 'recipients', 'sender',
        'success_count', 'failure_count', 'created_at',
    )

    def has_add_permission(self, request):
        return False
