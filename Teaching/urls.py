from django.urls import path
from . import views

app_name = 'teaching'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='Teaching'),
    path('enseignants/', views.EnseignantsView.as_view(), name='enseignants'),
    path('evaluations/', views.EvaluationsView.as_view(), name='evaluations'),
    path('suivi_cours/', views.Suivi_CoursView.as_view(), name='suivi_cours'),
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
    path('parametres/', views.ParametresView.as_view(), name='parametres'),
    path('enseignants/ajouter/', views.ajouter_enseignantView.as_view(), name='ajouter_enseignant'),
    path('evaluations/ajouter/', views.ajouter_evaluationView.as_view(), name='ajouter_evaluation'),
    path('suivi_cours/ajouter/', views.ajouter_suiviView.as_view(), name='ajouter_suivi'),

    
 ]
"""path('enseignants/liste', views.liste_enseignants, name='liste_enseignants'),  # ta vue principale"""
