from django import template

register = template.Library()


@register.filter(name='initials')
def initials(value, max_chars=2):
    """Retourne les initiales d'un nom complet (1 ou 2 lettres majuscules)."""
    if not value:
        return ''
    parts = [p for p in str(value).strip().split() if p]
    if not parts:
        return ''
    letters = [p[0] for p in parts[:max_chars]]
    return ''.join(letters).upper()
