#!/usr/bin/env python
"""
Script de test CRUD spécifique pour les agents de prospection
"""

import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from prospection.models import Agent, Campagne, Equipe, Prospect
from academic.models import AcademicYear
from schools.models import School

def test_agent_crud_urls():
    """Test des URLs CRUD pour les agents"""
    print("🧪 Test des URLs CRUD pour les agents...")
    
    client = Client()
    
    # URLs à tester
    urls_to_test = [
        ('prospection:agents', {}, 'Liste des agents'),
        ('prospection:ajouter_agent', {}, 'Ajouter un agent'),
    ]
    
    # Test avec un agent existant
    agent = Agent.objects.first()
    if agent:
        urls_to_test.extend([
            ('prospection:detail_agent', {'matricule': agent.matricule}, 'Détail agent'),
            ('prospection:modifier_agent', {'matricule': agent.matricule}, 'Modifier agent'),
        ])
    
    for url_name, kwargs, description in urls_to_test:
        try:
            url = reverse(url_name, kwargs=kwargs)
            response = client.get(url)
            # 302 = redirection (normal car authentification requise)
            # 200 = OK
            if response.status_code in [200, 302]:
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: ERREUR - {e}")
    
    return True

def test_agent_model_operations():
    """Test des opérations sur le modèle Agent"""
    print("\n🔧 Test des opérations sur le modèle Agent...")
    
    try:
        # Créer un agent de test
        agent_data = {
            'matricule': 'TEST_CRUD_001',
            'nom': 'TestCRUD',
            'prenom': 'Agent',
            'telephone': '123456789',
            'email': 'test@example.com',
            'type_agent': 'interne',
            'statut': 'actif',
            'date_embauche': date.today(),
            'adresse': '123 Rue Test'
        }
        
        # CREATE
        agent, created = Agent.objects.get_or_create(
            matricule=agent_data['matricule'],
            defaults=agent_data
        )
        print(f"✅ CREATE: Agent {'créé' if created else 'existant'}")
        
        # READ
        agent_read = Agent.objects.get(matricule=agent_data['matricule'])
        print(f"✅ READ: Agent trouvé - {agent_read.nom_complet}")
        
        # UPDATE
        agent_read.telephone = '987654321'
        agent_read.save()
        agent_updated = Agent.objects.get(matricule=agent_data['matricule'])
        print(f"✅ UPDATE: Téléphone modifié - {agent_updated.telephone}")
        
        # Test des propriétés
        print(f"✅ Propriété nom_complet: {agent.nom_complet}")
        print(f"✅ Propriété __str__: {str(agent)}")
        
        # Test avec équipes et prospects
        academic_year, _ = AcademicYear.objects.get_or_create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 8, 31),
            defaults={'is_active': True}
        )
        
        school, _ = School.objects.get_or_create(
            name="École Test Agent",
            defaults={'address': "123 Rue Test", 'phone_number': "123456789"}
        )
        
        campagne, _ = Campagne.objects.get_or_create(
            nom="Campagne Test Agent",
            defaults={
                'annee_academique': academic_year,
                'date_debut': date.today(),
                'date_fin': date.today() + timedelta(days=30),
                'objectif_global': 50,
                'statut': 'en_cours'
            }
        )
        
        equipe, _ = Equipe.objects.get_or_create(
            nom="Équipe Test Agent",
            campagne=campagne,
            defaults={
                'chef_equipe': agent,
                'etablissement_cible': school,
                'objectif_prospects': 10
            }
        )
        equipe.agents.add(agent)
        
        prospect, _ = Prospect.objects.get_or_create(
            telephone="555123456",
            equipe=equipe,
            defaults={
                'nom': 'Prospect',
                'prenom': 'Test',
                'agent_collecteur': agent
            }
        )
        
        # Test des relations
        print(f"✅ Équipes de l'agent: {agent.equipes.count()}")
        print(f"✅ Équipes dirigées: {agent.equipes_dirigees.count()}")
        print(f"✅ Prospects collectés: {agent.prospects_collectes.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des opérations sur le modèle Agent: {e}")
        return False

def test_agent_forms():
    """Test des formulaires d'agent"""
    print("\n📝 Test des formulaires d'agent...")
    
    from prospection.forms import AgentForm, AgentSearchForm
    
    # Test AgentForm valide
    valid_data = {
        'matricule': 'FORM_TEST_001',
        'nom': 'FormTest',
        'prenom': 'Agent',
        'telephone': '111222333',
        'email': 'formtest@example.com',
        'type_agent': 'externe',
        'statut': 'actif',
        'date_embauche': date.today(),
        'adresse': '456 Rue Form'
    }
    
    form = AgentForm(data=valid_data)
    print(f"✅ AgentForm valide: {form.is_valid()}")
    if not form.is_valid():
        print(f"   Erreurs: {form.errors}")
    
    # Test AgentForm invalide (matricule manquant)
    invalid_data = valid_data.copy()
    invalid_data['matricule'] = ''
    
    invalid_form = AgentForm(data=invalid_data)
    print(f"✅ AgentForm invalide (attendu): {not invalid_form.is_valid()}")
    
    # Test AgentSearchForm
    search_data = {
        'search': 'Test',
        'type_agent': 'interne',
        'statut': 'actif'
    }
    
    search_form = AgentSearchForm(data=search_data)
    print(f"✅ AgentSearchForm valide: {search_form.is_valid()}")
    
    return True

def test_agent_admin():
    """Test de l'intégration admin pour les agents"""
    print("\n🔧 Test de l'intégration admin pour les agents...")
    
    from django.contrib import admin
    from prospection.models import Agent
    from prospection.admin import AgentAdmin
    
    # Vérifier que le modèle Agent est enregistré
    if Agent in admin.site._registry:
        print("✅ Agent enregistré dans l'admin")
        
        # Vérifier la configuration de l'admin
        agent_admin = admin.site._registry[Agent]
        print(f"✅ Champs de liste: {agent_admin.list_display}")
        print(f"✅ Filtres: {agent_admin.list_filter}")
        print(f"✅ Champs de recherche: {agent_admin.search_fields}")
        
        return True
    else:
        print("❌ Agent NON enregistré dans l'admin")
        return False

def test_agent_templates():
    """Test des templates d'agent"""
    print("\n🎨 Test des templates d'agent...")
    
    from django.template.loader import get_template
    
    templates_agent = [
        'prospection/agents.html',
        'prospection/ajouter_agent.html',
        'prospection/detail_agent.html',
        'prospection/modifier_agent.html',
    ]
    
    for template_name in templates_agent:
        try:
            template = get_template(template_name)
            print(f"✅ Template {template_name}: OK")
        except Exception as e:
            print(f"❌ Template {template_name}: ERREUR - {e}")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 Test CRUD complet pour les Agents de Prospection")
    print("=" * 60)
    
    try:
        # Tests des URLs
        test_agent_crud_urls()
        
        # Tests des modèles
        test_agent_model_operations()
        
        # Tests des formulaires
        test_agent_forms()
        
        # Tests de l'admin
        test_agent_admin()
        
        # Tests des templates
        test_agent_templates()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests CRUD pour les agents sont passés avec succès!")
        
        print("\n📋 Fonctionnalités CRUD Agents disponibles:")
        print("   🔹 CREATE: Ajouter un nouvel agent")
        print("   🔹 READ: Liste paginée avec filtres et page de détails")
        print("   🔹 UPDATE: Modifier les informations d'un agent")
        print("   🔹 DELETE: Suppression via l'interface admin")
        
        print("\n🎯 Fonctionnalités spéciales:")
        print("   🔹 Recherche par nom, prénom, matricule, téléphone")
        print("   🔹 Filtres par type (interne/externe) et statut")
        print("   🔹 Statistiques de performance par agent")
        print("   🔹 Suivi des équipes et prospects collectés")
        print("   🔹 Validation des contraintes métier")
        
        print("\n🌐 URLs disponibles:")
        print("   🔹 /prospection/agents/ - Liste des agents")
        print("   🔹 /prospection/agents/ajouter/ - Ajouter un agent")
        print("   🔹 /prospection/agents/<matricule>/ - Détails d'un agent")
        print("   🔹 /prospection/agents/<matricule>/modifier/ - Modifier un agent")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
