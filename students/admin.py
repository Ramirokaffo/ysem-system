from django.contrib import admin
from .models import Student, StudentLevel, StudentMetaData


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'firstname', 'lastname', 'status', 'gender', 'school', 'program']
    list_filter = ['status', 'gender', 'school', 'program', 'lang']
    search_fields = ['matricule', 'firstname', 'lastname', 'email']
    date_hierarchy = 'date_naiss'


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    list_display = ['student', 'level', 'name']
    list_filter = ['level']
    search_fields = ['student__matricule', 'student__firstname', 'student__lastname']


@admin.register(StudentMetaData)
class StudentMetaDataAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle StudentMetaData
    """
    list_display = ['country', 'lang', 'residence_city', 'original_region']
    list_filter = ['country', 'lang', 'original_region']
    search_fields = ['country', 'residence_city', 'original_region']
