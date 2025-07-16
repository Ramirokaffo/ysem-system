#!/usr/bin/env python
"""
Script de test pour les templates de prospection
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.template.loader import get_template
from django.template import Context, RequestContext
from django.test import RequestFactory

def test_templates():
    """Test des templates de prospection"""
    print("🧪 Test des templates de prospection...")
    
    factory = RequestFactory()
    request = factory.get('/prospection/')
    
    templates_to_test = [
        'prospection/base.html',
        'prospection/dashboard.html',
        'prospection/agents.html',
        'prospection/ajouter_agent.html',
        'prospection/campagnes.html',
        'prospection/ajouter_campagne.html',
        'prospection/detail_agent.html',
        'prospection/modifier_agent.html',
        'prospection/detail_campagne.html',
        'prospection/modifier_campagne.html',
        'prospection/equipes.html',
        'prospection/ajouter_equipe.html',
        'prospection/detail_equipe.html',
        'prospection/modifier_equipe.html',
        'prospection/prospects.html',
        'prospection/ajouter_prospect.html',
        'prospection/detail_prospect.html',
        'prospection/modifier_prospect.html',
        'prospection/statistiques.html',
    ]
    
    for template_name in templates_to_test:
        try:
            template = get_template(template_name)
            print(f"✅ Template {template_name}: OK")
        except Exception as e:
            print(f"❌ Template {template_name}: ERREUR - {e}")
    
    return True

if __name__ == "__main__":
    test_templates()
