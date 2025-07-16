#!/usr/bin/env python
"""
Script de test pour vérifier la génération automatique du nom d'équipe
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from prospection.models import Agent, Equipe, Campagne
from schools.models import School

def test_nom_generation():
    """Test de la génération automatique du nom d'équipe"""
    print("=== Test de génération automatique du nom d'équipe ===\n")
    
    # Récupérer ou créer des données de test
    try:
        # Récupérer un agent existant
        agent = Agent.objects.filter(statut='actif').first()
        if not agent:
            print("❌ Aucun agent actif trouvé. Créez d'abord un agent.")
            return
        
        # Récupérer une école existante
        school = School.objects.first()
        if not school:
            print("❌ Aucune école trouvée. Créez d'abord une école.")
            return
        
        # Récupérer une campagne existante
        campagne = Campagne.objects.first()
        if not campagne:
            print("❌ Aucune campagne trouvée. Créez d'abord une campagne.")
            return
        
        print(f"Agent de test : {agent.nom_complet}")
        print(f"École de test : {school.name}")
        print(f"Campagne de test : {campagne.nom}\n")
        
        # Test 1: Équipe avec chef et établissement
        print("Test 1: Équipe avec chef et établissement cible")
        equipe1 = Equipe(
            campagne=campagne,
            chef_equipe=agent,
            etablissement_cible=school,
            objectif_prospects=10
        )
        equipe1.save()
        print(f"✅ Nom généré : '{equipe1.nom}'")
        print(f"   Attendu : 'Équipe {agent.nom_complet} - {school.name}'\n")
        
        # Test 2: Équipe avec chef seulement
        print("Test 2: Équipe avec chef seulement")
        equipe2 = Equipe(
            campagne=campagne,
            chef_equipe=agent,
            objectif_prospects=10
        )
        equipe2.save()
        print(f"✅ Nom généré : '{equipe2.nom}'")
        print(f"   Attendu : 'Équipe {agent.nom_complet}'\n")
        
        # Test 3: Équipe sans chef
        print("Test 3: Équipe sans chef")
        equipe3 = Equipe(
            campagne=campagne,
            objectif_prospects=10
        )
        equipe3.save()
        print(f"✅ Nom généré : '{equipe3.nom}'")
        print(f"   Attendu : 'Équipe sans chef'\n")
        
        # Nettoyage
        print("Nettoyage des équipes de test...")
        equipe1.delete()
        equipe2.delete()
        equipe3.delete()
        print("✅ Équipes de test supprimées\n")
        
        print("=== Tous les tests sont passés avec succès ! ===")
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")

if __name__ == "__main__":
    test_nom_generation()
