from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Classroom, TimeSlot, CourseSession, Schedule,
    LecturerAvailability, ScheduleSession, Equipment, Building, Floor
)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    """Administration des salles de classe"""
    list_display = ['code', 'name', 'capacity', 'building', 'floor', 'is_active', 'created_at']
    list_filter = ['is_active', 'building', 'floor', 'created_at']
    search_fields = ['code', 'name', 'building']
    ordering = ['building', 'floor', 'code']
    list_editable = ['is_active']
    list_per_page = 25

    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'name', 'capacity', )
        }),
        ('Localisation', {
            'fields': ('building', 'floor', )
        }),
        ('Équipements', {
            'fields': ('equipment', ),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """Administration des équipement
    """
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
    ordering = ['code', 'name']
    list_per_page = 25

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """Administration des batiments
    """
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
    ordering = ['code']
    list_per_page = 25

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    """Administration des etages
    """
    list_display = ['number', 'name']
    search_fields = ['number', 'name']
    ordering = ['number']
    list_per_page = 25
    


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Administration des créneaux horaires"""
    list_display = ['name', 'day_of_week_display', 'time_range', 'duration_display', 'is_active', 'usage_count']
    list_filter = ['day_of_week', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['day_of_week', 'start_time']
    list_editable = ['is_active']
    list_per_page = 25

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'day_of_week')
        }),
        ('Horaires', {
            'fields': ('start_time', 'end_time')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
    )

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'Jour'

    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = 'Horaires'

    def duration_display(self, obj):
        return f"{obj.duration_hours()}h"
    duration_display.short_description = 'Durée'

    def usage_count(self, obj):
        sessions_count = obj.sessions.count()
        availabilities_count = obj.lecturer_availabilities.count()
        return format_html(
            '<span title="Séances: {} | Disponibilités: {}">{} utilisations</span>',
            sessions_count, availabilities_count, sessions_count + availabilities_count
        )
    usage_count.short_description = 'Utilisation'


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    """Administration des séances de cours"""
    list_display = ['course', 'lecturer', 'classroom', 'time_slot', 'date', 'session_type', 'status']
    list_filter = ['session_type', 'status', 'date', 'academic_year', 'level']
    search_fields = ['course__label', 'lecturer__firstname', 'lecturer__lastname', 'classroom__name']
    ordering = ['-date', 'time_slot__start_time']
    list_per_page = 25
    date_hierarchy = 'date'

    fieldsets = (
        ('Cours', {
            'fields': ('course', 'lecturer', 'level', 'academic_year')
        }),
        ('Planification', {
            'fields': ('classroom', 'time_slot', 'date')
        }),
        ('Détails', {
            'fields': ('session_type', 'topic', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'lecturer', 'classroom', 'time_slot', 'level', 'academic_year'
        )


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """Administration des emplois du temps"""
    list_display = ['name', 'level', 'academic_year', 'period_display', 'status', 'is_generated', 'sessions_count']
    list_filter = ['status', 'is_generated', 'duration_type', 'academic_year', 'level']
    search_fields = ['name', 'description', 'level__name']
    ordering = ['-created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Paramètres académiques', {
            'fields': ('academic_year', 'level')
        }),
        ('Période', {
            'fields': ('start_date', 'end_date', 'duration_type')
        }),
        ('Statut', {
            'fields': ('status', 'is_generated')
        }),
    )

    readonly_fields = ['is_generated']

    def period_display(self, obj):
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
    period_display.short_description = 'Période'

    def sessions_count(self, obj):
        count = obj.get_total_sessions()
        if count > 0:
            url = reverse('admin:planification_schedulesession_changelist')
            return format_html(
                '<a href="{}?schedule__id__exact={}">{} séances</a>',
                url, obj.pk, count
            )
        return "0 séance"
    sessions_count.short_description = 'Séances'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('academic_year', 'level')


@admin.register(LecturerAvailability)
class LecturerAvailabilityAdmin(admin.ModelAdmin):
    """Administration des disponibilités des enseignants"""
    list_display = ['lecturer', 'time_slot_display', 'academic_year', 'status', 'period_display']
    list_filter = ['status', 'academic_year', 'time_slot__day_of_week']
    search_fields = ['lecturer__firstname', 'lecturer__lastname', 'lecturer__matricule']
    ordering = ['lecturer__lastname', 'time_slot__day_of_week', 'time_slot__start_time']
    list_per_page = 25

    fieldsets = (
        ('Enseignant et créneau', {
            'fields': ('lecturer', 'time_slot', 'academic_year')
        }),
        ('Disponibilité', {
            'fields': ('status',)
        }),
        ('Période spécifique', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
            'description': 'Laissez vide pour appliquer à toute l\'année académique'
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def time_slot_display(self, obj):
        return f"{obj.time_slot.get_day_of_week_display()} {obj.time_slot.start_time.strftime('%H:%M')}-{obj.time_slot.end_time.strftime('%H:%M')}"
    time_slot_display.short_description = 'Créneau'

    def period_display(self, obj):
        if obj.start_date and obj.end_date:
            return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
        return "Toute l'année"
    period_display.short_description = 'Période'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lecturer', 'time_slot', 'academic_year'
        )


@admin.register(ScheduleSession)
class ScheduleSessionAdmin(admin.ModelAdmin):
    """Administration des séances d'emploi du temps"""
    list_display = ['schedule', 'course_session_display', 'week_number', 'is_recurring']
    list_filter = ['is_recurring', 'schedule__academic_year', 'schedule__level', 'week_number']
    search_fields = ['schedule__name', 'course_session__course__label']
    ordering = ['schedule', 'week_number', 'course_session__time_slot__day_of_week']
    list_per_page = 25

    fieldsets = (
        ('Emploi du temps', {
            'fields': ('schedule',)
        }),
        ('Séance', {
            'fields': ('course_session', 'week_number', 'is_recurring')
        }),
    )

    def course_session_display(self, obj):
        session = obj.course_session
        return format_html(
            '<strong>{}</strong><br>'
            '<small>{} - {} - {}</small>',
            session.course.label,
            session.lecturer.get_full_name(),
            session.classroom.name,
            f"{session.time_slot.get_day_of_week_display()} {session.time_slot.start_time.strftime('%H:%M')}"
        )
    course_session_display.short_description = 'Séance de cours'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'schedule', 'course_session__course', 'course_session__lecturer',
            'course_session__classroom', 'course_session__time_slot'
        )



