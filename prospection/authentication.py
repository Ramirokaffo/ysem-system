from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from .models import Agent


class AgentJWTAuthentication(JWTAuthentication):
    """
    Authentification JWT personnalisée pour les agents
    """
    
    def get_user(self, validated_token):
        """
        Récupère l'agent à partir du token validé
        """
        try:
            agent_id = validated_token.get('agent_id')
            if agent_id:
                agent = Agent.objects.get(id=agent_id, is_active=True)
                # Créer un wrapper pour que l'agent soit compatible avec le système Django
                return AgentWrapper(agent)
        except Agent.DoesNotExist:
            pass
        
        return AnonymousUser()


class AgentWrapper:
    """
    Wrapper pour rendre l'Agent compatible avec le système d'authentification Django
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.id = agent.id
        self.pk = agent.id
        self.email = agent.email
        self.username = agent.email  # Django s'attend à un username
        self.first_name = agent.prenom
        self.last_name = agent.nom
        self.is_active = agent.is_active
        self.is_staff = False
        self.is_superuser = False
        self.last_login = agent.last_login
        self.date_joined = agent.created_at
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def __str__(self):
        return self.agent.nom_complet
    
    def get_full_name(self):
        return self.agent.nom_complet
    
    def get_short_name(self):
        return self.agent.prenom
    
    def has_perm(self, perm, obj=None):
        return False
    
    def has_perms(self, perm_list, obj=None):
        return False
    
    def has_module_perms(self, package_name):
        return False
