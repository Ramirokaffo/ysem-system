#!/usr/bin/env python
"""
Script de test pour vérifier la fonctionnalité de création en masse de documents
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import Student, StudentLevel, OfficialDocument
from academic.models import Level, AcademicYear, Program
from main.forms import BulkDocumentCreationForm

def test_bulk_creation():
    print("=== Test de la création en masse de documents ===")
    
    # Vérifier les données existantes
    students = Student.objects.filter(status='approved')
    levels = Level.objects.all()
    academic_years = AcademicYear.objects.all()
    programs = Program.objects.all()
    
    print(f"Étudiants approuvés: {students.count()}")
    print(f"Niveaux: {levels.count()}")
    print(f"Années académiques: {academic_years.count()}")
    print(f"Programmes: {programs.count()}")
    
    if students.exists() and levels.exists() and academic_years.exists():
        level = levels.first()
        academic_year = academic_years.first()
        program = programs.first() if programs.exists() else None
        
        print(f"\nTest avec:")
        print(f"- Niveau: {level.name}")
        print(f"- Année académique: {academic_year.name}")
        print(f"- Programme: {program.name if program else 'Tous'}")
        
        # Créer quelques StudentLevel pour le test
        test_students = students[:3]  # Prendre les 3 premiers étudiants
        for student in test_students:
            student_level, created = StudentLevel.objects.get_or_create(
                student=student,
                level=level,
                academic_year=academic_year
            )
            if created:
                print(f"✅ StudentLevel créé pour {student.matricule}")
        
        # Tester le formulaire
        form_data = {
            'document_type': 'student_card',
            'academic_year': academic_year.pk,
            'level': level.pk,
            'status': 'available'
        }
        
        if program:
            form_data['program'] = program.pk
        
        form = BulkDocumentCreationForm(data=form_data)
        
        if form.is_valid():
            print("✅ Formulaire valide!")
            
            # Tester la prévisualisation
            matching_students = form.get_matching_students()
            existing_count = form.get_existing_documents_count()
            
            print(f"✅ Étudiants correspondants: {matching_students.count()}")
            print(f"✅ Documents existants: {existing_count}")
            print(f"✅ Nouveaux documents à créer: {matching_students.count() - existing_count}")
            
            # Afficher les étudiants correspondants
            print("\nÉtudiants correspondants:")
            for student in matching_students:
                print(f"  - {student.matricule} - {student.firstname} {student.lastname}")
            
            # Tester la création (simulation)
            print(f"\nSimulation de création de documents...")
            created_count, skipped_count, errors = form.create_documents()
            
            print(f"✅ Documents créés: {created_count}")
            print(f"✅ Documents ignorés (existants): {skipped_count}")
            
            if errors:
                print("❌ Erreurs:")
                for error in errors:
                    print(f"  - {error}")
            
            print("✅ Test de création en masse réussi!")
        else:
            print("❌ Formulaire invalide!")
            print("Erreurs:", form.errors)
    
    else:
        print("❌ Données insuffisantes pour le test")
        print("Assurez-vous d'avoir des étudiants approuvés, niveaux et années académiques en base")

if __name__ == "__main__":
    test_bulk_creation()
