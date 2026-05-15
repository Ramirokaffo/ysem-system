"""Tokens signés pour le portail d'admission.

On évite une table dédiée en s'appuyant sur :
- ``TimestampSigner`` (Django) pour la signature + l'horodatage,
- un sel distinct par usage (activation vs reset),
- pour le reset : on intègre le hash du mot de passe dans la charge utile, ce
  qui rend le lien invalide dès qu'un nouveau mot de passe est défini.
"""

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner


EMAIL_ACTIVATION_SALT = 'admissions.email_activation.v1'
PASSWORD_RESET_SALT = 'admissions.password_reset.v1'

# Durées de validité (en secondes)
EMAIL_ACTIVATION_MAX_AGE = 60 * 60 * 48      # 48 heures
PASSWORD_RESET_MAX_AGE = 60 * 60 * 2         # 2 heures


def make_activation_token(student):
    """Génère un token d'activation pour le compte du candidat."""
    signer = TimestampSigner(salt=EMAIL_ACTIVATION_SALT)
    return signer.sign(str(student.pk))


def validate_activation_token(token, max_age=EMAIL_ACTIVATION_MAX_AGE):
    """Retourne le student_id si le token est valide, ``None`` sinon."""
    signer = TimestampSigner(salt=EMAIL_ACTIVATION_SALT)
    try:
        value = signer.unsign(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def make_password_reset_token(student):
    """Génère un token de réinitialisation lié au mot de passe courant.

    Le hash du mot de passe est inclus dans la charge utile : ainsi, dès que
    l'utilisateur change son mot de passe, tous les anciens liens de reset
    deviennent invalides.
    """
    signer = TimestampSigner(salt=PASSWORD_RESET_SALT)
    payload = f"{student.pk}:{student.external_password_hash or ''}"
    return signer.sign(payload)


def validate_password_reset_token(token, max_age=PASSWORD_RESET_MAX_AGE):
    """Retourne ``(student_id, password_hash)`` si le token est valide, sinon ``None``."""
    signer = TimestampSigner(salt=PASSWORD_RESET_SALT)
    try:
        value = signer.unsign(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    try:
        pk_str, password_hash = value.split(':', 1)
        return int(pk_str), password_hash
    except (ValueError, AttributeError):
        return None
