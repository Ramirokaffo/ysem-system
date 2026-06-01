import re

from django.core.exceptions import ValidationError


MAX_UPLOAD_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo

PHONE_NUMBER_MESSAGE = (
    "Le numéro de téléphone doit être au format international, "
    "ex : +237 6XX XXX XXX (indicatif pays inclus, 8 à 15 chiffres)."
)
_PHONE_SEPARATORS_RE = re.compile(r'[\s().\-]')
_PHONE_NUMBER_RE = re.compile(r'^\+?\d{8,15}$')


def validate_file_size(value):
    """Validateur pour la taille des fichiers (max 5Mo)"""
    filesize = value.size
    if filesize > MAX_UPLOAD_FILE_SIZE:
        raise ValidationError("La taille du fichier ne doit pas dépasser 5 Mo.")
    return value


def validate_phone_number(value):
    """Valide un numéro de téléphone au format international (E.164).

    Les séparateurs courants (espaces, points, tirets, parenthèses) sont ignorés ;
    le numéro normalisé doit comporter 8 à 15 chiffres, précédés d'un « + » facultatif.
    """
    if value in (None, ''):
        return value
    normalized = _PHONE_SEPARATORS_RE.sub('', str(value))
    if not _PHONE_NUMBER_RE.match(normalized):
        raise ValidationError(PHONE_NUMBER_MESSAGE)
    return value
