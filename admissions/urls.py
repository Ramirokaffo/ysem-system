from django.urls import path

from . import views
from . import preinscription_views

app_name = 'admissions'

urlpatterns = [
    path('', views.AdmissionLoginView.as_view(), name='login'),
    path('connexion/', views.AdmissionLoginView.as_view(), name='login'),
    path('inscription/', views.AdmissionSignupView.as_view(), name='signup'),
    path('deconnexion/', views.admission_logout, name='logout'),
    path('tableau-de-bord/', views.AdmissionDashboardView.as_view(), name='dashboard'),

    path('activer/<str:token>/', views.EmailActivationView.as_view(), name='activate'),
    path('renvoyer-activation/', views.ResendActivationView.as_view(), name='resend_activation'),

    path('mot-de-passe-oublie/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('reinitialiser/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('mon-compte/changer-mot-de-passe/', views.ChangePasswordView.as_view(), name='change_password'),

    path('preinscription/etape/<int:step>/',
         preinscription_views.PreinscriptionStepView.as_view(),
         name='preinscription_step'),
    path('preinscription/recapitulatif/',
         preinscription_views.PreinscriptionReviewView.as_view(),
         name='preinscription_review'),
    path('preinscription/recap/',
         preinscription_views.PreinscriptionRecapView.as_view(),
         name='preinscription_recap'),
    path('preinscription/specialites/',
         preinscription_views.preinscription_specialities,
         name='preinscription_specialities'),
]
