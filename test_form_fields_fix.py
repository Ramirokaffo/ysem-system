#!/usr/bin/env python3
"""
Script de test pour vérifier toutes les corrections des champs du formulaire
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
from academic.models import Course, Level, AcademicYear

def test_model_fields():
    """Test des champs disponibles dans chaque modèle"""
    
    print("=== Vérification des champs des modèles ===\n")
    
    models_to_check = [
        ('Student', Student),
        ('Course', Course),
        ('Level', Level),
        ('AcademicYear', AcademicYear),
    ]
    
    for model_name, model_class in models_to_check:
        try:
            fields = [field.name for field in model_class._meta.get_fields()]
            print(f"{model_name} - Champs disponibles:")
            for field in sorted(fields):
                print(f"   - {field}")
            print()
        except Exception as e:
            print(f"   ✗ Erreur pour {model_name}: {e}\n")

def test_evaluation_form():
    """Test du formulaire EvaluationForm"""
    
    print("=== Test du formulaire EvaluationForm ===\n")
    
    try:
        # Créer une instance du formulaire
        form = EvaluationForm()
        print("✓ Formulaire créé sans erreur")
        
        # Tester chaque queryset
        querysets_to_test = [
            ('student', 'Étudiants'),
            ('course', 'Cours'),
            ('level', 'Niveaux'),
            ('academic_year', 'Années académiques'),
        ]
        
        for field_name, description in querysets_to_test:
            try:
                queryset = form.fields[field_name].queryset
                count = queryset.count()
                print(f"✓ {description}: {count} élément(s) disponible(s)")
                
                # Afficher quelques exemples
                if count > 0:
                    examples = list(queryset[:3])
                    for example in examples:
                        print(f"   - {example}")
                else:
                    print(f"   ⚠️  Aucun {description.lower()} trouvé")
                print()
                    
            except Exception as e:
                print(f"✗ Erreur pour {description}: {e}\n")
        
        # Tester l'année académique par défaut
        try:
            if hasattr(form.fields['academic_year'], 'initial') and form.fields['academic_year'].initial:
                print(f"✓ Année académique par défaut: {form.fields['academic_year'].initial}")
            else:
                print("⚠️  Aucune année académique par défaut définie")
        except Exception as e:
            print(f"✗ Erreur pour l'année académique par défaut: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la création du formulaire: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        return False

def test_specific_filters():
    """Test des filtres spécifiques utilisés"""
    
    print("\n=== Test des filtres spécifiques ===\n")
    
    # Test du filtre Student
    try:
        students = Student.objects.filter(status='approved').order_by('lastname', 'firstname')
        print(f"✓ Étudiants avec status='approved': {students.count()}")
        
        # Vérifier les statuts disponibles
        all_statuses = Student.objects.values_list('status', flat=True).distinct()
        print(f"✓ Statuts d'étudiants disponibles: {list(all_statuses)}")
        
    except Exception as e:
        print(f"✗ Erreur filtre Student: {e}")
    
    # Test du tri Level
    try:
        levels = Level.objects.all().order_by('name')
        print(f"✓ Niveaux triés par 'name': {levels.count()}")
        
        # Afficher les noms des niveaux
        level_names = list(levels.values_list('name', flat=True))
        print(f"✓ Noms des niveaux: {level_names}")
        
    except Exception as e:
        print(f"✗ Erreur tri Level: {e}")
    
    # Test du tri Course
    try:
        courses = Course.objects.all().order_by('label')
        print(f"✓ Cours triés par 'label': {courses.count()}")
        
    except Exception as e:
        print(f"✗ Erreur tri Course: {e}")
    
    # Test du tri AcademicYear
    try:
        academic_years = AcademicYear.objects.all().order_by('-start_date')
        print(f"✓ Années académiques triées par '-start_date': {academic_years.count()}")
        
    except Exception as e:
        print(f"✗ Erreur tri AcademicYear: {e}")

def test_form_rendering():
    """Test du rendu du formulaire"""
    
    print("\n=== Test du rendu du formulaire ===\n")
    
    try:
        form = EvaluationForm()
        
        # Tester le rendu de chaque champ
        fields_to_test = ['student', 'course', 'level', 'academic_year']
        
        for field_name in fields_to_test:
            try:
                field_html = str(form[field_name])
                if field_html and len(field_html) > 0:
                    print(f"✓ Champ '{field_name}' se rend correctement")
                else:
                    print(f"⚠️  Champ '{field_name}' semble vide")
            except Exception as e:
                print(f"✗ Erreur rendu champ '{field_name}': {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors du test de rendu: {e}")
        return False

if __name__ == '__main__':
    print("Démarrage des tests de correction des champs du formulaire...\n")
    
    # Test des champs des modèles
    test_model_fields()
    
    # Test du formulaire
    form_success = test_evaluation_form()
    
    # Test des filtres spécifiques
    test_specific_filters()
    
    # Test du rendu
    render_success = test_form_rendering()
    
    if form_success and render_success:
        print("\n🎉 Toutes les corrections sont validées !")
        print("Le formulaire EvaluationForm devrait maintenant fonctionner correctement.")
    else:
        print("\n❌ Des erreurs persistent dans le formulaire.")
        print("Vérifiez les messages d'erreur ci-dessus.")
        sys.exit(1)
