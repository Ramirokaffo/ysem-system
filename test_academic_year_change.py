#!/usr/bin/env python3
"""
Test script pour vérifier la fonctionnalité de changement d'année académique
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from academic.models import AcademicYear
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from main.views import ParametresView

def test_academic_year_change():
    """Test du changement d'année académique"""
    print("=== Test du changement d'année académique ===")
    
    # Afficher les années académiques disponibles
    years = AcademicYear.objects.all().order_by('-start_at')
    print(f"\nAnnées académiques disponibles ({years.count()}):")
    for year in years:
        status = "ACTIVE" if year.is_active else "inactive"
        print(f"  - {year.name} (ID: {year.id}) [{status}]")
    
    # Créer une requête factice
    factory = RequestFactory()
    request = factory.post('/parametres/', {
        'form_type': 'academic_year',
        'academic_year_id': '4'  # Changer vers 2023/2024
    })
    
    # Ajouter la session à la requête
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Ajouter les messages à la requête
    msg_middleware = MessageMiddleware(lambda req: None)
    msg_middleware.process_request(request)
    
    # Simuler un utilisateur connecté
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.first()
        request.user = user
    except:
        print("Aucun utilisateur trouvé dans la base de données")
        return
    
    print(f"\nAnnée académique active avant changement:")
    current_year_id = request.session.get('active_academic_year_id')
    if current_year_id:
        try:
            current_year = AcademicYear.objects.get(id=current_year_id)
            print(f"  - {current_year.name} (ID: {current_year.id})")
        except AcademicYear.DoesNotExist:
            print("  - Aucune année définie dans la session")
    else:
        print("  - Aucune année définie dans la session")
    
    # Tester la vue
    view = ParametresView()
    view.setup(request)
    
    try:
        response = view.post(request)
        print(f"\nRéponse de la vue: {response.status_code}")
        
        # Vérifier la session après le changement
        new_year_id = request.session.get('active_academic_year_id')
        if new_year_id:
            try:
                new_year = AcademicYear.objects.get(id=new_year_id)
                print(f"Nouvelle année académique active: {new_year.name} (ID: {new_year.id})")
                print("✅ Changement d'année académique réussi!")
            except AcademicYear.DoesNotExist:
                print("❌ Erreur: Année académique introuvable")
        else:
            print("❌ Erreur: Aucune année académique définie après le changement")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

def test_context_processor():
    """Test du context processor"""
    print("\n=== Test du context processor ===")
    
    factory = RequestFactory()
    request = factory.get('/')
    
    # Ajouter la session
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Tester sans année dans la session
    from academic.context_processors import active_academic_year
    context = active_academic_year(request)
    
    print(f"Context processor sans année en session:")
    if context['active_academic_year']:
        year = context['active_academic_year']
        print(f"  - Année retournée: {year.name} (ID: {year.id})")
        print(f"  - Année mise en session: {request.session.get('active_academic_year_id')}")
    else:
        print("  - Aucune année retournée")
    
    # Tester avec une année spécifique en session
    request.session['active_academic_year_id'] = 2  # 2022/2023
    context = active_academic_year(request)
    
    print(f"\nContext processor avec année ID=2 en session:")
    if context['active_academic_year']:
        year = context['active_academic_year']
        print(f"  - Année retournée: {year.name} (ID: {year.id})")
    else:
        print("  - Aucune année retournée")

if __name__ == '__main__':
    test_academic_year_change()
    test_context_processor()
    print("\n=== Tests terminés ===")
