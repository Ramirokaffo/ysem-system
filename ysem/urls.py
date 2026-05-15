"""
URL configuration for ysem project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from main.views import *
from main.custom_views.pre_inscriptions_views import (
    NouvellePreInscriptionView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    path("scholar/", include("main.urls")),
    path("teach/", include("Teaching.urls")),
    path("planning/", include("planification.urls")),
    path("prospection/", include("prospection.urls")),
    path("portail-etudiant/", include("student_portal.urls")),
    path("admissions/", include("admissions.urls")),
    path("etudiants/", include("students.urls")),

    # URLs pour la gestion des paiements
    path('paiements/', include('payments.urls')),
    # API pour l'application mobile
    path("api/v1/", include("prospection.api_urls")),

    path('nouvelle_inscription/', NouvellePreInscriptionView.as_view(), name='nouvelle_inscription'),
    path('ajax/specialities-by-program/', get_specialities_by_program, name='get_specialities_by_program'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # URLs de test pour les pages d'erreur (seulement en mode DEBUG)
    from main.views import test_404_view, test_500_view, test_403_view
    urlpatterns += [
        path('test-404/', test_404_view, name='test_404'),
        path('test-500/', test_500_view, name='test_500'),
        path('test-403/', test_403_view, name='test_403'),
    ]
