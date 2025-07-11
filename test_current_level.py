#!/usr/bin/env python
"""
Script de test pour vérifier la fonctionnalité du niveau actuel
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import Student, StudentLevel
from academic.models import Level, AcademicYear

def test_current_level():
    print("=== Test du niveau actuel des étudiants ===")
    
    # Vérifier les données existantes
    students = Student.objects.all()
    levels = Level.objects.all()
    academic_years = AcademicYear.objects.all()
    
    print(f"Étudiants: {students.count()}")
    print(f"Niveaux: {levels.count()}")
    print(f"Années académiques: {academic_years.count()}")
    
    if students.exists() and levels.exists() and academic_years.exists():
        student = students.first()
        level = levels.first()
        academic_year = academic_years.first()
        
        print(f"\nTest avec l'étudiant: {student.matricule} - {student.firstname} {student.lastname}")
        
        # Créer un StudentLevel actif
        student_level, created = StudentLevel.objects.get_or_create(
            student=student,
            level=level,
            academic_year=academic_year,
            defaults={'is_active': True}
        )
        
        if created:
            print(f"✅ StudentLevel créé: {student_level}")
        else:
            print(f"✅ StudentLevel existant: {student_level}")
            student_level.is_active = True
            student_level.save()
        
        # Tester la propriété current_level
        current = student.current_level
        if current:
            print(f"✅ Niveau actuel trouvé: {current.level.name} ({current.academic_year.name})")
        else:
            print("❌ Aucun niveau actuel trouvé")
        
        # Tester le filtre dans la vue
        students_with_current_level = Student.objects.filter(
            student_levels__level_id=level.id,
            student_levels__is_active=True
        )
        
        print(f"✅ Étudiants avec le niveau {level.name} comme niveau actuel: {students_with_current_level.count()}")
        
        # Afficher tous les niveaux de l'étudiant
        all_levels = student.student_levels.all()
        print(f"\nTous les niveaux de l'étudiant {student.matricule}:")
        for sl in all_levels:
            status = "ACTUEL" if sl.is_active else "Historique"
            print(f"  - {sl.level.name} ({sl.academic_year.name}) [{status}]")
    
    else:
        print("❌ Données insuffisantes pour le test")

if __name__ == "__main__":
    test_current_level()
