#!/usr/bin/env python
"""
Script de test pour les fonctionnalités d'emploi du temps
"""

import os
import sys
import django
from datetime import date, time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from planification.models import Schedule, LecturerAvailability, TimeSlot, Classroom
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear

def create_test_data():
    """Créer des données de test"""
    print("🔧 Création des données de test...")
    
    # Créer une année académique
    academic_year, created = AcademicYear.objects.get_or_create(
        start_at=date(2024, 9, 1),
        end_at=date(2025, 6, 30),
        defaults={'is_active': True}
    )
    if created:
        print(f"✅ Année académique créée: {academic_year}")
    
    # Créer un niveau
    level, created = Level.objects.get_or_create(name="Licence 1")
    if created:
        print(f"✅ Niveau créé: {level}")
    
    # Créer des cours
    course1, created = Course.objects.get_or_create(
        course_code="INF101",
        defaults={
            'label': "Introduction à l'informatique",
            'credit_count': 3,
            'level': level
        }
    )
    if created:
        print(f"✅ Cours créé: {course1}")
    
    course2, created = Course.objects.get_or_create(
        course_code="MAT101",
        defaults={
            'label': "Mathématiques générales",
            'credit_count': 4,
            'level': level
        }
    )
    if created:
        print(f"✅ Cours créé: {course2}")
    
    # Créer des enseignants
    lecturer1, created = Lecturer.objects.get_or_create(
        matricule="ENS001",
        defaults={
            'firstname': "Jean",
            'lastname': "Dupont",
            'date_naiss': date(1980, 1, 1),
            'grade': "Professeur",
            'gender': "M"
        }
    )
    if created:
        print(f"✅ Enseignant créé: {lecturer1}")
    
    lecturer2, created = Lecturer.objects.get_or_create(
        matricule="ENS002",
        defaults={
            'firstname': "Marie",
            'lastname': "Martin",
            'date_naiss': date(1985, 5, 15),
            'grade': "Maître de conférences",
            'gender': "F"
        }
    )
    if created:
        print(f"✅ Enseignant créé: {lecturer2}")
    
    # Créer des créneaux horaires
    time_slot1, created = TimeSlot.objects.get_or_create(
        name="Matin 1",
        day_of_week="monday",
        start_time=time(8, 0),
        end_time=time(10, 0),
        defaults={'is_active': True}
    )
    if created:
        print(f"✅ Créneau créé: {time_slot1}")
    
    time_slot2, created = TimeSlot.objects.get_or_create(
        name="Matin 2",
        day_of_week="tuesday",
        start_time=time(8, 0),
        end_time=time(10, 0),
        defaults={'is_active': True}
    )
    if created:
        print(f"✅ Créneau créé: {time_slot2}")
    
    # Créer des salles
    classroom1, created = Classroom.objects.get_or_create(
        code="A101",
        defaults={
            'name': "Salle A101",
            'capacity': 50,
            'building': "Bâtiment A",
            'floor': "1er étage",
            'is_active': True
        }
    )
    if created:
        print(f"✅ Salle créée: {classroom1}")
    
    classroom2, created = Classroom.objects.get_or_create(
        code="A102",
        defaults={
            'name': "Salle A102",
            'capacity': 40,
            'building': "Bâtiment A",
            'floor': "1er étage",
            'is_active': True
        }
    )
    if created:
        print(f"✅ Salle créée: {classroom2}")
    
    return {
        'academic_year': academic_year,
        'level': level,
        'courses': [course1, course2],
        'lecturers': [lecturer1, lecturer2],
        'time_slots': [time_slot1, time_slot2],
        'classrooms': [classroom1, classroom2]
    }

def test_schedule_creation(data):
    """Tester la création d'emploi du temps"""
    print("\n📅 Test de création d'emploi du temps...")
    
    schedule, created = Schedule.objects.get_or_create(
        name="Emploi du temps L1 - Test",
        academic_year=data['academic_year'],
        level=data['level'],
        defaults={
            'description': "Emploi du temps de test",
            'start_date': date(2024, 9, 1),
            'end_date': date(2024, 12, 31),
            'duration_type': '3_months'
        }
    )
    
    if created:
        print(f"✅ Emploi du temps créé: {schedule}")
    else:
        print(f"ℹ️  Emploi du temps existant: {schedule}")
    
    print(f"   - Durée: {schedule.get_duration_days()} jours")
    print(f"   - Statut: {schedule.get_status_display()}")
    
    return schedule

def test_lecturer_availability(data):
    """Tester la création de disponibilités"""
    print("\n👨‍🏫 Test de création de disponibilités...")
    
    for lecturer in data['lecturers']:
        for time_slot in data['time_slots']:
            availability, created = LecturerAvailability.objects.get_or_create(
                lecturer=lecturer,
                time_slot=time_slot,
                academic_year=data['academic_year'],
                defaults={
                    'status': 'available',
                    'notes': f"Disponibilité test pour {lecturer.firstname}"
                }
            )
            
            if created:
                print(f"✅ Disponibilité créée: {availability}")
            else:
                print(f"ℹ️  Disponibilité existante: {availability}")

def test_schedule_generation(schedule, data):
    """Tester la génération d'emploi du temps"""
    print("\n🎯 Test de génération d'emploi du temps...")
    
    try:
        from planification.services import ScheduleGenerationService
        
        service = ScheduleGenerationService(
            schedule=schedule,
            courses=data['courses'],
            sessions_per_week=1,  # Réduire pour éviter les conflits
            max_daily_sessions=2
        )
        
        result = service.generate_schedule()
        
        if result['success']:
            print(f"✅ Génération réussie: {result['message']}")
            print(f"   - Séances créées: {result['sessions_count']}")
        else:
            print(f"❌ Échec de génération: {result['message']}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {str(e)}")

def display_statistics():
    """Afficher les statistiques"""
    print("\n📊 Statistiques du système:")
    print(f"   - Emplois du temps: {Schedule.objects.count()}")
    print(f"   - Disponibilités: {LecturerAvailability.objects.count()}")
    print(f"   - Enseignants: {Lecturer.objects.count()}")
    print(f"   - Créneaux horaires: {TimeSlot.objects.count()}")
    print(f"   - Salles: {Classroom.objects.count()}")

def main():
    """Fonction principale"""
    print("🚀 Test des fonctionnalités d'emploi du temps YSEM")
    print("=" * 50)
    
    try:
        # Créer les données de test
        data = create_test_data()
        
        # Tester la création d'emploi du temps
        schedule = test_schedule_creation(data)
        
        # Tester les disponibilités
        test_lecturer_availability(data)
        
        # Tester la génération (optionnel)
        if schedule.status == 'draft':
            test_schedule_generation(schedule, data)
        
        # Afficher les statistiques
        display_statistics()
        
        print("\n✅ Tests terminés avec succès!")
        print("\n🌐 Vous pouvez maintenant accéder au dashboard de planification:")
        print("   http://localhost:8000/planning/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
