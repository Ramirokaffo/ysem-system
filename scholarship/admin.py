from django.contrib import admin


from .models import Scholarship, StudentScholarship

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'application_deadline', 'created_at', 'last_updated')
    search_fields = ('name', 'description', 'eligibility_criteria')
    list_filter = ('application_deadline', 'created_at')

@admin.register(StudentScholarship)
class StudentScholarshipAdmin(admin.ModelAdmin):
    list_display = ('student_level', 'scholarship', 'created_at', 'last_updated', 'deleted_at')
    search_fields = ('student_level__level_name', 'scholarship__name')
    list_filter = ('created_at', 'last_updated', 'deleted_at')
    