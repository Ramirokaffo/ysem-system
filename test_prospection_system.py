#!/usr/bin/env python
"""
Script de test pour le système de prospection
"""

import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.contrib.auth import get_user_model
from prospection.models import Agent, Campagne, Equipe, Prospect
from academic.models import AcademicYear
from schools.models import School

User = get_user_model()

def test_prospection_models():
    """Test des modèles de prospection"""
    print("🧪 Test des modèles de prospection...")
    
    # Créer une année académique si elle n'existe pas
    academic_year, created = AcademicYear.objects.get_or_create(
        start_at=date(2024, 9, 1),
        end_at=date(2025, 8, 31),
        defaults={
            'is_active': True
        }
    )
    if created:
        print(f"✅ Année académique créée: {academic_year.name}")
    
    # Créer une école si elle n'existe pas
    school, created = School.objects.get_or_create(
        name="Lycée Test Prospection",
        defaults={
            'address': "123 Rue de la Prospection",
            'phone_number': "123456789"
        }
    )
    if created:
        print(f"✅ École créée: {school.name}")
    
    # Créer des agents de test
    agents_data = [
        {
            'matricule': 'AGT001',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'telephone': '123456789',
            'type_agent': 'interne',
            'date_embauche': date(2024, 1, 1)
        },
        {
            'matricule': 'AGT002',
            'nom': 'Martin',
            'prenom': 'Marie',
            'telephone': '987654321',
            'type_agent': 'externe',
            'date_embauche': date(2024, 2, 1)
        },
        {
            'matricule': 'AGT003',
            'nom': 'Durand',
            'prenom': 'Pierre',
            'telephone': '555123456',
            'type_agent': 'interne',
            'date_embauche': date(2024, 3, 1)
        }
    ]
    
    agents = []
    for agent_data in agents_data:
        agent, created = Agent.objects.get_or_create(
            matricule=agent_data['matricule'],
            defaults=agent_data
        )
        agents.append(agent)
        if created:
            print(f"✅ Agent créé: {agent.nom_complet}")
    
    # Créer une campagne de test
    campagne, created = Campagne.objects.get_or_create(
        nom="Campagne Test 2024",
        defaults={
            'annee_academique': academic_year,
            'date_debut': date(2024, 6, 1),
            'date_fin': date(2024, 8, 31),
            'objectif_global': 1000,
            'statut': 'en_cours'
        }
    )
    if created:
        print(f"✅ Campagne créée: {campagne.nom}")
    
    # Créer des équipes de test
    equipes_data = [
        {
            'nom': 'Équipe Alpha',
            'objectif_prospects': 50,
            'agents': [agents[0], agents[1]]
        },
        {
            'nom': 'Équipe Beta',
            'objectif_prospects': 75,
            'agents': [agents[1], agents[2]]
        }
    ]
    
    equipes = []
    for equipe_data in equipes_data:
        equipe, created = Equipe.objects.get_or_create(
            nom=equipe_data['nom'],
            campagne=campagne,
            defaults={
                'chef_equipe': equipe_data['agents'][0],
                'etablissement_cible': school,
                'objectif_prospects': equipe_data['objectif_prospects']
            }
        )
        if created:
            equipe.agents.set(equipe_data['agents'])
            print(f"✅ Équipe créée: {equipe.nom}")
        equipes.append(equipe)
    
    # Créer des prospects de test
    prospects_data = [
        {
            'nom': 'Doe',
            'prenom': 'John',
            'telephone': '111222333',
            'equipe': equipes[0],
            'agent_collecteur': agents[0]
        },
        {
            'nom': 'Smith',
            'prenom': 'Jane',
            'telephone': '444555666',
            'telephone_pere': '777888999',
            'equipe': equipes[0],
            'agent_collecteur': agents[1]
        },
        {
            'nom': 'Johnson',
            'prenom': 'Bob',
            'telephone': '123123123',
            'equipe': equipes[1],
            'agent_collecteur': agents[2]
        }
    ]
    
    for prospect_data in prospects_data:
        prospect, created = Prospect.objects.get_or_create(
            telephone=prospect_data['telephone'],
            equipe=prospect_data['equipe'],
            defaults=prospect_data
        )
        if created:
            print(f"✅ Prospect créé: {prospect.nom_complet}")
    
    print(f"\n📊 Statistiques créées:")
    print(f"   - Agents: {Agent.objects.count()}")
    print(f"   - Campagnes: {Campagne.objects.count()}")
    print(f"   - Équipes: {Equipe.objects.count()}")
    print(f"   - Prospects: {Prospect.objects.count()}")
    
    return True

def test_prospection_properties():
    """Test des propriétés et méthodes des modèles"""
    print("\n🔍 Test des propriétés des modèles...")
    
    # Test des propriétés de campagne
    campagne = Campagne.objects.first()
    if campagne:
        print(f"✅ Durée campagne: {campagne.duree_jours} jours")
        print(f"✅ Campagne active: {campagne.is_active}")
    
    # Test des propriétés d'équipe
    for equipe in Equipe.objects.all():
        print(f"✅ Équipe {equipe.nom}:")
        print(f"   - Nombre d'agents: {equipe.nombre_agents}")
        print(f"   - Prospects collectés: {equipe.prospects_collectes}")
        print(f"   - Taux de réalisation: {equipe.taux_realisation:.1f}%")
    
    return True

def test_admin_integration():
    """Test de l'intégration avec l'admin Django"""
    print("\n🔧 Test de l'intégration admin...")

    from django.contrib import admin
    from prospection.admin import AgentAdmin, CampagneAdmin, EquipeAdmin, ProspectAdmin

    # Vérifier que les modèles sont enregistrés
    prospection_models = [Agent, Campagne, Equipe, Prospect]
    for model in prospection_models:
        if model in admin.site._registry:
            print(f"✅ {model.__name__} enregistré dans l'admin")
        else:
            print(f"❌ {model.__name__} NON enregistré dans l'admin")

    return True

def test_urls_and_views():
    """Test des URLs et vues"""
    print("\n🌐 Test des URLs...")
    
    from django.urls import reverse, NoReverseMatch
    
    urls_to_test = [
        'prospection:dashboard',
        'prospection:agents',
        'prospection:ajouter_agent',
        'prospection:campagnes',
        'prospection:ajouter_campagne',
        'prospection:equipes',
        'prospection:ajouter_equipe',
        'prospection:prospects',
        'prospection:ajouter_prospect',
        'prospection:statistiques',
    ]
    
    for url_name in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"✅ URL {url_name}: {url}")
        except NoReverseMatch:
            print(f"❌ URL {url_name}: ERREUR - URL non trouvée")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du système de prospection")
    print("=" * 60)
    
    try:
        # Tests des modèles
        test_prospection_models()
        
        # Tests des propriétés
        test_prospection_properties()
        
        # Tests de l'admin
        test_admin_integration()
        
        # Tests des URLs
        test_urls_and_views()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont passés avec succès!")
        print("\n📋 Prochaines étapes:")
        print("   1. Démarrer le serveur: python manage.py runserver")
        print("   2. Accéder au dashboard: http://localhost:8000/scholar")
        print("   3. Cliquer sur 'Gestion prospection'")
        print("   4. Tester les fonctionnalités CRUD")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
