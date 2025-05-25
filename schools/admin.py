from django.contrib import admin
from .models import School, UniversityLevel, SecondaryDiploma


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'phone_number']
    list_filter = ['level']
    search_fields = ['name', 'address']


@admin.register(UniversityLevel)
class UniversityLevelAdmin(admin.ModelAdmin):
    list_display = ['level_name', 'diploma_name', 'speciality', 'academic_year']
    list_filter = ['academic_year', 'speciality']
    search_fields = ['level_name', 'diploma_name']


@admin.register(SecondaryDiploma)
class SecondaryDiplomaAdmin(admin.ModelAdmin):
    list_display = ['name', 'serie', 'obtained_year', 'mention']
    list_filter = ['obtained_year', 'serie', 'mention']
    search_fields = ['name']
