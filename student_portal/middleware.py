from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseForbidden


class StudentPortalSecurityMiddleware:
    """
    Middleware pour bloquer l'accès des étudiants aux zones d'administration
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs interdites aux étudiants connectés au portail
        self.forbidden_paths = [
            '/admin/',
            '/auth/',
            '/scholar',
            '/etudiants/',
            '/documents/',
            '/statistiques/',
            '/parametres/',
            '/etudiant/',
            '/document/',
            '/inscription/',
            '/teach/',
        ]
    
    def __call__(self, request):
        # Vérifier si l'utilisateur est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            # Vérifier si l'étudiant essaie d'accéder à une zone interdite
            for forbidden_path in self.forbidden_paths:
                if request.path.startswith(forbidden_path):
                    # Bloquer l'accès et rediriger vers le portail étudiant
                    messages.error(
                        request, 
                        "Accès interdit. Vous n'avez pas les permissions nécessaires pour accéder à cette page."
                    )
                    return redirect('student_portal:dashboard')
        
        # Vérifier si un utilisateur admin essaie d'accéder au portail étudiant
        # (optionnel, pour éviter les conflits de session)
        if (request.user.is_authenticated and 
            request.path.startswith('/portail-etudiant/') and 
            request.path != reverse('student_portal:login')):
            
            # Si c'est un admin connecté, on peut soit :
            # 1. Le laisser accéder (pour tester)
            # 2. Le bloquer pour éviter les conflits
            # Ici on choisit de le laisser accéder mais on affiche un avertissement
            if not request.session.get('admin_portal_warning_shown'):
                messages.warning(
                    request,
                    "Vous êtes connecté en tant qu'administrateur. "
                    "L'accès au portail étudiant peut créer des conflits de session."
                )
                request.session['admin_portal_warning_shown'] = True
        
        response = self.get_response(request)
        return response


class StudentSessionCleanupMiddleware:
    """
    Middleware pour nettoyer les sessions en cas de conflit
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Si un utilisateur Django est connecté ET qu'il y a une session étudiant
        if (request.user.is_authenticated and 
            request.session.get('student_authenticated')):
            
            # Nettoyer la session étudiant pour éviter les conflits
            if 'student_authenticated' in request.session:
                del request.session['student_authenticated']
            if 'student_matricule' in request.session:
                del request.session['student_matricule']
            if 'student_name' in request.session:
                del request.session['student_name']
        
        response = self.get_response(request)
        return response
