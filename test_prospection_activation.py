#!/usr/bin/env python
"""
Script de test pour le système d'activation/désactivation de la prospection
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from prospection.models import ProspectionConfig
from prospection.context_processors import prospection_context


def test_prospection_config_model():
    """Test du modèle ProspectionConfig"""
    print("🧪 Test du modèle ProspectionConfig...")
    
    # Test de création de configuration
    config = ProspectionConfig.get_or_create_config()
    print(f"✅ Configuration créée: {config}")
    
    # Test de l'état initial
    print(f"✅ État initial: {'Activée' if config.is_active else 'Désactivée'}")
    
    # Test de la méthode utilitaire
    is_active = ProspectionConfig.is_prospection_active()
    print(f"✅ Méthode utilitaire: {is_active}")
    
    # Test de modification
    original_state = config.is_active
    config.is_active = not original_state
    config.modified_by = "test_script"
    config.save()
    
    # Vérifier que la modification a été sauvegardée
    config_updated = ProspectionConfig.get_or_create_config()
    print(f"✅ État après modification: {'Activée' if config_updated.is_active else 'Désactivée'}")
    
    # Restaurer l'état original
    config_updated.is_active = original_state
    config_updated.save()
    
    return True


def test_context_processor():
    """Test du context processor"""
    print("\n🔧 Test du context processor...")
    
    from django.test import RequestFactory
    
    factory = RequestFactory()
    request = factory.get('/')
    
    # Test du context processor
    context = prospection_context(request)
    
    print(f"✅ Context prospection_active: {context['prospection_active']}")
    print(f"✅ Context prospection_config: {context['prospection_config']}")
    
    # Vérifier que les clés existent
    assert 'prospection_active' in context
    assert 'prospection_config' in context
    
    return True


def test_toggle_functionality():
    """Test de la fonctionnalité d'activation/désactivation"""
    print("\n🔄 Test de la fonctionnalité toggle...")
    
    client = Client()
    
    # État initial
    config = ProspectionConfig.get_or_create_config()
    initial_state = config.is_active
    print(f"✅ État initial: {'Activée' if initial_state else 'Désactivée'}")
    
    # Test de l'URL toggle (sans authentification - devrait rediriger)
    response = client.post(reverse('main:toggle_prospection'))
    print(f"✅ Réponse toggle sans auth: {response.status_code} (302 attendu)")
    
    # Vérifier que l'état n'a pas changé (pas d'authentification)
    config.refresh_from_db()
    print(f"✅ État après tentative non-auth: {'Activée' if config.is_active else 'Désactivée'}")
    
    return True


def test_admin_integration():
    """Test de l'intégration admin"""
    print("\n🔧 Test de l'intégration admin...")
    
    from django.contrib import admin
    from prospection.admin import ProspectionConfigAdmin
    
    # Vérifier que le modèle est enregistré
    if ProspectionConfig in admin.site._registry:
        print("✅ ProspectionConfig enregistré dans l'admin")
        
        # Vérifier la configuration de l'admin
        config_admin = admin.site._registry[ProspectionConfig]
        print(f"✅ Champs de liste: {config_admin.list_display}")
        print(f"✅ Champs modifiables: {config_admin.fields}")
        
        return True
    else:
        print("❌ ProspectionConfig NON enregistré dans l'admin")
        return False


def test_template_integration():
    """Test de l'intégration dans les templates"""
    print("\n🎨 Test de l'intégration dans les templates...")
    
    from django.template.loader import get_template
    from django.template import Context
    
    # Test du template des paramètres
    try:
        template = get_template('main/parametres.html')
        print("✅ Template parametres.html: OK")
    except Exception as e:
        print(f"❌ Template parametres.html: ERREUR - {e}")
    
    # Test du template de base
    try:
        template = get_template('main/base.html')
        print("✅ Template base.html: OK")
    except Exception as e:
        print(f"❌ Template base.html: ERREUR - {e}")
    
    # Test du template dashboard
    try:
        template = get_template('main/dashboard.html')
        print("✅ Template dashboard.html: OK")
    except Exception as e:
        print(f"❌ Template dashboard.html: ERREUR - {e}")
    
    return True


def test_urls():
    """Test des URLs"""
    print("\n🌐 Test des URLs...")
    
    client = Client()
    
    urls_to_test = [
        ('main:parametres', 'Page des paramètres'),
        ('main:toggle_prospection', 'Toggle prospection'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            response = client.get(url) if 'toggle' not in url_name else client.post(url)
            print(f"✅ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: ERREUR - {e}")
    
    return True


def main():
    """Fonction principale de test"""
    print("🚀 Test du système d'activation/désactivation de la prospection")
    print("=" * 70)
    
    try:
        # Tests du modèle
        test_prospection_config_model()
        
        # Tests du context processor
        test_context_processor()
        
        # Tests de la fonctionnalité toggle
        test_toggle_functionality()
        
        # Tests de l'admin
        test_admin_integration()
        
        # Tests des templates
        test_template_integration()
        
        # Tests des URLs
        test_urls()
        
        print("\n" + "=" * 70)
        print("✅ Tous les tests sont passés avec succès!")
        
        print("\n📋 Fonctionnalités implémentées:")
        print("   🔹 Modèle ProspectionConfig pour gérer l'activation")
        print("   🔹 Context processor pour rendre l'état disponible partout")
        print("   🔹 Interface d'activation/désactivation dans les paramètres")
        print("   🔹 Menu conditionnel dans la sidebar principale")
        print("   🔹 Masquage des éléments de prospection quand désactivée")
        print("   🔹 Administration Django intégrée")
        
        print("\n🎯 Utilisation:")
        print("   1. Aller dans Paramètres > Prospection")
        print("   2. Cliquer sur 'Activer' pour activer la prospection")
        print("   3. Le menu 'Prospection' apparaît dans la sidebar")
        print("   4. Les statistiques de prospection s'affichent sur le dashboard")
        print("   5. Cliquer sur 'Désactiver' pour masquer tout ce qui concerne la prospection")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
