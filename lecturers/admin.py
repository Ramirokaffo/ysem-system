from django.contrib import admin
from django.utils.html import format_html

from lecturers.models import Lecturer


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
            'fields': ('grade', 'lang', 'marital_status', 'has_health_problem', 'health_problem_description',  'favorite_subjects')
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


