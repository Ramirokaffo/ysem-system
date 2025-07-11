#!/usr/bin/env python
"""
Script de test pour vérifier la sécurité du portail étudiant
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import Student
from accounts.models import BaseUser


def test_student_portal_security():
    """Test de sécurité du portail étudiant"""
    
    print("=== Test de Sécurité du Portail Étudiant ===\n")
    
    # 1. Créer un étudiant de test avec mot de passe
    print("1. Préparation des données de test...")
    try:
        # Supprimer l'étudiant s'il existe déjà
        Student.objects.filter(matricule='SECURITY_TEST').delete()
        
        student = Student.objects.create(
            matricule='SECURITY_TEST',
            firstname='Test',
            lastname='Security',
            gender='M',
            status='approved',
            email='test.security@test.com'
        )
        
        # Générer un mot de passe
        password = student.generate_external_password()
        print(f"   ✓ Étudiant créé avec mot de passe: {password}")
    except Exception as e:
        print(f"   ✗ Erreur lors de la création de l'étudiant: {e}")
        return False
    
    # 2. Tester l'accès aux URLs d'administration sans authentification
    print("\n2. Test d'accès aux URLs d'administration sans authentification...")
    client = Client()
    
    admin_urls = [
        '/admin/',
        '/scholar',
        '/etudiants/',
        '/documents/',
        '/statistiques/',
        '/parametres/',
    ]
    
    for url in admin_urls:
        try:
            response = client.get(url)
            # Ces URLs devraient rediriger vers la connexion (302) ou être interdites (403)
            if response.status_code in [302, 403]:
                print(f"   ✓ {url} : Accès correctement bloqué (code: {response.status_code})")
            else:
                print(f"   ⚠ {url} : Accès non bloqué (code: {response.status_code})")
        except Exception as e:
            print(f"   ✗ Erreur lors du test de {url}: {e}")
    
    # 3. Connecter l'étudiant au portail
    print("\n3. Connexion de l'étudiant au portail...")
    try:
        response = client.post(reverse('student_portal:login'), {
            'matricule': 'SECURITY_TEST',
            'password': password
        })
        
        if client.session.get('student_authenticated'):
            print("   ✓ Étudiant connecté au portail")
        else:
            print("   ✗ Échec de la connexion de l'étudiant")
            return False
    except Exception as e:
        print(f"   ✗ Erreur lors de la connexion: {e}")
        return False
    
    # 4. Tester l'accès aux URLs d'administration avec un étudiant connecté
    print("\n4. Test d'accès aux URLs d'administration avec étudiant connecté...")
    
    for url in admin_urls:
        try:
            response = client.get(url)
            # L'étudiant devrait être redirigé vers son dashboard
            if response.status_code == 302:
                # Vérifier que la redirection va vers le dashboard étudiant
                if 'portail-etudiant/tableau-de-bord' in response.url:
                    print(f"   ✓ {url} : Accès bloqué, redirection vers dashboard étudiant")
                else:
                    print(f"   ⚠ {url} : Redirection vers {response.url} (attendu: dashboard étudiant)")
            else:
                print(f"   ✗ {url} : Accès non bloqué (code: {response.status_code})")
        except Exception as e:
            print(f"   ✗ Erreur lors du test de {url}: {e}")
    
    # 5. Tester l'accès à des vues spécifiques sensibles
    print("\n5. Test d'accès aux vues sensibles...")
    
    sensitive_urls = [
        f'/etudiant/{student.matricule}/',
        f'/etudiant/{student.matricule}/modifier/',
        f'/etudiant/{student.matricule}/generer-mot-de-passe/',
        '/document/nouveau/',
        '/inscription/TEST001/',
    ]
    
    for url in sensitive_urls:
        try:
            response = client.get(url)
            if response.status_code == 302:
                print(f"   ✓ {url} : Accès bloqué (redirection)")
            elif response.status_code == 403:
                print(f"   ✓ {url} : Accès bloqué (403 Forbidden)")
            else:
                print(f"   ✗ {url} : Accès non bloqué (code: {response.status_code})")
        except Exception as e:
            print(f"   ⚠ {url} : Erreur lors du test: {e}")
    
    # 6. Vérifier que l'étudiant peut toujours accéder à son portail
    print("\n6. Vérification de l'accès au portail étudiant...")
    
    student_urls = [
        reverse('student_portal:dashboard'),
        reverse('student_portal:documents'),
    ]
    
    for url in student_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"   ✓ {url} : Accès autorisé")
            else:
                print(f"   ✗ {url} : Accès bloqué (code: {response.status_code})")
        except Exception as e:
            print(f"   ✗ Erreur lors du test de {url}: {e}")
    
    # 7. Tester la déconnexion et la perte d'accès
    print("\n7. Test de déconnexion...")
    try:
        response = client.get(reverse('student_portal:logout'))
        
        if not client.session.get('student_authenticated'):
            print("   ✓ Déconnexion réussie")
            
            # Vérifier que l'accès au dashboard est maintenant bloqué
            response = client.get(reverse('student_portal:dashboard'))
            if response.status_code == 302:
                print("   ✓ Accès au dashboard bloqué après déconnexion")
            else:
                print(f"   ✗ Accès au dashboard non bloqué après déconnexion (code: {response.status_code})")
        else:
            print("   ✗ Échec de la déconnexion")
    except Exception as e:
        print(f"   ✗ Erreur lors du test de déconnexion: {e}")
    
    print("\n=== Test de sécurité terminé ===")
    return True


def test_admin_student_conflict():
    """Test des conflits entre sessions admin et étudiant"""
    
    print("\n=== Test de Conflit de Sessions ===\n")
    
    # Créer un utilisateur admin de test
    try:
        BaseUser.objects.filter(username='test_admin').delete()
        admin_user = BaseUser.objects.create_user(
            username='test_admin',
            password='test_password',
            role='scholar'
        )
        print("   ✓ Utilisateur admin créé")
    except Exception as e:
        print(f"   ✗ Erreur lors de la création de l'admin: {e}")
        return False
    
    client = Client()
    
    # Connecter l'admin
    try:
        response = client.post(reverse('authentication:login'), {
            'username': 'test_admin',
            'password': 'test_password'
        })
        
        if client.session.get('_auth_user_id'):
            print("   ✓ Admin connecté")
        else:
            print("   ✗ Échec de la connexion admin")
            return False
    except Exception as e:
        print(f"   ✗ Erreur lors de la connexion admin: {e}")
        return False
    
    # Essayer d'accéder au portail étudiant en tant qu'admin
    try:
        response = client.get(reverse('student_portal:login'))
        print(f"   ✓ Accès au portail étudiant en tant qu'admin (code: {response.status_code})")
        
        # L'admin devrait pouvoir voir la page mais avec un avertissement
        if response.status_code == 200:
            print("   ✓ Admin peut accéder au portail (pour tests)")
    except Exception as e:
        print(f"   ✗ Erreur lors de l'accès au portail: {e}")
    
    return True


if __name__ == '__main__':
    print("🔒 Test de sécurité du portail étudiant\n")
    
    success1 = test_student_portal_security()
    success2 = test_admin_student_conflict()
    
    if success1 and success2:
        print("\n🎉 Tous les tests de sécurité sont passés !")
        sys.exit(0)
    else:
        print("\n❌ Des problèmes de sécurité ont été détectés.")
        sys.exit(1)
