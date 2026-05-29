from django.contrib import messages
from django.shortcuts import redirect

from accounts.access_modules import (
    get_module_dashboard,
    get_module_for_path,
    get_module_label,
)


CURRENT_MODULE_SESSION_KEY = "current_module"


def _set_last_accessed_module(request, module_code):
    user = request.user
    request.session[CURRENT_MODULE_SESSION_KEY] = module_code
    if getattr(user, 'last_accessed_module', None) != module_code:
        user.last_accessed_module = module_code
        user.save(update_fields=['last_accessed_module'])


def _redirect_to_user_entrypoint(request):
    print("Redirection vers le point d'entrée utilisateur++++++++")
    user = request.user
    module_codes = user.get_accessible_module_codes()
    if not module_codes:
        return redirect('authentication:select_module')
    if len(module_codes) == 1:
        module_code = module_codes[0]
        _set_last_accessed_module(request, module_code)
        return redirect(get_module_dashboard(module_code))
    return redirect('authentication:select_module')


class RoleBasedAccessMiddleware:
    """
    Middleware historique, désormais basé sur les modules accessibles.

    Le nom de classe est conservé pour éviter de modifier la configuration
    MIDDLEWARE existante.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.public_paths = [
            '/auth/login/',
            '/auth/logout/',
            '/portail-etudiant/',
            '/admissions/',
            '/nouvelle_inscription/',
            '/ajax/',
        ]
        self.common_authenticated_paths = [
            '/auth/',
            '/admin/',
            '/enseignants/',
        ]

    def __call__(self, request):
        print(f"Middleware d'accès : path={request.path}, user={request.user}, authenticated={request.user.is_authenticated}, student_auth={request.session.get('student_authenticated')}")
        if request.path.startswith(('/static/', '/media/', '/favicon.ico')):
            return self.get_response(request)

        if any(request.path.startswith(path) for path in self.public_paths):
            print(f"Accès public à {request.path}")
            return self.get_response(request)

        if request.path == '/':
            print(f"Redirection vers le point d'entrée utilisateur++++++++")
            return self.get_response(request)

        if not request.user.is_authenticated:
            print(f"Accès non authentifié à {request.path}")
            return self.get_response(request)

        if request.session.get('student_authenticated'):
            print(f"Accès étudiant à {request.path}")
            return self.get_response(request)

        if request.user.is_superuser:
            module_code = get_module_for_path(request.path)
            print(f"Superuser accède à {request.path}, module détecté : {module_code}")
            if module_code:
                _set_last_accessed_module(request, module_code)
            return self.get_response(request)

        module_code = get_module_for_path(request.path)
        if module_code:
            if request.user.has_module_access(module_code):
                _set_last_accessed_module(request, module_code)
                return self.get_response(request)

            messages.error(
                request,
                f"Accès interdit. Vous n'avez pas accès au module {get_module_label(module_code)}."
            )
            return _redirect_to_user_entrypoint(request)

        if any(request.path.startswith(path) for path in self.common_authenticated_paths):
            print(f"Accès authentifié à {request.path}")
            return self.get_response(request)

        print(f"Accès non autorisé à {request.path}+++++-----")
        return self.get_response(request)


class DashboardRedirectMiddleware:
    """Redirige la racine vers le dernier module connu ou la page de choix."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.path == '/' and
            request.user.is_authenticated and
            not request.session.get('student_authenticated')):
            module_codes = request.user.get_accessible_module_codes()
            print(f"DashboardRedirectMiddleware: user={request.user}, last_accessed_module={request.user.last_accessed_module}, accessible_modules={module_codes}")
            if not module_codes:
                return redirect('authentication:select_module')

            module_code = request.user.last_accessed_module
            if module_code not in module_codes:
                module_code = module_codes[0] if len(module_codes) == 1 else None

            if module_code:
                _set_last_accessed_module(request, module_code)
                return redirect(get_module_dashboard(module_code))
            return redirect('authentication:select_module')

        return self.get_response(request)


class ProspectionAccessMiddleware:
    """Compatibilité : l'accès prospection est maintenant un accès module."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/prospection/'):
            if not request.user.is_authenticated or request.session.get('student_authenticated'):
                return self.get_response(request)
            if request.user.is_superuser or request.user.has_module_access('prospection'):
                return self.get_response(request)
            messages.error(request, "Accès interdit. Vous n'avez pas accès au module Prospection.")
            return _redirect_to_user_entrypoint(request)

        return self.get_response(request)