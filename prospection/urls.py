from django.urls import path
from . import views

app_name = 'prospection'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Agents
    path('agents/', views.AgentsView.as_view(), name='agents'),
    path('agents/ajouter/', views.AjouterAgentView.as_view(), name='ajouter_agent'),
    path('agents/<str:matricule>/', views.DetailAgentView.as_view(), name='detail_agent'),
    path('agents/<str:matricule>/modifier/', views.ModifierAgentView.as_view(), name='modifier_agent'),
    
    # Campagnes
    path('campagnes/', views.CampagnesView.as_view(), name='campagnes'),
    path('campagnes/ajouter/', views.AjouterCampagneView.as_view(), name='ajouter_campagne'),
    path('campagnes/<int:pk>/', views.DetailCampagneView.as_view(), name='detail_campagne'),
    path('campagnes/<int:pk>/modifier/', views.ModifierCampagneView.as_view(), name='modifier_campagne'),
    
    # Équipes
    path('equipes/', views.EquipesView.as_view(), name='equipes'),
    path('equipes/ajouter/', views.AjouterEquipeView.as_view(), name='ajouter_equipe'),
    path('equipes/<int:pk>/', views.DetailEquipeView.as_view(), name='detail_equipe'),
    path('equipes/<int:pk>/modifier/', views.ModifierEquipeView.as_view(), name='modifier_equipe'),
    
    # Prospects
    path('prospects/', views.ProspectsView.as_view(), name='prospects'),
    path('prospects/ajouter/', views.AjouterProspectView.as_view(), name='ajouter_prospect'),
    path('prospects/<int:pk>/', views.DetailProspectView.as_view(), name='detail_prospect'),
    path('prospects/<int:pk>/modifier/', views.ModifierProspectView.as_view(), name='modifier_prospect'),
    
    # Statistiques
    path('statistiques/', views.StatistiquesView.as_view(), name='statistiques'),
]
