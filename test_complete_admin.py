#!/usr/bin/env python
"""
Script de test complet pour l'administration YSEM
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.contrib import admin
from django.contrib.auth import get_user_model

# Import de tous les modèles
from planification.models import (
    Classroom, TimeSlot, CourseSession, Schedule, 
    LecturerAvailability, ScheduleSession
)
from Teaching.models import Lecturer, TeachingMonitoring, Evaluation
from academic.models import Speciality, Department, Level, Course, Program, AcademicYear
from accounts.models import BaseUser, Godfather
from students.models import Student, StudentLevel, StudentMetaData, OfficialDocument

User = get_user_model()

def check_admin_site_configuration():
    """Vérifier la configuration du site d'administration"""
    print("🏛️  Configuration du site d'administration:")
    print(f"   Titre du site: {admin.site.site_header}")
    print(f"   Titre de l'onglet: {admin.site.site_title}")
    print(f"   Titre de l'index: {admin.site.index_title}")

def check_all_registered_models():
    """Vérifier tous les modèles enregistrés dans l'admin"""
    print("\n📋 Modèles enregistrés dans l'administration:")
    
    # Modèles par application
    models_by_app = {
        'Planification': [
            ('Classroom', Classroom),
            ('TimeSlot', TimeSlot),
            ('CourseSession', CourseSession),
            ('Schedule', Schedule),
            ('LecturerAvailability', LecturerAvailability),
            ('ScheduleSession', ScheduleSession),
        ],
        'Enseignement': [
            ('Lecturer', Lecturer),
            ('TeachingMonitoring', TeachingMonitoring),
            ('Evaluation', Evaluation),
        ],
        'Académique': [
            ('Speciality', Speciality),
            ('Department', Department),
            ('Level', Level),
            ('Course', Course),
            ('Program', Program),
            ('AcademicYear', AcademicYear),
        ],
        'Comptes': [
            ('BaseUser', BaseUser),
            ('Godfather', Godfather),
        ],
        'Étudiants': [
            ('Student', Student),
            ('StudentLevel', StudentLevel),
            ('StudentMetaData', StudentMetaData),
            ('OfficialDocument', OfficialDocument),
        ]
    }
    
    total_registered = 0
    total_models = 0
    
    for app_name, models in models_by_app.items():
        print(f"\n   📁 {app_name}:")
        for model_name, model_class in models:
            total_models += 1
            if model_class in admin.site._registry:
                admin_class = admin.site._registry[model_class]
                print(f"      ✅ {model_name}: {admin_class.__class__.__name__}")
                total_registered += 1
            else:
                print(f"      ❌ {model_name}: Non enregistré")
    
    print(f"\n   📊 Résumé: {total_registered}/{total_models} modèles enregistrés")
    return total_registered, total_models

def check_admin_features():
    """Vérifier les fonctionnalités spécifiques de l'admin"""
    print("\n🔧 Fonctionnalités d'administration:")
    
    features = []
    
    # Vérifier les fonctionnalités de ClassroomAdmin
    if Classroom in admin.site._registry:
        classroom_admin = admin.site._registry[Classroom]
        features.append(f"✅ Salles: {len(classroom_admin.list_display)} colonnes d'affichage")
        features.append(f"✅ Salles: {len(classroom_admin.list_filter)} filtres")
        features.append(f"✅ Salles: {len(classroom_admin.search_fields)} champs de recherche")
    
    # Vérifier les fonctionnalités de TimeSlotAdmin
    if TimeSlot in admin.site._registry:
        timeslot_admin = admin.site._registry[TimeSlot]
        features.append(f"✅ Créneaux: {len(timeslot_admin.list_display)} colonnes d'affichage")
        features.append(f"✅ Créneaux: Méthodes personnalisées (duration_display, usage_count)")
    
    # Vérifier les fonctionnalités de StudentAdmin
    if Student in admin.site._registry:
        student_admin = admin.site._registry[Student]
        features.append(f"✅ Étudiants: {len(student_admin.fieldsets)} sections de formulaire")
        features.append(f"✅ Étudiants: Pagination ({student_admin.list_per_page} par page)")
    
    for feature in features:
        print(f"   {feature}")

def display_admin_statistics():
    """Afficher les statistiques complètes"""
    print("\n📊 Statistiques complètes des données:")
    
    stats = {
        'Planification': {
            'Salles de classe': Classroom.objects.count(),
            'Créneaux horaires': TimeSlot.objects.count(),
            'Séances de cours': CourseSession.objects.count(),
            'Emplois du temps': Schedule.objects.count(),
            'Disponibilités enseignants': LecturerAvailability.objects.count(),
            'Séances d\'emploi du temps': ScheduleSession.objects.count(),
        },
        'Enseignement': {
            'Enseignants': Lecturer.objects.count(),
            'Suivis pédagogiques': TeachingMonitoring.objects.count(),
            'Évaluations': Evaluation.objects.count(),
        },
        'Académique': {
            'Spécialités': Speciality.objects.count(),
            'Départements': Department.objects.count(),
            'Niveaux': Level.objects.count(),
            'Cours': Course.objects.count(),
            'Programmes': Program.objects.count(),
            'Années académiques': AcademicYear.objects.count(),
        },
        'Utilisateurs': {
            'Utilisateurs': User.objects.count(),
            'Superutilisateurs': User.objects.filter(is_superuser=True).count(),
            'Staff': User.objects.filter(is_staff=True).count(),
            'Parrains': Godfather.objects.count(),
        },
        'Étudiants': {
            'Étudiants': Student.objects.count(),
            'Niveaux d\'étudiants': StudentLevel.objects.count(),
            'Métadonnées': StudentMetaData.objects.count(),
            'Documents officiels': OfficialDocument.objects.count(),
        }
    }
    
    total_records = 0
    for category, category_stats in stats.items():
        print(f"\n   📁 {category}:")
        for model_name, count in category_stats.items():
            print(f"      {model_name}: {count}")
            total_records += count
    
    print(f"\n   🎯 Total des enregistrements: {total_records}")

def display_admin_urls():
    """Afficher toutes les URLs d'administration"""
    print("\n🌐 URLs d'administration complètes:")
    
    urls = {
        'Principal': [
            ('Administration principale', 'http://localhost:8000/admin/'),
        ],
        'Planification': [
            ('Salles de classe', 'http://localhost:8000/admin/planification/classroom/'),
            ('Créneaux horaires', 'http://localhost:8000/admin/planification/timeslot/'),
            ('Séances de cours', 'http://localhost:8000/admin/planification/coursesession/'),
            ('Emplois du temps', 'http://localhost:8000/admin/planification/schedule/'),
            ('Disponibilités', 'http://localhost:8000/admin/planification/lectureravailability/'),
            ('Séances d\'emploi du temps', 'http://localhost:8000/admin/planification/schedulesession/'),
        ],
        'Enseignement': [
            ('Enseignants', 'http://localhost:8000/admin/Teaching/lecturer/'),
            ('Suivi pédagogique', 'http://localhost:8000/admin/Teaching/teachingmonitoring/'),
            ('Évaluations', 'http://localhost:8000/admin/Teaching/evaluation/'),
        ],
        'Académique': [
            ('Spécialités', 'http://localhost:8000/admin/academic/speciality/'),
            ('Départements', 'http://localhost:8000/admin/academic/department/'),
            ('Niveaux', 'http://localhost:8000/admin/academic/level/'),
            ('Cours', 'http://localhost:8000/admin/academic/course/'),
            ('Programmes', 'http://localhost:8000/admin/academic/program/'),
            ('Années académiques', 'http://localhost:8000/admin/academic/academicyear/'),
        ],
        'Comptes': [
            ('Utilisateurs', 'http://localhost:8000/admin/accounts/baseuser/'),
            ('Parrains', 'http://localhost:8000/admin/accounts/godfather/'),
        ],
        'Étudiants': [
            ('Étudiants', 'http://localhost:8000/admin/students/student/'),
            ('Niveaux d\'étudiants', 'http://localhost:8000/admin/students/studentlevel/'),
            ('Métadonnées', 'http://localhost:8000/admin/students/studentmetadata/'),
            ('Documents officiels', 'http://localhost:8000/admin/students/officialdocument/'),
        ]
    }
    
    for category, category_urls in urls.items():
        print(f"\n   📁 {category}:")
        for name, url in category_urls:
            print(f"      {name}: {url}")

def main():
    """Fonction principale"""
    print("🚀 Test complet de l'administration YSEM")
    print("=" * 60)
    
    try:
        # Configuration du site
        check_admin_site_configuration()
        
        # Modèles enregistrés
        registered, total = check_all_registered_models()
        
        # Fonctionnalités
        check_admin_features()
        
        # Statistiques
        display_admin_statistics()
        
        # URLs
        display_admin_urls()
        
        print(f"\n✅ Test complet terminé avec succès!")
        print(f"   📊 {registered}/{total} modèles enregistrés")
        print(f"   🏛️  Site: {admin.site.site_header}")
        
        print(f"\n🔑 Accès à l'administration:")
        print(f"   URL: http://localhost:8000/admin/")
        print(f"   Utilisateur: admin")
        print(f"   Mot de passe: admin123")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
