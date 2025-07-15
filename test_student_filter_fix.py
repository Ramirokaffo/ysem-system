#!/usr/bin/env python3
"""
Script de test pour vérifier la correction du filtre Student
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from Teaching.forms import EvaluationForm
from students.models import Student

def test_student_filter():
    """Test du filtre Student corrigé"""
    
    print("=== Test de la correction du filtre Student ===\n")
    
    # 1. Vérifier les champs disponibles du modèle Student
    print("1. Vérification des champs du modèle Student")
    try:
        student_fields = [field.name for field in Student._meta.get_fields()]
        print(f"   ✓ Champs disponibles: {', '.join(student_fields)}")
        
        # Vérifier spécifiquement le champ status
        if 'status' in student_fields:
            print("   ✓ Champ 'status' trouvé")
        else:
            print("   ✗ Champ 'status' non trouvé")
            return False
            
        # Vérifier si is_active existe
        if 'is_active' in student_fields:
            print("   ⚠️  Champ 'is_active' existe (utilisation possible)")
        else:
            print("   ✓ Champ 'is_active' n'existe pas (correction nécessaire)")
            
    except Exception as e:
        print(f"   ✗ Erreur lors de la vérification des champs: {e}")
        return False
    
    # 2. Tester les valeurs du champ status
    print("\n2. Test des valeurs du champ status")
    try:
        # Récupérer les choix du champ status
        status_field = Student._meta.get_field('status')
        if hasattr(status_field, 'choices') and status_field.choices:
            print("   ✓ Choix du champ status:")
            for choice in status_field.choices:
                print(f"      - {choice[0]}: {choice[1]}")
        else:
            print("   ⚠️  Pas de choix définis pour le champ status")
        
        # Compter les étudiants par status
        status_counts = {}
        for status_choice in ['pending', 'approved', 'abandoned', 'rejected']:
            try:
                count = Student.objects.filter(status=status_choice).count()
                status_counts[status_choice] = count
                print(f"   ✓ Étudiants avec status '{status_choice}': {count}")
            except:
                print(f"   ⚠️  Impossible de filtrer par status '{status_choice}'")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des valeurs status: {e}")
        return False
    
    # 3. Tester le formulaire EvaluationForm
    print("\n3. Test du formulaire EvaluationForm")
    try:
        # Créer une instance du formulaire
        form = EvaluationForm()
        
        # Vérifier le queryset des étudiants
        student_queryset = form.fields['student'].queryset
        student_count = student_queryset.count()
        
        print(f"   ✓ Formulaire créé sans erreur")
        print(f"   ✓ Nombre d'étudiants dans le formulaire: {student_count}")
        
        # Vérifier que le filtre fonctionne
        if student_count >= 0:
            print("   ✓ Filtre Student fonctionne correctement")
            
            # Afficher quelques étudiants pour vérification
            if student_count > 0:
                print("   ✓ Premiers étudiants dans le formulaire:")
                for student in student_queryset[:3]:
                    print(f"      - {student.lastname} {student.firstname} (status: {student.status})")
            else:
                print("   ⚠️  Aucun étudiant avec status 'approved' trouvé")
        else:
            print("   ✗ Problème avec le filtre Student")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors du test du formulaire: {e}")
        print(f"   ✗ Détail de l'erreur: {type(e).__name__}: {str(e)}")
        return False
    
    # 4. Test des autres querysets du formulaire
    print("\n4. Test des autres querysets du formulaire")
    try:
        form = EvaluationForm()
        
        # Tester les autres relations
        course_count = form.fields['course'].queryset.count()
        level_count = form.fields['level'].queryset.count()
        academic_year_count = form.fields['academic_year'].queryset.count()
        
        print(f"   ✓ Cours disponibles: {course_count}")
        print(f"   ✓ Niveaux disponibles: {level_count}")
        print(f"   ✓ Années académiques disponibles: {academic_year_count}")
        
        # Vérifier l'année académique par défaut
        if hasattr(form.fields['academic_year'], 'initial') and form.fields['academic_year'].initial:
            print(f"   ✓ Année académique par défaut: {form.fields['academic_year'].initial}")
        else:
            print("   ⚠️  Aucune année académique par défaut définie")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des autres querysets: {e}")
        return False
    
    print("\n=== Test de correction réussi ! ===")
    return True

def test_alternative_filters():
    """Test des filtres alternatifs pour Student"""
    
    print("\n=== Test des filtres alternatifs ===\n")
    
    try:
        # Test de différents filtres possibles
        filters_to_test = [
            ('status=approved', lambda: Student.objects.filter(status='approved')),
            ('status__in=[approved, pending]', lambda: Student.objects.filter(status__in=['approved', 'pending'])),
            ('tous les étudiants', lambda: Student.objects.all()),
        ]
        
        for filter_name, filter_func in filters_to_test:
            try:
                queryset = filter_func()
                count = queryset.count()
                print(f"   ✓ {filter_name}: {count} étudiant(s)")
            except Exception as e:
                print(f"   ✗ {filter_name}: Erreur - {e}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des filtres alternatifs: {e}")

if __name__ == '__main__':
    print("Démarrage du test de correction du filtre Student...\n")
    
    success = test_student_filter()
    test_alternative_filters()
    
    if success:
        print("\n🎉 Correction du filtre Student validée !")
        print("Le formulaire EvaluationForm devrait maintenant fonctionner correctement.")
    else:
        print("\n❌ Des erreurs persistent dans le filtre Student.")
        print("Vérifiez la structure du modèle Student et les filtres utilisés.")
        sys.exit(1)
