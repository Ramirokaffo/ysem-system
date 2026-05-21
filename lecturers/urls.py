from django.urls import path

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
]
