#!/usr/bin/env python3
"""
Script de test pour vérifier l'implémentation CRUD des enseignants
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from Teaching.models import Lecturer
from Teaching.forms import EnseignantForm
from django.test import Client
from django.urls import reverse

def test_crud_operations():
    """Test des opérations CRUD sur les enseignants"""
    
    print("=== Test CRUD Enseignants ===\n")
    
    # 1. Test CREATE (Création)
    print("1. Test CREATE - Création d'un enseignant")
    try:
        # Supprimer l'enseignant de test s'il existe déjà
        try:
            existing = Lecturer.objects.get(matricule="TEST001")
            existing.delete()
            print("   - Enseignant de test existant supprimé")
        except Lecturer.DoesNotExist:
            pass
        
        # Créer un nouvel enseignant
        enseignant_data = {
            'matricule': 'TEST001',
            'firstname': 'Jean',
            'lastname': 'Dupont',
            'date_naiss': date(1980, 5, 15),
            'grade': 'Professeur',
            'gender': 'M',
            'lang': 'fr',
            'phone_number': '+237123456789',
            'email': 'jean.dupont@ysem.edu'
        }
        
        enseignant = Lecturer.objects.create(**enseignant_data)
        print(f"   ✓ Enseignant créé: {enseignant}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la création: {e}")
        return False
    
    # 2. Test READ (Lecture)
    print("\n2. Test READ - Lecture des enseignants")
    try:
        # Lire tous les enseignants
        enseignants = Lecturer.objects.all()
        print(f"   ✓ Nombre total d'enseignants: {enseignants.count()}")
        
        # Lire l'enseignant spécifique
        enseignant = Lecturer.objects.get(matricule='TEST001')
        print(f"   ✓ Enseignant trouvé: {enseignant.firstname} {enseignant.lastname}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la lecture: {e}")
        return False
    
    # 3. Test UPDATE (Mise à jour)
    print("\n3. Test UPDATE - Mise à jour d'un enseignant")
    try:
        enseignant = Lecturer.objects.get(matricule='TEST001')
        ancien_grade = enseignant.grade
        enseignant.grade = 'Professeur Titulaire'
        enseignant.phone_number = '+237987654321'
        enseignant.save()
        
        # Vérifier la mise à jour
        enseignant_updated = Lecturer.objects.get(matricule='TEST001')
        print(f"   ✓ Grade mis à jour: {ancien_grade} → {enseignant_updated.grade}")
        print(f"   ✓ Téléphone mis à jour: {enseignant_updated.phone_number}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la mise à jour: {e}")
        return False
    
    # 4. Test du formulaire
    print("\n4. Test FORM - Validation du formulaire")
    try:
        # Test avec des données valides
        form_data = {
            'matricule': 'TEST002',
            'firstname': 'Marie',
            'lastname': 'Martin',
            'date_naiss': '1985-03-20',
            'grade': 'Maître de Conférences',
            'gender': 'F',
            'lang': 'fr',
            'phone_number': '+237111222333',
            'email': 'marie.martin@ysem.edu'
        }
        
        form = EnseignantForm(data=form_data)
        if form.is_valid():
            enseignant2 = form.save()
            print(f"   ✓ Formulaire valide et enseignant créé: {enseignant2}")
        else:
            print(f"   ✗ Formulaire invalide: {form.errors}")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors du test du formulaire: {e}")
        return False
    
    # 5. Test DELETE (Suppression)
    print("\n5. Test DELETE - Suppression d'enseignants")
    try:
        # Supprimer les enseignants de test
        Lecturer.objects.filter(matricule__in=['TEST001', 'TEST002']).delete()
        
        # Vérifier la suppression
        count = Lecturer.objects.filter(matricule__in=['TEST001', 'TEST002']).count()
        if count == 0:
            print("   ✓ Enseignants de test supprimés avec succès")
        else:
            print(f"   ✗ {count} enseignant(s) de test encore présent(s)")
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
        # Créer un enseignant de test pour les URLs
        enseignant = Lecturer.objects.create(
            matricule='URL_TEST',
            firstname='Test',
            lastname='URL',
            date_naiss=date(1990, 1, 1),
            grade='Test',
            gender='M',
            lang='fr'
        )
        
        # Test des URLs
        urls_to_test = [
            ('teaching:enseignants', 'Liste des enseignants'),
            ('teaching:ajouter_enseignant', 'Ajouter enseignant'),
            ('teaching:detail_enseignant', 'Détail enseignant', {'matricule': 'URL_TEST'}),
            ('teaching:modifier_enseignant', 'Modifier enseignant', {'matricule': 'URL_TEST'}),
            ('teaching:supprimer_enseignant', 'Supprimer enseignant', {'matricule': 'URL_TEST'}),
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
        enseignant.delete()
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des URLs: {e}")

if __name__ == '__main__':
    print("Démarrage des tests CRUD pour les enseignants...\n")
    
    # Test des opérations CRUD
    success = test_crud_operations()
    
    # Test des URLs
    test_urls()
    
    if success:
        print("\n🎉 Implémentation CRUD des enseignants validée avec succès !")
    else:
        print("\n❌ Des erreurs ont été détectées dans l'implémentation CRUD.")
        sys.exit(1)
