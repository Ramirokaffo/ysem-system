from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


SESSION_AUTH_KEY = 'admission_authenticated'
SESSION_STUDENT_ID = 'admission_student_id'
SESSION_STUDENT_EMAIL = 'admission_student_email'
SESSION_STUDENT_NAME = 'admission_student_name'


def candidate_required(view_func):
    """Refuse l'accès aux pages internes du portail d'admission si le candidat
    n'est pas authentifié via la session dédiée."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(SESSION_AUTH_KEY):
            messages.error(
                request,
                "Vous devez vous connecter pour accéder à votre espace d'admission."
            )
            return redirect('admissions:login')
        return view_func(request, *args, **kwargs)

    return _wrapped
