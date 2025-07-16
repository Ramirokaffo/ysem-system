from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from academic.models import AcademicYear


@never_cache
@csrf_protect
def login_view(request):
    """
    Vue de connexion personnalisée
    """
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('main:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Déterminer la redirection basée sur le rôle
                    user_role = getattr(user, 'role', 'student')

                    # URLs de redirection par défaut par rôle
                    role_default_urls = {
                        'scholar': 'main:dashboard',
                        'teaching': 'teaching:Teaching',
                        'planning': 'planification:dashboard',
                        'super_admin': 'main:dashboard',
                        'student': 'student_portal:login'  # Les étudiants doivent utiliser le portail
                    }

                    # Obtenir l'URL de redirection
                    next_url = request.GET.get('next')

                    if next_url:
                        # Vérifier si l'utilisateur a le droit d'accéder à l'URL demandée
                        if user_can_access_url(user, next_url):
                            return redirect(next_url)
                        else:
                            messages.warning(
                                request,
                                f"Redirection vers votre dashboard. Votre rôle ne permet pas d'accéder à la page demandée."
                            )

                    # Rediriger vers le dashboard par défaut du rôle
                    default_url = role_default_urls.get(user_role, 'main:dashboard')
                    return redirect(default_url)
                else:
                    messages.error(request, 'Votre compte est désactivé.')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    return render(request, 'authentication/login.html')


@login_required
def logout_view(request):
    """
    Vue de déconnexion
    """
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('authentication:login')


def user_can_access_url(user, url):
    """
    Vérifie si un utilisateur peut accéder à une URL donnée basé sur son rôle
    """
    user_role = getattr(user, 'role', 'student')

    # Définir les accès par rôle
    role_access = {
        'scholar': ['/scholar/', '/auth/', '/admin/'],
        'teaching': ['/teach/', '/auth/', '/admin/'],
        'planning': ['/planning/', '/auth/', '/admin/'],
        'super_admin': ['/scholar/', '/teach/', '/planning/', '/prospection/', '/auth/', '/admin/'],
        'student': ['/portail-etudiant/', '/auth/logout/']
    }

    allowed_paths = role_access.get(user_role, [])

    # Vérifier si l'URL commence par un des chemins autorisés
    for allowed_path in allowed_paths:
        if url.startswith(allowed_path):
            return True

    return False


@login_required
def roles_info_view(request):
    """
    Vue pour afficher les informations sur les rôles et permissions
    Accessible uniquement aux super administrateurs
    """
    # Vérifier que l'utilisateur est un super administrateur
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

    context = {
        'page_title': 'Gestion des Rôles et Permissions',
        'current_user_role': getattr(request.user, 'role', 'unknown'),
    }

    return render(request, 'authentication/roles_info.html', context)
