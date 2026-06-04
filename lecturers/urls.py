from django.urls import path

from lecturers import admin_views

from . import views


app_name = 'lecturers'

urlpatterns = [
    path('', views.LecturerLoginView.as_view(), name='login'),
    path('connexion/', views.LecturerLoginView.as_view(), name='login'),
    path('inscription/', views.LecturerSignupView.as_view(), name='signup'),
    path('deconnexion/', views.lecturer_logout, name='logout'),
    path('tableau-de-bord/', views.LecturerDashboardView.as_view(), name='dashboard'),

    path('activer/<str:token>/', views.EmailActivationView.as_view(), name='activate'),
    path('renvoyer-activation/', views.ResendActivationView.as_view(), name='resend_activation'),

    path('mot-de-passe-oublie/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('reinitialiser/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('changer-mot-de-passe/', views.LecturerPasswordChangeView.as_view(), name='password_change'),

    path('home/', admin_views.admin_dashboard, name='home'),
    path('parametres/', admin_views.lecturer_settings, name='settings'),
    path('dossiers/', admin_views.lecturer_dossiers, name='dossiers'),
    path('dossiers/ajouter/', admin_views.lecturer_dossier_create, name='dossier_create'),
    path('dossiers/<str:matricule>/', admin_views.lecturer_dossier_detail, name='dossier_detail'),
    path('dossiers/<str:matricule>/modifier/', admin_views.lecturer_dossier_edit, name='dossier_edit'),
    path('dossiers/<str:matricule>/traiter/', admin_views.lecturer_dossier_process, name='dossier_process'),
    path('dossiers/<str:matricule>/pdf/', admin_views.lecturer_dossier_pdf, name='dossier_pdf'),

]
