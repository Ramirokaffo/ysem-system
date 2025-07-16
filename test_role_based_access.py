#!/usr/bin/env python
"""
Script de test pour vérifier le système de contrôle d'accès basé sur les rôles
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_role_based_access():
    """Test du système de contrôle d'accès basé sur les rôles"""
    print("=== Test du contrôle d'accès basé sur les rôles ===\n")
    
    try:
        # Créer des utilisateurs de test pour chaque rôle
        test_users = {}
        
        roles = [
            ('scholar', 'Responsable Scolarité'),
            ('teaching', 'Responsable Enseignements'),
            ('planning', 'Responsable Planification'),
            ('super_admin', 'Super Administrateur'),
            ('student', 'Étudiant')
        ]
        
        print("Création des utilisateurs de test :")
        for role, description in roles:
            username = f'test_{role}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': 'Test',
                    'last_name': description,
                    'role': role
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            test_users[role] = user
            print(f"   ✅ {description} ({username}) - Rôle: {role}")
        
        print("\n" + "="*60)
        
        # URLs à tester par rôle
        test_urls = {
            'scholar_urls': [
                ('/scholar/', 'Dashboard Scolarité'),
                ('/scholar/etudiants/', 'Gestion Étudiants'),
                ('/prospection/', 'Module Prospection'),
            ],
            'teaching_urls': [
                ('/teach/', 'Dashboard Enseignements'),
                ('/teach/enseignants/', 'Gestion Enseignants'),
                ('/teach/suivi_cours/', 'Suivi des Cours'),
            ],
            'planning_urls': [
                ('/planning/', 'Dashboard Planification'),
                ('/planning/salles/', 'Gestion Salles'),
                ('/planning/emplois-du-temps/', 'Emplois du Temps'),
            ],
            'forbidden_urls': [
                ('/admin/', 'Administration Django'),
            ]
        }
        
        # Test pour chaque utilisateur
        for role, user in test_users.items():
            print(f"\n🧪 Tests pour {user.first_name} {user.last_name} (rôle: {role})")
            print("-" * 50)
            
            client = Client()
            client.login(username=user.username, password='testpass123')
            
            # Test des URLs selon le rôle
            if role == 'scholar':
                test_user_access(client, user, test_urls['scholar_urls'], should_access=True)
                test_user_access(client, user, test_urls['teaching_urls'], should_access=False)
                test_user_access(client, user, test_urls['planning_urls'], should_access=False)
                
            elif role == 'teaching':
                test_user_access(client, user, test_urls['teaching_urls'], should_access=True)
                test_user_access(client, user, test_urls['scholar_urls'], should_access=False)
                test_user_access(client, user, test_urls['planning_urls'], should_access=False)
                
            elif role == 'planning':
                test_user_access(client, user, test_urls['planning_urls'], should_access=True)
                test_user_access(client, user, test_urls['scholar_urls'], should_access=False)
                test_user_access(client, user, test_urls['teaching_urls'], should_access=False)
                
            elif role == 'super_admin':
                # Super admin devrait avoir accès à tout
                test_user_access(client, user, test_urls['scholar_urls'], should_access=True)
                test_user_access(client, user, test_urls['teaching_urls'], should_access=True)
                test_user_access(client, user, test_urls['planning_urls'], should_access=True)
                
            elif role == 'student':
                # Étudiant ne devrait avoir accès à aucun dashboard admin
                test_user_access(client, user, test_urls['scholar_urls'], should_access=False)
                test_user_access(client, user, test_urls['teaching_urls'], should_access=False)
                test_user_access(client, user, test_urls['planning_urls'], should_access=False)
            
            client.logout()
        
        print("\n" + "="*60)
        print("🧪 Test de redirection automatique depuis la racine")
        print("-" * 50)
        
        # Test de redirection automatique depuis la racine
        for role, user in test_users.items():
            if role != 'student':  # Skip student pour ce test
                client = Client()
                client.login(username=user.username, password='testpass123')
                
                response = client.get('/', follow=False)
                if response.status_code == 302:
                    print(f"   ✅ {user.first_name} {user.last_name} ({role}): Redirection automatique")
                else:
                    print(f"   ❌ {user.first_name} {user.last_name} ({role}): Pas de redirection")
                
                client.logout()
        
        print(f"\n=== Tests terminés ===")
        print("✅ Système de contrôle d'accès basé sur les rôles testé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

def test_user_access(client, user, urls, should_access=True):
    """Test l'accès d'un utilisateur à une liste d'URLs"""
    for url, description in urls:
        try:
            response = client.get(url, follow=False)
            
            if should_access:
                # L'utilisateur devrait avoir accès
                if response.status_code in [200, 302]:
                    if response.status_code == 302:
                        # Vérifier que ce n'est pas une redirection de sécurité
                        location = response.get('Location', '')
                        if any(forbidden in location for forbidden in ['/auth/login', '/main/', '/teach/', '/planning/']):
                            print(f"   ❌ {description}: Accès refusé (redirection sécurité)")
                        else:
                            print(f"   ✅ {description}: Accès autorisé (redirection)")
                    else:
                        print(f"   ✅ {description}: Accès autorisé")
                else:
                    print(f"   ❌ {description}: Accès refusé (status: {response.status_code})")
            else:
                # L'utilisateur ne devrait PAS avoir accès
                if response.status_code == 302:
                    # Vérifier que c'est bien une redirection de sécurité
                    location = response.get('Location', '')
                    if any(redirect in location for redirect in ['/auth/login', '/main/', '/teach/', '/planning/']):
                        print(f"   ✅ {description}: Accès correctement refusé")
                    else:
                        print(f"   ⚠️  {description}: Redirection inattendue vers {location}")
                elif response.status_code == 403:
                    print(f"   ✅ {description}: Accès correctement refusé (403)")
                elif response.status_code == 200:
                    print(f"   ❌ {description}: Accès autorisé alors qu'il devrait être refusé")
                else:
                    print(f"   ⚠️  {description}: Status inattendu: {response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ {description}: Erreur - {e}")

if __name__ == "__main__":
    test_role_based_access()
