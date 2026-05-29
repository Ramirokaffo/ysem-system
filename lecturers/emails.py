"""Envois d'emails pour le portail enseignant (activation, reset)."""

import logging
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from templated_mail.mail import BaseEmailMessage

from main.models import SystemSettings


logger = logging.getLogger(__name__)


ACTIVATION_TEMPLATE = 'lecturers/emails/account_activation.html'
PASSWORD_RESET_TEMPLATE = 'lecturers/emails/password_reset.html'
RECRUITMENT_ACCEPTED_TEMPLATE = 'lecturers/emails/recruitment_accepted.html'
RECRUITMENT_REFUSED_TEMPLATE = 'lecturers/emails/recruitment_refused.html'


def _lecturer_display_name(lecturer):
    return f"{lecturer.firstname or ''} {lecturer.lastname or ''}".strip() or (lecturer.email or '')


def _build_absolute_url(base_url, path):
    if not path:
        return ''
    if path.startswith(('http://', 'https://')):
        return path
    normalized_base = (base_url or '').strip()
    if not normalized_base:
        return path
    if not normalized_base.endswith('/'):
        normalized_base = f"{normalized_base}/"
    return urljoin(normalized_base, path.lstrip('/'))


def _branding_context(request=None):
    """Construit le contexte de branding utilisé par les emails."""
    institution_name = 'YSEM'
    contact_email = ''
    website = ''
    logo_path = ''
    address = ''
    phone = ''
    try:
        system_settings = SystemSettings.get_settings()
        institution_name = system_settings.institution_name or institution_name
        contact_email = system_settings.email or ''
        website = system_settings.website or ''
        logo_path = system_settings.get_logo_url() or ''
        address = system_settings.address or ''
        phone = system_settings.phone or ''
    except Exception:
        logger.exception("Impossible de charger SystemSettings pour l'email enseignant.")

    base_url = ''
    if request is not None:
        try:
            base_url = request.build_absolute_uri('/').rstrip('/')
        except Exception:
            base_url = ''
    if not base_url:
        base_url = website

    return {
        'institution_name': institution_name,
        'contact_email': contact_email or '--',
        'website': website or '--',
        'address': address,
        'phone': phone,
        'email_logo_url': _build_absolute_url(base_url or website, logo_path),
        'base_url': base_url,
    }


def _send(template_name, recipient, context):
    from_email = (
        getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or context.get('contact_email')
        or 'noreply@ysem.education'
    )
    try:
        BaseEmailMessage(
            context=context,
            template_name=template_name,
        ).send(to=[recipient], from_email=from_email)
        return True
    except Exception:
        logger.exception("Échec d'envoi du mail enseignant (%s) à %s", template_name, recipient)
        return False


def send_activation_email(lecturer, token, request=None):
    """Envoie l'email d'activation contenant le lien signé."""
    recipient = (lecturer.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('lecturers:activate', args=[token])
    activation_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'lecturer': lecturer,
        'lecturer_name': _lecturer_display_name(lecturer),
        'activation_url': activation_url,
        'expires_hours': 48,
        **branding,
    }
    return _send(ACTIVATION_TEMPLATE, recipient, context)


def send_password_reset_email(lecturer, token, request=None):
    """Envoie l'email de réinitialisation de mot de passe."""
    recipient = (lecturer.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('lecturers:password_reset_confirm', args=[token])
    reset_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'lecturer': lecturer,
        'lecturer_name': _lecturer_display_name(lecturer),
        'reset_url': reset_url,
        'expires_hours': 2,
        **branding,
    }
    return _send(PASSWORD_RESET_TEMPLATE, recipient, context)


def send_recruitment_accepted_email(lecturer, request=None):
    """Notifie l'enseignant que sa candidature a été acceptée."""
    recipient = (lecturer.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('lecturers:dashboard')
    dashboard_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'lecturer': lecturer,
        'lecturer_name': _lecturer_display_name(lecturer),
        'dashboard_url': dashboard_url,
        **branding,
    }
    return _send(RECRUITMENT_ACCEPTED_TEMPLATE, recipient, context)


def send_recruitment_refused_email(lecturer, reason, can_be_resubmitted=False, request=None):
    """Notifie l'enseignant que sa candidature a été refusée."""
    recipient = (lecturer.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('lecturers:dashboard')
    dashboard_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'lecturer': lecturer,
        'lecturer_name': _lecturer_display_name(lecturer),
        'reason': reason,
        'can_be_resubmitted': can_be_resubmitted,
        'dashboard_url': dashboard_url,
        **branding,
    }
    return _send(RECRUITMENT_REFUSED_TEMPLATE, recipient, context)
