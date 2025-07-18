from django.urls import path
from . import api_views

app_name = 'prospection_api'

urlpatterns = [
    # Authentification des agents
    path('auth/register/', api_views.AgentRegistrationView.as_view(), name='agent_register'),
    path('auth/login/', api_views.AgentLoginView.as_view(), name='agent_login'),
    path('auth/logout/', api_views.logout_agent, name='agent_logout'),
    path('auth/validate/', api_views.validate_token, name='validate_token'),

    # Profil de l'agent
    path('profile/', api_views.AgentProfileView.as_view(), name='agent_profile'),
    path('change-password/', api_views.ChangePasswordView.as_view(), name='change_password'),

    # Séances de prospection
    path('seances/', api_views.SeanceProspectionListView.as_view(), name='seances_list'),
    path('seances/<int:pk>/', api_views.SeanceProspectionDetailView.as_view(), name='seance_detail'),

    # Équipes de prospection
    path('equipes/', api_views.EquipeProspectionListView.as_view(), name='equipes_list'),
    path('equipes/<int:pk>/', api_views.EquipeProspectionDetailView.as_view(), name='equipe_detail'),
    path('equipes/<int:equipe_id>/membres/', api_views.ajouter_membre_equipe, name='ajouter_membre'),
    path('equipes/<int:equipe_id>/membres/<int:agent_id>/', api_views.supprimer_membre_equipe, name='supprimer_membre'),
    path('equipes/reconduire/', api_views.reconduire_equipe, name='reconduire_equipe'),

    # Utilitaires
    path('agents-actifs/', api_views.agents_actifs, name='agents_actifs'),

    # Gestion des agents (pour responsables)
    path('gestion/agents/', api_views.liste_agents_gestion, name='liste_agents_gestion'),
    path('gestion/agents/activer/', api_views.activer_agent, name='activer_agent'),
    path('gestion/agents/statistiques/', api_views.statistiques_agents, name='statistiques_agents'),
]
