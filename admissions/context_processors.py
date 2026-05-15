"""Context processors du portail d'admission."""
from students.models import Student

from .decorators import SESSION_AUTH_KEY, SESSION_STUDENT_ID


def candidate_session(request):
    """Expose les informations du candidat connecté aux templates du portail.

    Permet notamment d'afficher la photo de profil dans le bloc utilisateur
    en haut à droite, sans devoir requêter explicitement la base depuis
    chaque vue.
    """
    if not getattr(request, 'session', None):
        return {}
    if not request.session.get(SESSION_AUTH_KEY):
        return {}
    student_id = request.session.get(SESSION_STUDENT_ID)
    if not student_id:
        return {}

    photo_url = ''
    student = (
        Student.objects
        .filter(pk=student_id)
        .only('profile_photo')
        .first()
    )
    if student and student.profile_photo:
        try:
            photo_url = student.profile_photo.url
        except (ValueError, AttributeError):
            photo_url = ''
    return {
        'candidate_profile_photo_url': photo_url,
    }
