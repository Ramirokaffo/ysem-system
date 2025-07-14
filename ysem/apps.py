"""
Configuration des applications YSEM
"""

from django.apps import AppConfig
from django.contrib import admin


class YsemConfig(AppConfig):
    """Configuration principale de YSEM"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ysem'
    
    def ready(self):
        """Configuration à exécuter quand l'application est prête"""
        # Configuration du site d'administration
        admin.site.site_header = "Administration YSEM"
        admin.site.site_title = "Administration YSEM"
        admin.site.index_title = "Panneau d'administration YSEM"
