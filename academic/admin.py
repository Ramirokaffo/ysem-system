from django.contrib import admin
from .models import Speciality, Department, Level, Course, Program, AcademicYear


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'method_type']
    search_fields = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'speciality', 'method_type']
    list_filter = ['speciality']
    search_fields = ['label']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'method_type']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'label', 'credit_count', 'level']
    list_filter = ['level', 'credit_count']
    search_fields = ['course_code', 'label']


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'method_type']
    search_fields = ['label']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['id', 'start_at', 'end_at', 'method_type']
    list_filter = ['start_at', 'end_at']
