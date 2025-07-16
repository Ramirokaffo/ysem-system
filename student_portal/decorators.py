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


def teaching_admin_required(view_func):
    """
    Décorateur pour s'assurer qu'un utilisateur est un responsable des enseignements
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier si c'est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables des enseignements."
            )
            return redirect('student_portal:dashboard')

        # Vérifier si l'utilisateur est connecté et est un responsable des enseignements
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à cette page."
            )
            return redirect('authentication:login')

        if not request.user.is_study_admin():
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux responsables des enseignements."
            )
            # Rediriger vers le dashboard approprié selon le rôle
            if request.user.is_scholar_admin():
                return redirect('main:dashboard')
            elif request.user.is_planning_admin():
                return redirect('planification:dashboard')
            else:
                return redirect('main:dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def super_admin_required(view_func):
    """
    Décorateur pour s'assurer qu'un utilisateur est un super administrateur
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Vérifier si c'est un étudiant connecté au portail
        if request.session.get('student_authenticated'):
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux super administrateurs."
            )
            return redirect('student_portal:dashboard')

        # Vérifier si l'utilisateur est connecté et est un super administrateur
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à cette page."
            )
            return redirect('authentication:login')

        if getattr(request.user, 'role', '') != 'super_admin':
            messages.error(
                request,
                "Accès interdit. Cette page est réservée aux super administrateurs."
            )
            # Rediriger vers le dashboard approprié selon le rôle
            if request.user.is_scholar_admin():
                return redirect('main:dashboard')
            elif request.user.is_study_admin():
                return redirect('teaching:Teaching')
            elif request.user.is_planning_admin():
                return redirect('planification:dashboard')
            else:
                return redirect('main:dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    """
    Décorateur générique pour vérifier les rôles autorisés
    Usage: @role_required('scholar', 'super_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Vérifier si c'est un étudiant connecté au portail
            if request.session.get('student_authenticated'):
                messages.error(
                    request,
                    "Accès interdit. Vous n'avez pas les permissions nécessaires."
                )
                return redirect('student_portal:dashboard')

            # Vérifier si l'utilisateur est connecté
            if not request.user.is_authenticated:
                messages.error(
                    request,
                    "Vous devez vous connecter pour accéder à cette page."
                )
                return redirect('authentication:login')

            # Vérifier le rôle de l'utilisateur
            user_role = getattr(request.user, 'role', 'student')
            if user_role not in allowed_roles:
                messages.error(
                    request,
                    f"Accès interdit. Votre rôle ne permet pas d'accéder à cette page."
                )
                # Rediriger vers le dashboard approprié selon le rôle
                if request.user.is_scholar_admin():
                    return redirect('main:dashboard')
                elif request.user.is_study_admin():
                    return redirect('teaching:Teaching')
                elif request.user.is_planning_admin():
                    return redirect('planification:dashboard')
                else:
                    return redirect('main:dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
