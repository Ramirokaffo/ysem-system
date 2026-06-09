"""Service d'envoi d'emails composés depuis n'importe où dans le système."""

import logging
from urllib.parse import urljoin

from django.conf import settings
from templated_mail.mail import BaseEmailMessage

from main.models import SystemSettings

from .models import EmailLog


logger = logging.getLogger(__name__)

COMPOSED_EMAIL_TEMPLATE = 'emails/emails/composed_email.html'


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
    """Construit le contexte de branding réutilisé par les emails."""
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
        logger.exception("Impossible de charger SystemSettings pour l'email composé.")

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


def send_composed_email(subject, html_body, recipients, request=None, sender=None):
    """Envoie un email composé à un ou plusieurs destinataires.

    Chaque destinataire reçoit un message individuel (pas de fuite d'adresses).
    Retourne un tuple ``(success_count, failure_count)``.
    """
    branding = _branding_context(request=request)
    from_email = (
        getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or branding.get('contact_email')
        or 'noreply@ysem.education'
    )

    context = {
        'subject': subject,
        'body': html_body,
        **branding,
    }

    success_count = 0
    failure_count = 0
    for recipient in recipients:
        try:
            BaseEmailMessage(
                context=context,
                template_name=COMPOSED_EMAIL_TEMPLATE,
            ).send(to=[recipient], from_email=from_email)
            success_count += 1
        except Exception:
            logger.exception("Échec de l'envoi de l'email composé à %s", recipient)
            failure_count += 1

    try:
        EmailLog.objects.create(
            subject=subject,
            body=html_body,
            recipients=', '.join(recipients),
            sender=sender if getattr(sender, 'pk', None) else None,
            success_count=success_count,
            failure_count=failure_count,
        )
    except Exception:
        logger.exception("Impossible d'enregistrer le journal d'email composé.")

    return success_count, failure_count
