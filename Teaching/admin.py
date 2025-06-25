from django.contrib import admin
from .models import Lecturer, TeachingMonitoring, Evaluation
# Register your models here.



@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'firstname', 'lastname', 'date_naiss', 'grade', 'gender', 'lang', 'phone_number','email']
    search_fields = ['firstname']


@admin.register(TeachingMonitoring)
class TeachingMonitoringAdmin(admin.ModelAdmin):
    list_display = ['totalChapterCount', 'groupWork', 'classWork', 'homeWork', 'pedagogicActivities', 'TDandTP', 'TDandTPContent', 'observation', 'solution', 'generalObservation']
    search_fields = ['homeWork']


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['courseSupportAvailable', 'goodExplanation', 'goodQuestionAnswer', 'courseMethodology', 'giveWork', 'difficulty', 'anyDifficulty', 'difficulties', 'ssacAction', 'ssacObservation', 'studentProposition']
    search_fields = ['studentProposition']

