from django.urls import path
from . import views

app_name = 'planification'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Salles de classe - Liste et CRUD
    path('salles/', views.ClassroomsView.as_view(), name='classrooms'),
    path('salles/ajouter/', views.ClassroomCreateView.as_view(), name='classroom_create'),
    path('salles/<str:code>/', views.ClassroomDetailView.as_view(), name='classroom_detail'),
    path('salles/<str:code>/modifier/', views.ClassroomUpdateView.as_view(), name='classroom_update'),
    path('salles/<str:code>/supprimer/', views.ClassroomDeleteView.as_view(), name='classroom_delete'),

    # Enseignants - Liste et CRUD
    path('enseignants/', views.LecturersView.as_view(), name='lecturers'),
    path('enseignants/ajouter/', views.LecturerCreateView.as_view(), name='lecturer_create'),
    path('enseignants/<str:matricule>/', views.LecturerDetailView.as_view(), name='lecturer_detail'),
    path('enseignants/<str:matricule>/modifier/', views.LecturerUpdateView.as_view(), name='lecturer_update'),
    path('enseignants/<str:matricule>/supprimer/', views.LecturerDeleteView.as_view(), name='lecturer_delete'),

    # Emplois du temps
    path('emplois-du-temps/', views.SchedulesView.as_view(), name='schedules'),
    path('emplois-du-temps/creer/', views.ScheduleCreateView.as_view(), name='schedule_create'),
    path('emplois-du-temps/<int:pk>/', views.ScheduleDetailView.as_view(), name='schedule_detail'),
    path('emplois-du-temps/<int:pk>/modifier/', views.ScheduleUpdateView.as_view(), name='schedule_update'),
    path('emplois-du-temps/generer/', views.ScheduleGenerateView.as_view(), name='schedule_generate'),

    # Disponibilités des enseignants
    path('disponibilites/', views.LecturerAvailabilitiesView.as_view(), name='lecturer_availabilities'),
    path('disponibilites/ajouter/', views.LecturerAvailabilityCreateView.as_view(), name='lecturer_availability_create'),

    # Créneaux horaires
    # path('creneaux/', views.TimeSlotsView.as_view(), name='time_slots'),
    # path('creneaux/ajouter/', views.TimeSlotCreateView.as_view(), name='time_slot_create'),
    # path('creneaux/<int:pk>/', views.TimeSlotDetailView.as_view(), name='time_slot_detail'),
    # path('creneaux/<int:pk>/modifier/', views.TimeSlotUpdateView.as_view(), name='time_slot_update'),
    # path('creneaux/<int:pk>/supprimer/', views.TimeSlotDeleteView.as_view(), name='time_slot_delete'),
    # path('creneaux/<int:pk>/toggle-active/', views.TimeSlotToggleActiveView.as_view(), name='time_slot_toggle_active'),

    # Séances de cours
    path('seances/', views.SessionsView.as_view(), name='sessions'),
    path('seances/ajouter/', views.CourseSessionCreateView.as_view(), name='session_create'),
    path('seances/<int:pk>/', views.CourseSessionDetailView.as_view(), name='session_detail'),
    path('seances/<int:pk>/modifier/', views.CourseSessionUpdateView.as_view(), name='session_update'),
    path('seances/<int:pk>/supprimer/', views.CourseSessionDeleteView.as_view(), name='session_delete'),

    #cours 
    path('cours/', views.CoursView.as_view(), name='cours'),


]
