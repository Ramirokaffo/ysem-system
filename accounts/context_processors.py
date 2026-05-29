"""Context processors liés aux accès modules des utilisateurs internes."""

from .access_modules import get_module_for_path


def accessible_modules(request):
    """Expose les modules internes accessibles à l'utilisateur connecté.

    Permet d'afficher un sélecteur de module (bascule en 1 clic) dans les
    tableaux de bord, sans devoir requêter explicitement depuis chaque vue.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    session = getattr(request, 'session', None)
    if session is not None and session.get('student_authenticated'):
        return {}

    try:
        modules = user.get_accessible_modules_data()
    except Exception:
        return {}

    current_code = get_module_for_path(request.path)
    if not current_code and session is not None:
        current_code = session.get('current_module')

    return {
        'accessible_modules': modules,
        'current_module_code': current_code,
        'has_multiple_modules': len(modules) > 1,
    }
