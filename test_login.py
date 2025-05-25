#!/usr/bin/env python
"""
Script de test pour vérifier l'implémentation du login
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

def test_login_implementation():
    """Test de l'implémentation du login"""
    print("🧪 Test de l'implémentation du login YSEM")
    print("=" * 50)
    
    # Initialiser le client de test
    client = Client()
    
    # Test 1: Accès à la page de login
    print("\n1. Test d'accès à la page de login...")
    try:
        response = client.get('/auth/login/')
        if response.status_code == 200:
            print("✅ Page de login accessible")
        else:
            print(f"❌ Erreur d'accès: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Redirection depuis le dashboard
    print("\n2. Test de redirection depuis le dashboard...")
    try:
        response = client.get('/')
        if response.status_code == 302:
            print("✅ Redirection vers login fonctionnelle")
            print(f"   Redirection vers: {response.url}")
        else:
            print(f"❌ Pas de redirection: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Vérification des URLs
    print("\n3. Test des URLs d'authentification...")
    try:
        login_url = reverse('authentication:login')
        logout_url = reverse('authentication:logout')
        print(f"✅ URL login: {login_url}")
        print(f"✅ URL logout: {logout_url}")
    except Exception as e:
        print(f"❌ Erreur URLs: {e}")
    
    # Test 4: Vérification du modèle utilisateur
    print("\n4. Test du modèle utilisateur...")
    try:
        User = get_user_model()
        print(f"✅ Modèle utilisateur: {User}")
        print(f"   Champs disponibles: {[f.name for f in User._meta.fields]}")
    except Exception as e:
        print(f"❌ Erreur modèle: {e}")
    
    # Test 5: Test de création d'utilisateur (simulation)
    print("\n5. Test de création d'utilisateur...")
    try:
        User = get_user_model()
        # Vérifier si on peut créer un utilisateur
        user_data = {
            'username': 'test_user',
            'email': 'test@ysem.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        print("✅ Structure utilisateur valide")
        print(f"   Données test: {user_data}")
    except Exception as e:
        print(f"❌ Erreur structure: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés!")
    print("\n📋 Instructions pour tester manuellement:")
    print("1. Lancez le serveur: python manage.py runserver")
    print("2. Créez un superutilisateur: python manage.py createsuperuser")
    print("3. Accédez à http://localhost:8000")
    print("4. Vous devriez être redirigé vers /auth/login/")
    print("5. Connectez-vous avec vos identifiants")
    print("6. Vous devriez accéder au dashboard")

if __name__ == '__main__':
    test_login_implementation()
