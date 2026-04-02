from django.urls import path, include

from main.custom_views.documents_views import *
from main.custom_views.pre_inscriptions_views import *
from main.views import *
from .custom_views import *
from django.views.generic.base import RedirectView
from django.urls import re_path
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

app_name = 'main'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='main:dashboard', permanent=False)),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('inscriptions/', PreInscriptionsView.as_view(), name='inscriptions'),
    path('inscriptions/imprimer-pdf/', pre_inscriptions_print_pdf, name='inscriptions_print_pdf'),
    path('inscription/<str:pk>/', pre_inscription_detail, name='inscription_detail'),
    path('inscription/<str:pk>/marquer-complet/', pre_inscription_mark_complete, name='inscription_mark_complete'),
    path('inscription/<str:pk>/imprimer-pdf/', pre_inscription_print_pdf, name='inscription_print_pdf'),
    path('inscription/<str:pk>/modifier/', pre_inscription_edit, name='inscription_edit'),
    path('inscription/<str:pk>/approuver/', pre_inscription_approve, name='inscription_approve'),
    path('inscription/<str:pk>/inscrire/', pre_inscription_register, name='inscription_register'),
    path('inscription/<str:pk>/rejeter/', pre_inscription_reject, name='inscription_reject'),
    path('inscription/<str:pk>/supprimer/', pre_inscription_delete, name='inscription_delete'),
    path('documents/', DocumentsView.as_view(), name='documents'),
    path('statistiques/', StatistiquesView.as_view(), name='statistiques'),
    path('parametres/', ParametresView.as_view(), name='parametres'),
    path('toggle-prospection/', toggle_prospection, name='toggle_prospection'),
    path('profil/', ProfilView.as_view(), name='profil'),

    # Gestion des documents officiels
    path('document/nouveau/', document_create, name='document_create'),
    path('document/<int:pk>/modifier/', document_edit, name='document_edit'),
    path('document/<int:pk>/supprimer/', document_delete, name='document_delete'),
    path('document/<int:pk>/toggle-status/', document_toggle_status, name='document_toggle_status'),
    path('document/<int:pk>/telecharger-certificat-inscription/', registration_certificate_download, name='registration_certificate_download'),
    path('document/creation-masse/', document_bulk_create, name='document_bulk_create'),
    path('document/preview-masse/', document_bulk_preview, name='document_bulk_preview'),
    path('document/ajax/student-search/', document_student_search, name='document_student_search'),
    path('document/ajax/student-levels/', document_student_levels, name='document_student_levels'),
    path('document/ajax/student-academic-years/', document_student_academic_years, name='document_student_academic_years'),

    # Formulaire d'inscription public
    path('inscription-externe/', PreInscriptionExterneView.as_view(), name='inscription_externe'),
    path('inscription-externe/etape/<int:step>/', PreInscriptionExterneStepView.as_view(), name='inscription_externe_step'),
    path('inscription-externe/confirmation/', PreInscriptionExterneConfirmationView.as_view(), name='inscription_externe_confirmation'),
    path('nouvelle_inscription/', NouvellePreInscriptionView.as_view(), name='nouvelle_inscription'),

    
    # AJAX endpoints
    path('ajax/specialities-by-program/', get_specialities_by_program, name='get_specialities_by_program'),

    re_path(r'^favicon\.ico$', favicon_view),
]
