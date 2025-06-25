from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BaseUser, Godfather


@admin.register(BaseUser)
class BaseUserAdmin(UserAdmin):
    """
    Administration pour le modèle BaseUser étendu
    """
    list_display = UserAdmin.list_display + ('role', 'gender', 'phone_number')
    list_filter = UserAdmin.list_filter + ('role', 'gender', 'is_staff')

    fieldsets = UserAdmin.fieldsets + (
        ('Informations personnelles', {
            'fields': ('phone_number', 'date_of_birth', 'address', 'gender')
        }),
        ('Informations professionnelles', {
            'fields': ('role', )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations personnelles', {
            'fields': ('phone_number', 'date_of_birth', 'address', 'gender')
        }),
        ('Informations professionnelles', {
            'fields': ('role', )
        }),
    )


@admin.register(Godfather)
class GodfatherAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle Godfather
    """
    list_display = ['firstname', 'lastname', 'occupation', 'phone_number', 'email']
    list_filter = ['occupation']
    search_fields = ['firstname', 'lastname', 'email']



