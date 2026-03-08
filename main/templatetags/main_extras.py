import os

from django import template


register = template.Library()


@register.filter
def basename(value):
    """Retourne le nom final d'un chemin de fichier."""
    if not value:
        return ''
    return os.path.basename(str(value))