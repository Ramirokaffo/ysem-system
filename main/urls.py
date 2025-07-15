from django.urls import path
from . import views
from django.conf import settings
from django.views.generic.base import RedirectView
from django.urls import re_path
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

app_name = 'main'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('scholar', views.DashboardView.as_view(), name='dashboard'),
    path('inscriptions/', views.InscriptionsView.as_view(), name='inscriptions'),
    path('inscription/<str:pk>/', views.inscription_detail, name='inscription_detail'),
    path('inscription/<str:pk>/approuver/', views.inscription_approve, name='inscription_approve'),
    path('inscription/<str:pk>/rejeter/', views.inscription_reject, name='inscription_reject'),
    path('etudiants/', views.EtudiantsView.as_view(), name='etudiants'),
    path('documents/', views.DocumentsView.as_view(), name='documents'),
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
    path('parametres/', views.ParametresView.as_view(), name='parametres'),
    path('profil/', views.ProfilView.as_view(), name='profil'),
    path('etudiant/<str:pk>/', views.etudiant_detail, name='etudiant_detail'),
    path('etudiant/<str:pk>/modifier/', views.etudiant_edit, name='etudiant_edit'),
    path('etudiant/<str:pk>/generer-mot-de-passe/', views.generate_student_external_password, name='generate_student_external_password'),

    # Gestion des documents officiels
    path('document/nouveau/', views.document_create, name='document_create'),
    path('document/<int:pk>/modifier/', views.document_edit, name='document_edit'),
    path('document/<int:pk>/supprimer/', views.document_delete, name='document_delete'),
    path('document/<int:pk>/toggle-status/', views.document_toggle_status, name='document_toggle_status'),
    path('document/creation-masse/', views.document_bulk_create, name='document_bulk_create'),
    path('document/preview-masse/', views.document_bulk_preview, name='document_bulk_preview'),

    # Formulaire d'inscription public
    path('inscription-externe/', views.InscriptionExterneView.as_view(), name='inscription_externe'),
    path('inscription-externe/etape/<int:step>/', views.InscriptionExterneStepView.as_view(), name='inscription_externe_step'),
    path('inscription-externe/confirmation/', views.InscriptionExterneConfirmationView.as_view(), name='inscription_externe_confirmation'),
    path('nouvelle_inscription/', views.NouvelleInscriptionView.as_view(), name='nouvelle_inscription'),

    # AJAX endpoints
    path('ajax/specialities-by-program/', views.get_specialities_by_program, name='get_specialities_by_program'),

    re_path(r'^favicon\.ico$', favicon_view),
]
