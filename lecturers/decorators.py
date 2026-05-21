from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


SESSION_AUTH_KEY = 'lecturer_authenticated'
SESSION_LECTURER_ID = 'lecturer_matricule'
SESSION_LECTURER_EMAIL = 'lecturer_email'
SESSION_LECTURER_NAME = 'lecturer_name'


def lecturer_required(view_func):
    """Refuse l'accès aux pages du portail enseignant sans session valide."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(SESSION_AUTH_KEY):
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à votre espace enseignant."
            )
            return redirect('lecturers:login')
        return view_func(request, *args, **kwargs)

    return _wrapped
