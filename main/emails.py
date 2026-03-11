import logging
from urllib.parse import urljoin

from django.conf import settings
from templated_mail.mail import BaseEmailMessage

from .models import SystemSettings


logger = logging.getLogger(__name__)


STUDENT_STATUS_EMAIL_TEMPLATES = {
    'pre_inscription': 'main/emails/student_status_pre_inscription.html',
    'pre_inscription_approved': 'main/emails/student_status_pre_inscription_approved.html',
    'registration': 'main/emails/student_status_registration.html',
}


def _get_student_display_name(student):
    return f"{student.firstname} {student.lastname}".strip() or str(student)


def _build_absolute_url(base_url, url):
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url

    normalized_base = (base_url or '').strip()
    if not normalized_base:
        return ''

    if not normalized_base.endswith('/'):
        normalized_base = f"{normalized_base}/"

    return urljoin(normalized_base, url.lstrip('/'))


def send_student_status_email(student, notification_type):
    recipient = (student.email or '').strip()
    if not recipient:
        return False

    template_name = STUDENT_STATUS_EMAIL_TEMPLATES.get(notification_type)
    if not template_name:
        return False

    try:
        system_settings = SystemSettings.get_settings()
        if not system_settings.email_enrollment:
            return False

        institution_name = system_settings.institution_name
        contact_email = system_settings.email
        website = system_settings.website
        email_logo_url = _build_absolute_url(website, system_settings.get_logo_url())
    except Exception:
        logger.exception("Impossible de récupérer les paramètres système pour l'email étudiant.")
        institution_name = 'YSEM'
        contact_email = ''
        website = ''
        email_logo_url = ''

    from_email = (
        getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or contact_email
        or 'noreply@ysem.education'
    )

    context = {
        'student': student,
        'student_name': _get_student_display_name(student),
        'institution_name': institution_name,
        'contact_email': contact_email or 'Non renseigné',
        'website': website or 'Non renseigné',
        'email_logo_url': email_logo_url,
    }

    try:
        BaseEmailMessage(
            context=context,
            template_name=template_name,
        ).send(
            to=[recipient],
            from_email=from_email,
        )
    except Exception:
        logger.exception(
            "Échec de l'envoi de l'email '%s' à l'étudiant %s.",
            notification_type,
            student.pk,
        )
        return False

    return True