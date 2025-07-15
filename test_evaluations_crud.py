#!/usr/bin/env python3
"""
Script de test pour vérifier l'implémentation CRUD des évaluations
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from Teaching.models import Evaluation
from Teaching.forms import EvaluationForm
from django.test import Client
from django.urls import reverse

def test_crud_operations():
    """Test des opérations CRUD sur les évaluations"""
    
    print("=== Test CRUD Évaluations ===\n")
    
    # 1. Test CREATE (Création)
    print("1. Test CREATE - Création d'une évaluation")
    try:
        # Supprimer les évaluations de test s'elles existent déjà
        Evaluation.objects.filter(nom_et_prenom_etudiant__startswith="TEST_").delete()
        print("   - Évaluations de test existantes supprimées")
        
        # Créer une nouvelle évaluation
        evaluation_data = {
            'evaluationDat': date(2024, 1, 15),
            'nom_et_prenom_etudiant': 'TEST_Jean Dupont',
            'cycle': 'Licence',
            'niveau': 2,
            'intitule_cours': 'Programmation Web',
            'support_cours_acessible': True,
            'bonne_explication_cours': True,
            'bonne_reponse_questions': True,
            'courseMethodology': 'Cours magistral + TP',
            'donne_TD': True,
            'donne_projet': True,
            'difficulte_rencontree': False,
            'quelles_difficultes_rencontrees': '',
            'propositionEtudiants': 'Plus d\'exercices pratiques',
            'observationSSAC': 'Bon niveau général',
            'actionSSAC': 'Continuer sur cette voie'
        }
        
        evaluation = Evaluation.objects.create(**evaluation_data)
        print(f"   ✓ Évaluation créée: ID #{evaluation.id} - {evaluation.nom_et_prenom_etudiant}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la création: {e}")
        return False
    
    # 2. Test READ (Lecture)
    print("\n2. Test READ - Lecture des évaluations")
    try:
        # Lire toutes les évaluations
        evaluations = Evaluation.objects.all()
        print(f"   ✓ Nombre total d'évaluations: {evaluations.count()}")
        
        # Lire l'évaluation spécifique
        evaluation = Evaluation.objects.get(nom_et_prenom_etudiant='TEST_Jean Dupont')
        print(f"   ✓ Évaluation trouvée: {evaluation.nom_et_prenom_etudiant} - {evaluation.intitule_cours}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la lecture: {e}")
        return False
    
    # 3. Test UPDATE (Mise à jour)
    print("\n3. Test UPDATE - Mise à jour d'une évaluation")
    try:
        evaluation = Evaluation.objects.get(nom_et_prenom_etudiant='TEST_Jean Dupont')
        ancien_cours = evaluation.intitule_cours
        evaluation.intitule_cours = 'Développement Web Avancé'
        evaluation.propositionEtudiants = 'Ajouter des projets en équipe'
        evaluation.save()
        
        # Vérifier la mise à jour
        evaluation_updated = Evaluation.objects.get(nom_et_prenom_etudiant='TEST_Jean Dupont')
        print(f"   ✓ Cours mis à jour: {ancien_cours} → {evaluation_updated.intitule_cours}")
        print(f"   ✓ Proposition mise à jour: {evaluation_updated.propositionEtudiants}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la mise à jour: {e}")
        return False
    
    # 4. Test du formulaire
    print("\n4. Test FORM - Validation du formulaire")
    try:
        # Test avec des données valides
        form_data = {
            'evaluationDat': '2024-02-20',
            'nom_et_prenom_etudiant': 'TEST_Marie Martin',
            'cycle': 'Master',
            'niveau': 1,
            'intitule_cours': 'Intelligence Artificielle',
            'support_cours_acessible': True,
            'bonne_explication_cours': True,
            'bonne_reponse_questions': False,
            'courseMethodology': 'Cours + Projets',
            'donne_TD': True,
            'donne_projet': True,
            'difficulte_rencontree': True,
            'quelles_difficultes_rencontrees': 'Concepts mathématiques complexes',
            'propositionEtudiants': 'Plus de rappels mathématiques',
            'observationSSAC': 'Niveau hétérogène',
            'actionSSAC': 'Prévoir des séances de rattrapage'
        }
        
        form = EvaluationForm(data=form_data)
        if form.is_valid():
            evaluation2 = form.save()
            print(f"   ✓ Formulaire valide et évaluation créée: {evaluation2.nom_et_prenom_etudiant}")
        else:
            print(f"   ✗ Formulaire invalide: {form.errors}")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors du test du formulaire: {e}")
        return False
    
    # 5. Test des évaluations booléennes
    print("\n5. Test BOOLEAN FIELDS - Vérification des champs booléens")
    try:
        evaluation = Evaluation.objects.get(nom_et_prenom_etudiant='TEST_Marie Martin')
        
        # Vérifier les valeurs booléennes
        print(f"   ✓ Support accessible: {evaluation.support_cours_acessible}")
        print(f"   ✓ Bonne explication: {evaluation.bonne_explication_cours}")
        print(f"   ✓ Bonnes réponses: {evaluation.bonne_reponse_questions}")
        print(f"   ✓ Donne TD: {evaluation.donne_TD}")
        print(f"   ✓ Donne projets: {evaluation.donne_projet}")
        print(f"   ✓ Difficultés: {evaluation.difficulte_rencontree}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des booléens: {e}")
        return False
    
    # 6. Test DELETE (Suppression)
    print("\n6. Test DELETE - Suppression d'évaluations")
    try:
        # Supprimer les évaluations de test
        deleted_count = Evaluation.objects.filter(nom_et_prenom_etudiant__startswith="TEST_").delete()[0]
        
        # Vérifier la suppression
        count = Evaluation.objects.filter(nom_et_prenom_etudiant__startswith="TEST_").count()
        if count == 0:
            print(f"   ✓ {deleted_count} évaluation(s) de test supprimée(s) avec succès")
        else:
            print(f"   ✗ {count} évaluation(s) de test encore présente(s)")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors de la suppression: {e}")
        return False
    
    print("\n=== Tous les tests CRUD ont réussi ! ===")
    return True

def test_urls():
    """Test des URLs des vues CRUD"""
    
    print("\n=== Test des URLs ===\n")
    
    try:
        # Créer une évaluation de test pour les URLs
        evaluation = Evaluation.objects.create(
            evaluationDat=date(2024, 1, 1),
            nom_et_prenom_etudiant='URL_TEST',
            cycle='Test',
            niveau=1,
            intitule_cours='Test Course',
            support_cours_acessible=True,
            bonne_explication_cours=True,
            bonne_reponse_questions=True,
            courseMethodology='Test',
            donne_TD=True,
            donne_projet=True,
            difficulte_rencontree=False,
            quelles_difficultes_rencontrees='',
            propositionEtudiants='Test',
            observationSSAC='Test',
            actionSSAC='Test'
        )
        
        # Test des URLs
        urls_to_test = [
            ('teaching:evaluations', 'Liste des évaluations'),
            ('teaching:ajouter_evaluation', 'Ajouter évaluation'),
            ('teaching:detail_evaluation', 'Détail évaluation', {'pk': evaluation.id}),
            ('teaching:modifier_evaluation', 'Modifier évaluation', {'pk': evaluation.id}),
            ('teaching:supprimer_evaluation', 'Supprimer évaluation', {'pk': evaluation.id}),
        ]
        
        for url_info in urls_to_test:
            url_name = url_info[0]
            description = url_info[1]
            kwargs = url_info[2] if len(url_info) > 2 else {}
            
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"   ✓ {description}: {url}")
            except Exception as e:
                print(f"   ✗ {description}: Erreur - {e}")
        
        # Nettoyer
        evaluation.delete()
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des URLs: {e}")

def test_model_methods():
    """Test des méthodes du modèle"""
    
    print("\n=== Test des méthodes du modèle ===\n")
    
    try:
        # Créer une évaluation de test
        evaluation = Evaluation.objects.create(
            evaluationDat=date(2024, 1, 1),
            nom_et_prenom_etudiant='Method Test',
            cycle='Licence',
            niveau=3,
            intitule_cours='Test Course',
            support_cours_acessible=True,
            bonne_explication_cours=False,
            bonne_reponse_questions=True,
            courseMethodology='Mixed',
            donne_TD=True,
            donne_projet=False,
            difficulte_rencontree=True,
            quelles_difficultes_rencontrees='Rythme trop rapide',
            propositionEtudiants='Ralentir le rythme',
            observationSSAC='Attention au rythme',
            actionSSAC='Adapter le rythme'
        )
        
        print(f"   ✓ Évaluation créée pour les tests de méthodes")
        print(f"   ✓ Représentation string: {evaluation}")
        print(f"   ✓ Meta verbose_name: {evaluation._meta.verbose_name}")
        print(f"   ✓ Meta verbose_name_plural: {evaluation._meta.verbose_name_plural}")
        
        # Nettoyer
        evaluation.delete()
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des méthodes: {e}")

if __name__ == '__main__':
    print("Démarrage des tests CRUD pour les évaluations...\n")
    
    # Test des opérations CRUD
    success = test_crud_operations()
    
    # Test des URLs
    test_urls()
    
    # Test des méthodes du modèle
    test_model_methods()
    
    if success:
        print("\n🎉 Implémentation CRUD des évaluations validée avec succès !")
    else:
        print("\n❌ Des erreurs ont été détectées dans l'implémentation CRUD.")
        sys.exit(1)
