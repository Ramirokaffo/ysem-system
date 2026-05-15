"""
Double authentification ciblée par email : décision de déclenchement,
création des défis, envoi de l'email de vérification.
"""
import logging

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from templated_mail.mail import BaseEmailMessage

from .models import (
    LoginHistory,
    TwoFactorChallenge,
    TWO_FACTOR_CHALLENGE_TTL,
)
from .services import (
    build_device_label,
    get_client_ip,
    is_known_device,
    parse_user_agent,
)


logger = logging.getLogger("authentication")


_PURPOSE_TEMPLATES = {
    TwoFactorChallenge.PURPOSE_LOGIN: "authentication/emails/two_factor_login.html",
    TwoFactorChallenge.PURPOSE_TOGGLE: "authentication/emails/two_factor_toggle.html",
}

_PURPOSE_LABELS = {
    TwoFactorChallenge.PURPOSE_LOGIN: "votre connexion",
    TwoFactorChallenge.PURPOSE_TOGGLE: "la modification de votre double authentification",
}


def should_challenge_user(request, user) -> bool:
    """Décide si la 2FA doit être déclenchée pour cet utilisateur/appareil."""
    if user is None or not getattr(user, "pk", None):
        return False
    if not (getattr(user, "email", "") or "").strip():
        return False
    if getattr(user, "two_factor_enabled", False):
        return True
    return not is_known_device(request=request, user=user)


def _institution_context():
    try:
        from main.models import SystemSettings

        system_settings = SystemSettings.get_settings()
        return {
            "institution_name": system_settings.institution_name or "YSEM",
            "contact_email": system_settings.email or "",
        }
    except Exception:
        return {"institution_name": "YSEM", "contact_email": ""}


def create_challenge(request, user, *, purpose, next_url="", requested_state=None) -> tuple[TwoFactorChallenge, str]:
    """
    Crée un défi 2FA en base et retourne (challenge, code_en_clair).
    Le code en clair n'est jamais persisté et ne doit servir qu'à l'email.
    """
    ip = get_client_ip(request) if request is not None else None
    ua = (request.META.get("HTTP_USER_AGENT") if request is not None else "") or ""
    parsed = parse_user_agent(ua)
    fingerprint = LoginHistory.compute_fingerprint(
        user_agent=ua,
        os_family=parsed["os_family"],
        browser_family=parsed["browser_family"],
        device_family=parsed["device_family"],
    )

    code = TwoFactorChallenge.generate_code()
    challenge = TwoFactorChallenge.objects.create(
        user=user,
        purpose=purpose,
        token=TwoFactorChallenge.generate_token(),
        code_hash=TwoFactorChallenge.hash_code(code),
        requested_state=requested_state,
        next_url=(next_url or "")[:500],
        ip_address=ip,
        user_agent=ua,
        device_fingerprint=fingerprint,
        expires_at=timezone.now() + TWO_FACTOR_CHALLENGE_TTL,
    )
    return challenge, code


def _confirm_url_name(purpose: str) -> str:
    if purpose == TwoFactorChallenge.PURPOSE_TOGGLE:
        return "authentication:two_factor_toggle_confirm_link"
    return "authentication:two_factor_login_confirm_link"


def send_challenge_email(request, challenge: TwoFactorChallenge, code: str) -> bool:
    """Envoie l'email de vérification contenant le code et le lien direct."""
    recipient = (getattr(challenge.user, "email", "") or "").strip()
    if not recipient:
        logger.warning(
            "Impossible d'envoyer le défi 2FA %s : utilisateur %s sans email.",
            challenge.pk,
            challenge.user_id,
        )
        return False

    template_name = _PURPOSE_TEMPLATES.get(challenge.purpose)
    if not template_name:
        return False

    parsed = parse_user_agent(challenge.user_agent)
    direct_path = reverse(_confirm_url_name(challenge.purpose), args=[challenge.token])
    direct_link = request.build_absolute_uri(direct_path) if request is not None else direct_path

    inst = _institution_context()
    user = challenge.user

    context = {
        "user": user,
        "user_name": user.get_full_name() or user.username,
        "code": code,
        "direct_link": direct_link,
        "expires_in_minutes": int(TWO_FACTOR_CHALLENGE_TTL.total_seconds() // 60),
        "ip_address": challenge.ip_address or "Inconnue",
        "user_agent": challenge.user_agent or "Inconnu",
        "device_label": build_device_label(parsed) or "Appareil inconnu",
        "purpose": challenge.purpose,
        "purpose_label": _PURPOSE_LABELS.get(challenge.purpose, ""),
        "institution_name": inst["institution_name"],
        "contact_email": inst["contact_email"],
    }

    from_email = (
        getattr(settings, "DEFAULT_FROM_EMAIL", "")
        or getattr(settings, "EMAIL_HOST_USER", "")
        or inst["contact_email"]
        or "noreply@ysem.education"
    )

    try:
        BaseEmailMessage(context=context, template_name=template_name).send(
            to=[recipient], from_email=from_email
        )
        return True
    except Exception:
        logger.exception("Échec d'envoi du défi 2FA %s à %s", challenge.pk, recipient)
        return False



def consume_challenge_by_code(challenge: TwoFactorChallenge, code: str) -> tuple[bool, str]:
    """Vérifie un code, incrémente le compteur d'essais, marque le défi comme consommé si OK."""
    if challenge.is_consumed():
        return False, "already_consumed"
    if challenge.is_expired():
        return False, "expired"
    if challenge.is_locked():
        return False, "locked"
    if not challenge.check_code(code or ""):
        challenge.attempts = (challenge.attempts or 0) + 1
        challenge.save(update_fields=["attempts"])
        return False, "invalid_code"
    challenge.mark_consumed()
    return True, "ok"


def consume_challenge_by_token(token: str, purpose: str) -> tuple[TwoFactorChallenge | None, str]:
    """Récupère un défi par son token (lien direct) et le consomme s'il est utilisable."""
    try:
        challenge = TwoFactorChallenge.objects.select_related("user").get(
            token=token, purpose=purpose
        )
    except TwoFactorChallenge.DoesNotExist:
        return None, "invalid_token"
    if challenge.is_consumed():
        return challenge, "already_consumed"
    if challenge.is_expired():
        return challenge, "expired"
    challenge.mark_consumed()
    return challenge, "ok"
