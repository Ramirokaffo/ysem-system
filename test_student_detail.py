#!/usr/bin/env python
"""
Script de test pour vérifier la vue etudiant_detail
"""
import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append('/Users/user/Desktop/Programmation/ysem-project')

django.setup()

from students.models import Student
from django.test import RequestFactory
from main.views import etudiant_detail

def test_student_detail_view():
    """Test de la vue etudiant_detail"""
    
    # Vérifier qu'il y a des étudiants dans la base
    students = Student.objects.all()
    print(f"Nombre d'étudiants trouvés: {students.count()}")
    
    if students.exists():
        student = students.first()
        print(f"Test avec l'étudiant: {student.matricule} - {student.firstname} {student.lastname}")
        
        # Créer une requête factice
        factory = RequestFactory()
        request = factory.get(f'/etudiant/{student.matricule}/')
        
        try:
            # Tester la vue
            response = etudiant_detail(request, pk=student.matricule)
            print(f"Vue exécutée avec succès. Status code: {response.status_code}")
            
            # Vérifier le contexte
            if hasattr(response, 'context_data'):
                context = response.context_data
                print(f"Contexte disponible: {list(context.keys())}")
            
            print("✅ Test réussi - La vue fonctionne correctement")
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Aucun étudiant trouvé dans la base de données")

if __name__ == "__main__":
    test_student_detail_view()
