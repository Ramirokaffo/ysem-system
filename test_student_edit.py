#!/usr/bin/env python
"""
Script de test pour vérifier la vue etudiant_edit
"""
import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append('/Users/user/Desktop/Programmation/ysem-project')

django.setup()

from students.models import Student
from main.forms import StudentEditForm, StudentMetaDataEditForm

def test_student_edit_forms():
    """Test des formulaires de modification"""
    
    # Vérifier qu'il y a des étudiants dans la base
    students = Student.objects.all()
    print(f"Nombre d'étudiants trouvés: {students.count()}")
    
    if students.exists():
        student = students.first()
        print(f"Test avec l'étudiant: {student.matricule} - {student.firstname} {student.lastname}")
        
        try:
            # Tester le formulaire principal
            student_form = StudentEditForm(instance=student)
            print(f"✅ StudentEditForm créé avec succès")
            print(f"   Champs disponibles: {list(student_form.fields.keys())}")
            
            # Tester le formulaire des métadonnées
            if student.metadata:
                metadata_form = StudentMetaDataEditForm(instance=student.metadata)
                print(f"✅ StudentMetaDataEditForm créé avec succès")
                print(f"   Champs disponibles: {list(metadata_form.fields.keys())}")
            else:
                print("⚠️  Pas de métadonnées pour cet étudiant")
            
            # Tester la validation
            test_data = {
                'firstname': 'Test',
                'lastname': 'Étudiant',
                'gender': 'M',
                'lang': 'fr',
                'status': 'approved'
            }
            
            form_test = StudentEditForm(test_data, instance=student)
            if form_test.is_valid():
                print("✅ Validation du formulaire réussie")
            else:
                print(f"❌ Erreurs de validation: {form_test.errors}")
            
            print("✅ Test des formulaires réussi")
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Aucun étudiant trouvé dans la base de données")

if __name__ == "__main__":
    test_student_edit_forms()
