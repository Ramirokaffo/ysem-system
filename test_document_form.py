#!/usr/bin/env python
"""
Script de test pour vérifier le formulaire OfficialDocument
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import Student, StudentLevel, OfficialDocument
from academic.models import Level, AcademicYear
from main.forms import OfficialDocumentForm

def test_form():
    print("=== Test du formulaire OfficialDocument ===")
    
    # Vérifier les données existantes
    students = Student.objects.all()
    levels = Level.objects.all()
    academic_years = AcademicYear.objects.all()
    
    print(f"Étudiants disponibles: {students.count()}")
    print(f"Niveaux disponibles: {levels.count()}")
    print(f"Années académiques disponibles: {academic_years.count()}")
    
    if students.exists() and levels.exists() and academic_years.exists():
        # Test avec des données valides
        student = students.first()
        level = levels.first()
        academic_year = academic_years.first()
        
        print(f"\nTest avec:")
        print(f"- Étudiant: {student.matricule} - {student.firstname} {student.lastname}")
        print(f"- Niveau: {level.name}")
        print(f"- Année académique: {academic_year.name}")
        
        # Données de test
        form_data = {
            'student': student.pk,
            'level': level.pk,
            'academic_year': academic_year.pk,
            'type': 'student_card',
            'status': 'available'
        }
        
        form = OfficialDocumentForm(data=form_data)
        
        if form.is_valid():
            print("✅ Formulaire valide!")
            
            # Vérifier si StudentLevel existe déjà
            student_level_exists = StudentLevel.objects.filter(
                student=student,
                level=level,
                academic_year=academic_year
            ).exists()
            
            print(f"StudentLevel existe déjà: {student_level_exists}")
            
            # Simuler la sauvegarde
            try:
                document = form.save(commit=False)
                print(f"Document créé: {document.type} pour {document.student_level}")
                print("✅ Test réussi!")
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde: {e}")
        else:
            print("❌ Formulaire invalide!")
            print("Erreurs:", form.errors)
    else:
        print("❌ Données insuffisantes pour le test")
        print("Assurez-vous d'avoir des étudiants, niveaux et années académiques en base")

if __name__ == "__main__":
    test_form()
