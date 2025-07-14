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
                    if user.is_study_admin():
                        next_url = request.GET.get('next', 'teaching:Teaching')
                        return redirect(next_url)
                    elif user.is_planning_admin():
                        next_url = request.GET.get('next', 'planification:dashboard')
                        return redirect(next_url)

                    # Rediriger vers la page demandée ou le dashboard
                    next_url = request.GET.get('next', 'main:dashboard')
                    return redirect(next_url)
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
