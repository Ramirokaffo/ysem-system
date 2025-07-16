#!/usr/bin/env python
"""
Script de test pour vérifier toutes les URLs du système CRUD suivi des cours
"""
import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Teaching.models import TeachingMonitoring, Lecturer
from academic.models import AcademicYear, Course, Level

def test_suivi_urls():
    """Test de toutes les URLs du système CRUD"""
    print("=== Test des URLs - Système CRUD Suivi des cours ===\n")
    
    try:
        # Créer un client de test
        client = Client()
        
        # Créer un utilisateur de test pour l'authentification
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'academic_admin'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Se connecter
        client.login(username='test_user', password='testpass123')
        print("✅ Utilisateur de test connecté\n")
        
        # Vérifier qu'il y a au moins un suivi en base
        suivi = TeachingMonitoring.objects.first()
        if not suivi:
            # Créer un suivi de test
            lecturer = Lecturer.objects.first()
            course = Course.objects.first()
            level = Level.objects.first()
            academic_year = AcademicYear.objects.filter(is_active=True).first()
            
            if all([lecturer, course, level, academic_year]):
                suivi = TeachingMonitoring.objects.create(
                    date=date.today(),
                    lecturer=lecturer,
                    course=course,
                    level=level,
                    academic_year=academic_year,
                    totalChapterCount=10,
                    chapitre_fait=6,
                    contenu_seance_prevu=20,
                    contenu_effectif_seance=15,
                    travaux_preparatoires=True,
                    groupWork=True,
                    classWork=True,
                    homeWork=False,
                    pedagogicActivities=True,
                    TDandTP=True,
                    projet_fin_cours="Test projet",
                    association_pratique_aux_enseigements="Test association",
                    observation="Test observation",
                    solution="Test solution",
                    generalObservation="Test observation générale"
                )
                print(f"✅ Suivi de test créé avec l'ID: {suivi.id}\n")
        
        # Test des URLs
        urls_to_test = [
            ('/teaching/suivi_cours/', 'Liste des suivis'),
            ('/teaching/suivi_cours/ajouter/', 'Ajouter un suivi'),
            (f'/teaching/suivi_cours/{suivi.id}/', 'Détails du suivi'),
            (f'/teaching/suivi_cours/{suivi.id}/modifier/', 'Modifier le suivi'),
            (f'/teaching/suivi_cours/{suivi.id}/supprimer/', 'Supprimer le suivi'),
        ]
        
        print("Test des URLs :")
        for url, description in urls_to_test:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    print(f"✅ {description}: {url} - Status: {response.status_code}")
                elif response.status_code == 302:
                    print(f"🔄 {description}: {url} - Redirection: {response.status_code}")
                else:
                    print(f"❌ {description}: {url} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {description}: {url} - Erreur: {e}")
        
        print("\nTest des filtres sur la liste :")
        # Test avec filtres
        filter_urls = [
            ('/teaching/suivi_cours/?lecturer=ENS001', 'Filtre par enseignant'),
            ('/teaching/suivi_cours/?course=CSI001', 'Filtre par cours'),
            ('/teaching/suivi_cours/?level=1', 'Filtre par niveau'),
            ('/teaching/suivi_cours/?academic_year=1', 'Filtre par année académique'),
        ]
        
        for url, description in filter_urls:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    print(f"✅ {description}: Status: {response.status_code}")
                else:
                    print(f"❌ {description}: Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {description}: Erreur: {e}")
        
        print("\nTest des actions POST :")
        
        # Test de création (POST)
        lecturer = Lecturer.objects.first()
        course = Course.objects.first()
        level = Level.objects.first()
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        
        if all([lecturer, course, level, academic_year]):
            post_data = {
                'date': date.today(),
                'lecturer': lecturer.matricule,
                'course': course.course_code,
                'level': level.id,
                'academic_year': academic_year.id,
                'totalChapterCount': 8,
                'chapitre_fait': 4,
                'contenu_seance_prevu': 16,
                'contenu_effectif_seance': 12,
                'travaux_preparatoires': True,
                'groupWork': False,
                'classWork': True,
                'homeWork': True,
                'pedagogicActivities': True,
                'TDandTP': False,
                'projet_fin_cours': 'Projet test POST',
                'association_pratique_aux_enseigements': 'Association test',
                'observation': 'Observation test',
                'solution': 'Solution test',
                'generalObservation': 'Observation générale test'
            }
            
            response = client.post('/teaching/suivi_cours/ajouter/', post_data)
            if response.status_code in [200, 302]:
                print(f"✅ Création via POST: Status: {response.status_code}")
            else:
                print(f"❌ Création via POST: Status: {response.status_code}")
        
        # Test de modification (POST)
        if suivi:
            post_data = {
                'date': suivi.date,
                'lecturer': suivi.lecturer.matricule,
                'course': suivi.course.course_code,
                'level': suivi.level.id,
                'academic_year': suivi.academic_year.id,
                'totalChapterCount': suivi.totalChapterCount,
                'chapitre_fait': suivi.chapitre_fait + 1,  # Modification
                'contenu_seance_prevu': suivi.contenu_seance_prevu,
                'contenu_effectif_seance': suivi.contenu_effectif_seance + 2,  # Modification
                'travaux_preparatoires': suivi.travaux_preparatoires,
                'groupWork': suivi.groupWork,
                'classWork': suivi.classWork,
                'homeWork': suivi.homeWork,
                'pedagogicActivities': suivi.pedagogicActivities,
                'TDandTP': suivi.TDandTP,
                'projet_fin_cours': suivi.projet_fin_cours,
                'association_pratique_aux_enseigements': suivi.association_pratique_aux_enseigements,
                'observation': 'Observation modifiée via test',
                'solution': suivi.solution,
                'generalObservation': suivi.generalObservation
            }
            
            response = client.post(f'/teaching/suivi_cours/{suivi.id}/modifier/', post_data)
            if response.status_code in [200, 302]:
                print(f"✅ Modification via POST: Status: {response.status_code}")
            else:
                print(f"❌ Modification via POST: Status: {response.status_code}")
        
        print(f"\n=== Tests terminés avec succès ! ===")
        print(f"Total des suivis en base: {TeachingMonitoring.objects.count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_suivi_urls()
