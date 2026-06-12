from django.contrib import admin

from .models import LecturerSubject, LecturerCourse, LecturerRefusalReason

@admin.register(LecturerSubject)
class LecturerSubjectAdmin(admin.ModelAdmin):
    """Administration des matières enseignées par les enseignants"""
    list_display = ['lecturer', 'subject', 'practice_experience_years', 'teaching_experience_years', 'created_at']
    search_fields = ['lecturer__firstname', 'lecturer__lastname', 'subject__name']
    list_per_page = 25
    # raw_id_fields = ['lecturer', 'subject']

@admin.register(LecturerCourse)
class LecturerCourseAdmin(admin.ModelAdmin):
    """Administration des cours enseignés par les enseignants"""
    list_display = ['lecturer', 'course', 'status', 'validated_by', 'validated_at', 'created_at']
    list_filter = ['status']
    search_fields = ['lecturer__firstname', 'lecturer__lastname', 'course__label']
    list_per_page = 25
    # raw_id_fields = ['lecturer', 'course', 'validated_by']

@admin.register(LecturerRefusalReason)
class LecturerRefusalReasonAdmin(admin.ModelAdmin):
    """Administration des motifs de refus de candidature des enseignants"""
    list_display = ['lecturer', 'reason', 'created_at']
    search_fields = ['lecturer__firstname', 'lecturer__lastname', 'reason']
    list_per_page = 25
    # raw_id_fields = ['lecturer']