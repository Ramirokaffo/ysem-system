"""Envois d'emails pour le portail d'admission (activation, reset)."""

import logging
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from templated_mail.mail import BaseEmailMessage

from main.models import SystemSettings


logger = logging.getLogger(__name__)


ACTIVATION_TEMPLATE = 'admissions/emails/account_activation.html'
PASSWORD_RESET_TEMPLATE = 'admissions/emails/password_reset.html'


def _student_display_name(student):
    return f"{student.firstname} {student.lastname}".strip() or (student.email or '')


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
        logger.exception("Impossible de charger SystemSettings pour l'email admissions.")

    # Préfixe absolu : request si possible, sinon le site web configuré
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
        logger.exception("Échec d'envoi du mail admissions (%s) à %s", template_name, recipient)
        return False


def send_activation_email(student, token, request=None):
    """Envoie l'email d'activation contenant le lien signé."""
    recipient = (student.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('admissions:activate', args=[token])
    activation_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'student': student,
        'student_name': _student_display_name(student),
        'activation_url': activation_url,
        'expires_hours': 48,
        **branding,
    }
    return _send(ACTIVATION_TEMPLATE, recipient, context)


def send_password_reset_email(student, token, request=None):
    """Envoie l'email de réinitialisation de mot de passe."""
    recipient = (student.email or '').strip()
    if not recipient:
        return False

    branding = _branding_context(request=request)
    relative_url = reverse('admissions:password_reset_confirm', args=[token])
    reset_url = _build_absolute_url(branding['base_url'], relative_url)

    context = {
        'student': student,
        'student_name': _student_display_name(student),
        'reset_url': reset_url,
        'expires_hours': 2,
        **branding,
    }
    return _send(PASSWORD_RESET_TEMPLATE, recipient, context)
