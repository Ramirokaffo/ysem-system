from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden


class RoleBasedAccessMiddleware:
    """
    Middleware pour contrôler l'accès aux dashboards basé sur les rôles utilisateur
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Définition des accès par rôle
        self.role_access_map = {
            'scholar': {
                'allowed_paths': ['/scholar/', '/auth/', '/admin/'],
                'dashboard_url': 'main:dashboard',
                'forbidden_paths': ['/teach/', '/planning/', '/prospection/']
            },
            'teaching': {
                'allowed_paths': ['/teach/', '/auth/', '/admin/'],
                'dashboard_url': 'teaching:Teaching',
                'forbidden_paths': ['/scholar/', '/planning/', '/prospection/']
            },
            'planning': {
                'allowed_paths': ['/planning/', '/auth/', '/admin/'],
                'dashboard_url': 'planification:dashboard',
                'forbidden_paths': ['/scholar/', '/teach/', '/prospection/']
            },
            'super_admin': {
                'allowed_paths': ['/scholar/', '/teach/', '/planning/', '/prospection/', '/auth/', '/admin/'],
                'dashboard_url': 'main:dashboard',
                'forbidden_paths': []
            },
            'student': {
                'allowed_paths': ['/portail-etudiant/', '/auth/logout/'],
                'dashboard_url': '/portail-etudiant/connexion/',
                'forbidden_paths': ['/scholar/', '/teach/', '/planning/', '/prospection/', '/admin/']
            }
        }
    
    def __call__(self, request):
        # Ignorer les requêtes pour les fichiers statiques et media
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/favicon.ico')):
            return self.get_response(request)
        
        # Ignorer si l'utilisateur n'est pas authentifié (sera géré par les décorateurs login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Ignorer si c'est un étudiant connecté au portail (géré par StudentPortalSecurityMiddleware)
        if request.session.get('student_authenticated'):
            return self.get_response(request)
        
        # Obtenir le rôle de l'utilisateur
        user_role = getattr(request.user, 'role', 'student')
        
        # Si le rôle n'est pas défini dans notre mapping, traiter comme étudiant
        if user_role not in self.role_access_map:
            user_role = 'student'
        
        role_config = self.role_access_map[user_role]
        
        # Vérifier si l'utilisateur essaie d'accéder à un chemin interdit
        for forbidden_path in role_config['forbidden_paths']:
            if request.path.startswith(forbidden_path):
                messages.error(
                    request,
                    f"Accès interdit. Votre rôle ({self.get_role_display(user_role)}) ne permet pas d'accéder à cette section."
                )
                # Rediriger vers le dashboard approprié pour ce rôle
                try:
                    return redirect(role_config['dashboard_url'])
                except:
                    # En cas d'erreur de redirection, utiliser une URL absolue
                    if user_role == 'scholar':
                        return redirect('/scholar/')
                    elif user_role == 'teaching':
                        return redirect('/teach/')
                    elif user_role == 'planning':
                        return redirect('/planning/')
                    else:
                        return redirect('/scholar/')
        
        # Vérifier si l'utilisateur accède à un chemin autorisé
        path_allowed = False
        for allowed_path in role_config['allowed_paths']:
            if request.path.startswith(allowed_path):
                path_allowed = True
                break
        
        # Si le chemin n'est pas explicitement autorisé et n'est pas dans les chemins communs
        common_paths = ['/auth/', '/admin/logout/', '/admin/password_change/']
        is_common_path = any(request.path.startswith(path) for path in common_paths)
        
        if not path_allowed and not is_common_path:
            # Permettre l'accès à la racine et rediriger vers le bon dashboard
            if request.path == '/':
                return redirect(role_config['dashboard_url'])
            
            # Pour les autres chemins non autorisés, afficher un message et rediriger
            messages.warning(
                request,
                f"Vous avez été redirigé vers votre dashboard. Votre rôle ({self.get_role_display(user_role)}) ne permet pas d'accéder à la section demandée."
            )
            return redirect(role_config['dashboard_url'])
        
        return self.get_response(request)
    
    def get_role_display(self, role):
        """Retourne le nom d'affichage du rôle"""
        role_names = {
            'scholar': 'Responsable de Scolarité',
            'teaching': 'Responsable des Enseignements',
            'planning': 'Responsable de Planification',
            'super_admin': 'Administrateur',
            'student': 'Étudiant'
        }
        return role_names.get(role, 'Utilisateur')


class DashboardRedirectMiddleware:
    """
    Middleware pour rediriger automatiquement vers le bon dashboard après connexion
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Redirection automatique pour la page d'accueil
        if (request.path == '/' and 
            request.user.is_authenticated and 
            not request.session.get('student_authenticated')):
            
            user_role = getattr(request.user, 'role', 'student')
            
            # Définir les URLs de redirection par rôle
            role_redirects = {
                'scholar': 'main:dashboard',
                'teaching': 'teaching:Teaching',
                'planning': 'planification:dashboard',
                'super_admin': 'main:dashboard',
                'student': 'authentication:login'  # Les étudiants doivent utiliser le portail
            }
            
            redirect_url = role_redirects.get(user_role, 'main:dashboard')
            return redirect(redirect_url)
        
        return self.get_response(request)


class ProspectionAccessMiddleware:
    """
    Middleware spécial pour gérer l'accès au module de prospection
    qui est accessible uniquement aux responsables de scolarité (scholar_admin)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier l'accès au module prospection
        if request.path.startswith('/prospection/'):
            # Ignorer si l'utilisateur n'est pas authentifié
            if not request.user.is_authenticated:
                return self.get_response(request)
            
            # Ignorer si c'est un étudiant connecté au portail
            if request.session.get('student_authenticated'):
                return self.get_response(request)
            
            # Vérifier si l'utilisateur a le droit d'accéder à la prospection
            if not (request.user.is_scholar_admin() or 
                    getattr(request.user, 'role', '') == 'super_admin'):
                messages.error(
                    request,
                    "Accès interdit. Le module de prospection est réservé aux responsables de scolarité."
                )
                # Rediriger vers le dashboard approprié
                if request.user.is_study_admin():
                    return redirect('teaching:Teaching')
                elif request.user.is_planning_admin():
                    return redirect('planification:dashboard')
                else:
                    return redirect('main:dashboard')
        
        return self.get_response(request)
