from django.contrib import admin
from .models import Student, StudentLevel, StudentMetaData, OfficialDocument


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

@admin.register(OfficialDocument)
class OfficialDocumentAdmin(admin.ModelAdmin):
    """
    Administration pour le modèle OfficialDocument
    """
    list_display = ['student_level__name', 'type', 'status', 'withdrawn_date', 'created_at', 'last_updated']
    list_filter = ['type', 'status', 'created_at', 'withdrawn_date']
    search_fields = [
        'student_level__student__matricule',
        'student_level__student__firstname',
        'student_level__student__lastname',
        'type'
    ]

    # def student_level_name(self, obj):
    #     return getattr(getattr(obj.student, 'level', None), 'name', None)
    # student_level_name.admin_order_field = 'student__level__name'
    # student_level_name.short_description = 'Student Level Name'