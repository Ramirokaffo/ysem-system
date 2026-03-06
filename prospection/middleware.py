from django.http import JsonResponse
from django.urls import resolve
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .authentication import AgentJWTAuthentication
from .models import Agent


class AgentActiveMiddleware:
    """
    Middleware pour vérifier que seuls les agents actifs peuvent accéder aux endpoints protégés
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs qui ne nécessitent pas d'agent actif
        self.exempt_urls = [
            'agent_register',
            'agent_login', 
            'validate_token',
            'agent_logout'
        ]
    
    def __call__(self, request):
        # Vérifier si c'est une URL de l'API prospection
        if request.path.startswith('/api/v1/'):
            try:
                resolved = resolve(request.path)
                url_name = resolved.url_name
                
                # Si c'est un endpoint protégé
                if url_name not in self.exempt_urls:
                    # Vérifier l'authentification JWT
                    auth_header = request.META.get('HTTP_AUTHORIZATION')
                    if auth_header and auth_header.startswith('Bearer '):
                        token_string = auth_header.split(' ')[1]
                        
                        try:
                            # Utiliser notre authentification personnalisée
                            auth = AgentJWTAuthentication()
                            validated_token = auth.get_validated_token(token_string)
                            user = auth.get_user(validated_token)
                            
                            # Vérifier si l'agent est actif
                            if hasattr(user, 'agent'):
                                agent = user.agent
                                if not agent.is_active:
                                    return JsonResponse({
                                        'success': False,
                                        'message': 'Votre compte n\'est pas actif. Contactez un administrateur.',
                                        'error_code': 'ACCOUNT_INACTIVE'
                                    }, status=403)
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'message': 'Token invalide',
                                    'error_code': 'INVALID_TOKEN'
                                }, status=401)
                                
                        except (InvalidToken, TokenError):
                            return JsonResponse({
                                'success': False,
                                'message': 'Token invalide ou expiré',
                                'error_code': 'INVALID_TOKEN'
                            }, status=401)
            except:
                # Si on ne peut pas résoudre l'URL, on laisse passer
                pass
        
        response = self.get_response(request)
        return response


class AgentPermissionMiddleware:
    """
    Middleware pour gérer les permissions spécifiques aux agents
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs qui nécessitent des permissions spéciales
        self.admin_urls = [
            'seances_list',  # Créer des séances
            'equipes_list',  # Créer des équipes
        ]
    
    def __call__(self, request):
        # Vérifier si c'est une URL d'administration
        if request.path.startswith('/api/v1/') and request.method in ['POST', 'PUT', 'DELETE']:
            try:
                resolved = resolve(request.path)
                url_name = resolved.url_name
                
                # Si c'est un endpoint d'administration
                if url_name in self.admin_urls:
                    # Vérifier l'authentification JWT
                    auth_header = request.META.get('HTTP_AUTHORIZATION')
                    if auth_header and auth_header.startswith('Bearer '):
                        token_string = auth_header.split(' ')[1]
                        
                        try:
                            # Utiliser notre authentification personnalisée
                            auth = AgentJWTAuthentication()
                            validated_token = auth.get_validated_token(token_string)
                            user = auth.get_user(validated_token)
                            
                            # Vérifier si l'agent a les permissions
                            if hasattr(user, 'agent'):
                                agent = user.agent
                                # Pour l'instant, tous les agents actifs peuvent créer des séances/équipes
                                # On peut ajouter une logique plus complexe ici
                                if not agent.is_active:
                                    return JsonResponse({
                                        'success': False,
                                        'message': 'Permissions insuffisantes',
                                        'error_code': 'INSUFFICIENT_PERMISSIONS'
                                    }, status=403)
                                    
                        except (InvalidToken, TokenError):
                            return JsonResponse({
                                'success': False,
                                'message': 'Token invalide ou expiré',
                                'error_code': 'INVALID_TOKEN'
                            }, status=401)
            except:
                # Si on ne peut pas résoudre l'URL, on laisse passer
                pass
        
        response = self.get_response(request)
        return response
