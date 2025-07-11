#!/usr/bin/env python
"""
Script de test pour la fonctionnalité du portail étudiant
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import Student, StudentLevel, OfficialDocument
from academic.models import AcademicYear, Level
from accounts.models import BaseUser


def test_student_portal():
    """Test complet du portail étudiant"""
    
    print("=== Test du Portail Étudiant ===\n")
    
    # 1. Créer un étudiant de test
    print("1. Création d'un étudiant de test...")
    try:
        # Supprimer l'étudiant s'il existe déjà
        Student.objects.filter(matricule='TEST001').delete()
        
        student = Student.objects.create(
            matricule='TEST001',
            firstname='Jean',
            lastname='Dupont',
            gender='M',
            status='approved',
            email='jean.dupont@test.com'
        )
        print(f"   ✓ Étudiant créé: {student}")
    except Exception as e:
        print(f"   ✗ Erreur lors de la création de l'étudiant: {e}")
        return False
    
    # 2. Tester la génération de mot de passe
    print("\n2. Test de génération de mot de passe...")
    try:
        # Vérifier qu'il n'y a pas de mot de passe initialement
        assert not student.has_external_password(), "L'étudiant ne devrait pas avoir de mot de passe initialement"
        
        # Générer un mot de passe
        password = student.generate_external_password()
        print(f"   ✓ Mot de passe généré: {password}")
        
        # Vérifier que le mot de passe est configuré
        assert student.has_external_password(), "L'étudiant devrait maintenant avoir un mot de passe"
        assert student.external_password_created_at is not None, "La date de création devrait être définie"
        
        # Tester la vérification du mot de passe
        assert student.check_external_password(password), "Le mot de passe devrait être valide"
        assert not student.check_external_password('mauvais_mot_de_passe'), "Un mauvais mot de passe ne devrait pas être valide"
        
        print("   ✓ Vérification du mot de passe réussie")
    except Exception as e:
        print(f"   ✗ Erreur lors du test de mot de passe: {e}")
        return False
    
    # 3. Créer des données de test (niveau et documents)
    print("\n3. Création de données de test...")
    try:
        # Créer une année académique
        academic_year, created = AcademicYear.objects.get_or_create(
            name='2024-2025',
            defaults={
                'start_at': date(2024, 9, 1),
                'end_at': date(2025, 8, 31),
                'is_active': True
            }
        )
        
        # Créer un niveau
        level, created = Level.objects.get_or_create(
            name='Licence 1'
        )
        
        # Créer un StudentLevel
        student_level, created = StudentLevel.objects.get_or_create(
            student=student,
            level=level,
            academic_year=academic_year,
            defaults={'is_active': True}
        )
        
        # Créer quelques documents officiels
        documents_data = [
            {'type': 'student_card', 'status': 'available'},
            {'type': 'transcript', 'status': 'withdrawn'},
            {'type': 'certificate', 'status': 'available'},
        ]
        
        for doc_data in documents_data:
            OfficialDocument.objects.get_or_create(
                student_level=student_level,
                type=doc_data['type'],
                defaults={'status': doc_data['status']}
            )
        
        print(f"   ✓ Données créées: {academic_year}, {level}, {len(documents_data)} documents")
    except Exception as e:
        print(f"   ✗ Erreur lors de la création des données: {e}")
        return False
    
    # 4. Tester l'authentification
    print("\n4. Test de l'authentification...")
    try:
        client = Client()
        
        # Test de la page de connexion
        response = client.get(reverse('student_portal:login'))
        assert response.status_code == 200, f"La page de connexion devrait être accessible (code: {response.status_code})"
        print("   ✓ Page de connexion accessible")
        
        # Test de connexion avec de mauvaises informations
        response = client.post(reverse('student_portal:login'), {
            'matricule': 'TEST001',
            'password': 'mauvais_mot_de_passe'
        })
        assert response.status_code == 200, "Devrait rester sur la page de connexion"
        assert not client.session.get('student_authenticated'), "Ne devrait pas être authentifié"
        print("   ✓ Rejet des mauvaises informations")
        
        # Test de connexion avec les bonnes informations
        response = client.post(reverse('student_portal:login'), {
            'matricule': 'TEST001',
            'password': password
        })
        assert response.status_code == 302, "Devrait rediriger après connexion réussie"
        assert client.session.get('student_authenticated'), "Devrait être authentifié"
        assert client.session.get('student_matricule') == 'TEST001', "Le matricule devrait être en session"
        print("   ✓ Connexion réussie")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test d'authentification: {e}")
        return False
    
    # 5. Tester l'accès au dashboard
    print("\n5. Test du dashboard...")
    try:
        response = client.get(reverse('student_portal:dashboard'))
        assert response.status_code == 200, f"Le dashboard devrait être accessible (code: {response.status_code})"
        assert 'Jean Dupont' in response.content.decode(), "Le nom de l'étudiant devrait apparaître"
        print("   ✓ Dashboard accessible")
    except Exception as e:
        print(f"   ✗ Erreur lors du test du dashboard: {e}")
        return False
    
    # 6. Tester l'accès aux documents
    print("\n6. Test de la consultation des documents...")
    try:
        response = client.get(reverse('student_portal:documents'))
        assert response.status_code == 200, f"La page des documents devrait être accessible (code: {response.status_code})"
        content = response.content.decode()
        assert 'Carte d\'étudiant' in content or 'student_card' in content, "Les documents devraient être listés"
        print("   ✓ Page des documents accessible")
    except Exception as e:
        print(f"   ✗ Erreur lors du test des documents: {e}")
        return False
    
    # 7. Tester la déconnexion
    print("\n7. Test de la déconnexion...")
    try:
        response = client.get(reverse('student_portal:logout'))
        assert response.status_code == 302, "Devrait rediriger après déconnexion"
        assert not client.session.get('student_authenticated'), "Ne devrait plus être authentifié"
        print("   ✓ Déconnexion réussie")
    except Exception as e:
        print(f"   ✗ Erreur lors du test de déconnexion: {e}")
        return False
    
    # 8. Tester l'accès protégé après déconnexion
    print("\n8. Test de protection après déconnexion...")
    try:
        response = client.get(reverse('student_portal:dashboard'))
        assert response.status_code == 302, "Devrait rediriger vers la connexion"
        print("   ✓ Accès protégé après déconnexion")
    except Exception as e:
        print(f"   ✗ Erreur lors du test de protection: {e}")
        return False
    
    print("\n=== Tous les tests sont passés avec succès ! ===")
    return True


if __name__ == '__main__':
    success = test_student_portal()
    if success:
        print("\n🎉 Le portail étudiant fonctionne correctement !")
        sys.exit(0)
    else:
        print("\n❌ Des erreurs ont été détectées.")
        sys.exit(1)
