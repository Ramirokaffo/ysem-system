from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import BaseUser, Godfather


@admin.register(BaseUser)
class BaseUserAdmin(UserAdmin):
    """
    Administration pour le modèle BaseUser étendu
    """
    list_display = ['username', 'full_name', 'email', 'role', 'gender', 'is_active', 'date_joined']
    list_filter = ['role', 'gender', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    ordering = ['-date_joined']
    list_per_page = 25
    date_hierarchy = 'date_joined'

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'gender')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Informations professionnelles', {
            'fields': ('role',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address', 'gender')
        }),
        ('Informations professionnelles', {
            'fields': ('role',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ['last_login', 'date_joined']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    full_name.short_description = 'Nom complet'

    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(Godfather)
class GodfatherAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle Godfather (Parrain)
    """
    list_display = ['full_name', 'occupation', 'contact_info', 'created_at']
    list_filter = ['occupation', 'created_at']
    search_fields = ['full_name', 'email', 'phone_number']
    ordering = ['full_name']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('full_name', 'occupation')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Informations système', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'last_updated']

    def contact_info(self, obj):
        contact = []
        if obj.email:
            contact.append(f"📧 {obj.email}")
        if obj.phone_number:
            contact.append(f"📞 {obj.phone_number}")
        return format_html('<br>'.join(contact)) if contact else '-'
    contact_info.short_description = 'Contact'



