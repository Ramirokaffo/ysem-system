"""
Context processors pour le module de prospection
"""

from .models import ProspectionConfig


def prospection_context(request):
    """
    Context processor pour rendre la configuration de prospection 
    disponible dans tous les templates
    """
    return {
        'prospection_active': ProspectionConfig.is_prospection_active(),
        'prospection_config': ProspectionConfig.get_or_create_config(),
    }
