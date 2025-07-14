"""
Configuration personnalisée pour l'administration Django YSEM
"""

from django.contrib import admin


def configure_admin_site():
    """Configure le site d'administration YSEM"""
    admin.site.site_header = "Administration YSEM"
    admin.site.site_title = "Administration YSEM"
    admin.site.index_title = "Panneau d'administration YSEM"


# Appliquer la configuration
configure_admin_site()
