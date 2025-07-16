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
    path('enseignants/<str:matricule>/', views.DetailEnseignantView.as_view(), name='detail_enseignant'),
    path('enseignants/<str:matricule>/modifier/', views.ModifierEnseignantView.as_view(), name='modifier_enseignant'),
    path('enseignants/<str:matricule>/supprimer/', views.SupprimerEnseignantView.as_view(), name='supprimer_enseignant'),
    path('evaluations/ajouter/', views.ajouter_evaluationView.as_view(), name='ajouter_evaluation'),
    path('evaluations/<int:pk>/', views.DetailEvaluationView.as_view(), name='detail_evaluation'),
    path('evaluations/<int:pk>/modifier/', views.ModifierEvaluationView.as_view(), name='modifier_evaluation'),
    path('evaluations/<int:pk>/supprimer/', views.SupprimerEvaluationView.as_view(), name='supprimer_evaluation'),
    path('suivi_cours/ajouter/', views.ajouter_suiviView.as_view(), name='ajouter_suivi'),
    path('suivi_cours/<int:pk>/', views.DetailSuiviView.as_view(), name='detail_suivi'),
    path('suivi_cours/<int:pk>/modifier/', views.ModifierSuiviView.as_view(), name='modifier_suivi'),
    path('suivi_cours/<int:pk>/supprimer/', views.SupprimerSuiviView.as_view(), name='supprimer_suivi'),


 ]
"""path('enseignants/liste', views.liste_enseignants, name='liste_enseignants'),  # ta vue principale"""
