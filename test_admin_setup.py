#!/usr/bin/env python
"""
Script de test pour l'administration Django YSEM
"""

import os
import sys
import django
from datetime import date, time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from django.contrib.auth import get_user_model
from planification.models import (
    Classroom, TimeSlot, CourseSession, Schedule, 
    LecturerAvailability, ScheduleSession
)
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear

User = get_user_model()

def create_superuser_if_needed():
    """Créer un superutilisateur si aucun n'existe"""
    print("🔐 Vérification des superutilisateurs...")
    
    if not User.objects.filter(is_superuser=True).exists():
        print("   Aucun superutilisateur trouvé. Création d'un compte admin...")
        
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@ysem.edu',
            password='admin123',
            firstname='Administrateur',
            lastname='YSEM',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Superutilisateur créé: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Mot de passe: admin123")
    else:
        admin_users = User.objects.filter(is_superuser=True)
        print(f"✅ {admin_users.count()} superutilisateur(s) trouvé(s):")
        for user in admin_users:
            print(f"   - {user.username} ({user.email})")

def check_admin_models():
    """Vérifier que tous les modèles sont enregistrés dans l'admin"""
    print("\n📋 Vérification des modèles dans l'administration...")
    
    from django.contrib import admin
    
    models_to_check = [
        ('Classroom', Classroom),
        ('TimeSlot', TimeSlot),
        ('CourseSession', CourseSession),
        ('Schedule', Schedule),
        ('LecturerAvailability', LecturerAvailability),
        ('ScheduleSession', ScheduleSession),
    ]
    
    for model_name, model_class in models_to_check:
        if model_class in admin.site._registry:
            admin_class = admin.site._registry[model_class]
            print(f"✅ {model_name}: Enregistré ({admin_class.__class__.__name__})")
        else:
            print(f"❌ {model_name}: Non enregistré")

def display_admin_statistics():
    """Afficher les statistiques des modèles pour l'admin"""
    print("\n📊 Statistiques des données pour l'administration:")
    
    stats = {
        'Salles de classe': Classroom.objects.count(),
        'Créneaux horaires': TimeSlot.objects.count(),
        'Séances de cours': CourseSession.objects.count(),
        'Emplois du temps': Schedule.objects.count(),
        'Disponibilités enseignants': LecturerAvailability.objects.count(),
        'Séances d\'emploi du temps': ScheduleSession.objects.count(),
    }
    
    for model_name, count in stats.items():
        print(f"   {model_name}: {count}")

def test_admin_features():
    """Tester les fonctionnalités spécifiques de l'admin"""
    print("\n🧪 Test des fonctionnalités d'administration...")
    
    # Test des méthodes personnalisées
    time_slot = TimeSlot.objects.first()
    if time_slot:
        print(f"✅ TimeSlot.duration_hours(): {time_slot.duration_hours()}h")
    
    schedule = Schedule.objects.first()
    if schedule:
        print(f"✅ Schedule.get_total_sessions(): {schedule.get_total_sessions()}")
    
    # Test des liens entre modèles
    if CourseSession.objects.exists():
        session = CourseSession.objects.first()
        print(f"✅ Relations CourseSession: {session.course} - {session.lecturer} - {session.classroom}")

def create_sample_data_for_admin():
    """Créer des données d'exemple pour tester l'admin"""
    print("\n🔧 Création de données d'exemple pour l'administration...")
    
    # Créer une année académique si elle n'existe pas
    academic_year, created = AcademicYear.objects.get_or_create(
        start_at=date(2024, 9, 1),
        end_at=date(2025, 6, 30),
        defaults={'is_active': True}
    )
    if created:
        print(f"✅ Année académique créée: {academic_year}")
    
    # Créer un niveau si il n'existe pas
    level, created = Level.objects.get_or_create(name="Test Admin")
    if created:
        print(f"✅ Niveau créé: {level}")
    
    # Créer une salle si elle n'existe pas
    classroom, created = Classroom.objects.get_or_create(
        code="ADMIN01",
        defaults={
            'name': "Salle Admin Test",
            'capacity': 30,
            'building': "Bâtiment Test",
            'floor': "1er étage",
            'is_active': True
        }
    )
    if created:
        print(f"✅ Salle créée: {classroom}")
    
    # Créer un créneau si il n'existe pas
    time_slot, created = TimeSlot.objects.get_or_create(
        name="Admin Test",
        day_of_week="monday",
        start_time=time(9, 0),
        end_time=time(11, 0),
        defaults={'is_active': True}
    )
    if created:
        print(f"✅ Créneau créé: {time_slot}")
    
    # Créer un emploi du temps si il n'existe pas
    schedule, created = Schedule.objects.get_or_create(
        name="Emploi du temps Admin Test",
        academic_year=academic_year,
        level=level,
        defaults={
            'start_date': date(2024, 9, 1),
            'end_date': date(2024, 12, 31),
            'duration_type': '3_months'
        }
    )
    if created:
        print(f"✅ Emploi du temps créé: {schedule}")

def display_admin_urls():
    """Afficher les URLs d'administration"""
    print("\n🌐 URLs d'administration disponibles:")
    print("   Administration principale: http://localhost:8000/admin/")
    print("   Salles de classe: http://localhost:8000/admin/planification/classroom/")
    print("   Créneaux horaires: http://localhost:8000/admin/planification/timeslot/")
    print("   Séances de cours: http://localhost:8000/admin/planification/coursesession/")
    print("   Emplois du temps: http://localhost:8000/admin/planification/schedule/")
    print("   Disponibilités: http://localhost:8000/admin/planification/lectureravailability/")
    print("   Séances d'emploi du temps: http://localhost:8000/admin/planification/schedulesession/")

def main():
    """Fonction principale"""
    print("🚀 Configuration et test de l'administration YSEM")
    print("=" * 60)
    
    try:
        # Créer un superutilisateur si nécessaire
        create_superuser_if_needed()
        
        # Vérifier les modèles enregistrés
        check_admin_models()
        
        # Afficher les statistiques
        display_admin_statistics()
        
        # Créer des données d'exemple
        create_sample_data_for_admin()
        
        # Tester les fonctionnalités
        test_admin_features()
        
        # Afficher les URLs
        display_admin_urls()
        
        print(f"\n✅ Configuration de l'administration terminée avec succès!")
        print(f"\n🔑 Informations de connexion:")
        print(f"   URL: http://localhost:8000/admin/")
        print(f"   Utilisateur: admin")
        print(f"   Mot de passe: admin123")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la configuration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
