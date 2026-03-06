"""
Configuration des applications YSEM
"""

from django.apps import AppConfig
from django.contrib import admin


class YsemConfig(AppConfig):
    """Configuration principale de YSEM"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ysem'
    
