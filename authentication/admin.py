from django.contrib import admin

from .models import LoginHistory, TwoFactorChallenge


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "login_at",
        "actor_display",
        "actor_identifier",
        "actor_type",
        "channel",
        "status",
        "ip_address",
        "country",
        "city",
        "device_label",
        "is_known_device",
    )
    list_filter = (
        "status",
        "channel",
        "actor_type",
        "is_known_device",
        "country",
        "browser_family",
        "os_family",
        "device_type",
    )
    search_fields = (
        "actor_identifier",
        "actor_display",
        "ip_address",
        "user_agent",
        "device_fingerprint",
        "session_key",
    )
    readonly_fields = [field.name for field in LoginHistory._meta.fields]
    date_hierarchy = "login_at"
    ordering = ("-login_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser



@admin.register(TwoFactorChallenge)
class TwoFactorChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "purpose",
        "ip_address",
        "attempts",
        "expires_at",
        "consumed_at",
    )
    list_filter = ("purpose", "consumed_at")
    search_fields = ("user__username", "user__email", "token", "ip_address")
    readonly_fields = [field.name for field in TwoFactorChallenge._meta.fields]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
