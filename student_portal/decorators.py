from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """
    Décorateur pour s'assurer qu'un utilisateur est un vrai administrateur
    et non un étudiant connecté au portail
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier si c'est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux administrateurs."
            )
            return redirect('student_portal:dashboard')
        
        # Vérifier si l'utilisateur est connecté en tant qu'admin
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Vous devez vous connecter en tant qu'administrateur pour accéder à cette page."
            )
            return redirect('authentication:login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def scholar_admin_required(view_func):
    """
    Décorateur pour s'assurer qu'un utilisateur est un responsable de scolarité
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier si c'est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables de scolarité."
            )
            return redirect('student_portal:dashboard')
        
        # Vérifier si l'utilisateur est connecté et est un responsable de scolarité
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à cette page."
            )
            return redirect('authentication:login')
        
        if not request.user.is_scholar_admin():
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables de scolarité."
            )
            return redirect('main:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def no_student_portal_access(view_func):
    """
    Décorateur pour bloquer explicitement l'accès aux étudiants du portail
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('student_authenticated'):
            return HttpResponseForbidden(
                "Accès interdit. Les étudiants ne peuvent pas accéder à cette page."
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def planning_admin_required(view_func):
    """
    Décorateur pour s'assurer qu'un utilisateur est un responsable de planification
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier si c'est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables de planification."
            )
            return redirect('student_portal:dashboard')

        # Vérifier si l'utilisateur est connecté et est un responsable de planification
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à cette page."
            )
            return redirect('authentication:login')

        if not request.user.is_planning_admin():
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables de planification."
            )
            return redirect('main:dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper
