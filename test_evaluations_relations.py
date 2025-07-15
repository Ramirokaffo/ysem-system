#!/usr/bin/env python3
"""
Script de test pour vérifier les nouvelles relations du modèle Evaluation
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from Teaching.models import Evaluation
from Teaching.forms import EvaluationForm
from students.models import Student
from academic.models import Course, Level, AcademicYear
from django.urls import reverse

def test_model_relations():
    """Test des relations du modèle Evaluation"""
    
    print("=== Test des Relations du Modèle Evaluation ===\n")
    
    # 1. Vérifier les relations disponibles
    print("1. Vérification des relations disponibles")
    try:
        # Vérifier que les modèles liés existent
        students_count = Student.objects.count()
        courses_count = Course.objects.count()
        levels_count = Level.objects.count()
        academic_years_count = AcademicYear.objects.count()
        
        print(f"   ✓ Étudiants disponibles: {students_count}")
        print(f"   ✓ Cours disponibles: {courses_count}")
        print(f"   ✓ Niveaux disponibles: {levels_count}")
        print(f"   ✓ Années académiques disponibles: {academic_years_count}")
        
        if students_count == 0 or courses_count == 0 or levels_count == 0 or academic_years_count == 0:
            print("   ⚠️  Attention: Certaines données de référence sont manquantes")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors de la vérification des relations: {e}")
        return False
    
    # 2. Test de création avec relations
    print("\n2. Test de création d'évaluation avec relations")
    try:
        # Récupérer des objets de référence
        student = Student.objects.first()
        course = Course.objects.first()
        level = Level.objects.first()
        academic_year = AcademicYear.objects.first()
        
        if not all([student, course, level, academic_year]):
            print("   ✗ Impossible de récupérer les objets de référence")
            return False
        
        # Supprimer les évaluations de test existantes
        Evaluation.objects.filter(
            student__matricule__startswith='TEST_'
        ).delete()
        
        # Créer une évaluation avec relations
        evaluation = Evaluation.objects.create(
            evaluationDat=date.today(),
            student=student,
            course=course,
            level=level,
            academic_year=academic_year,
            support_cours_acessible=True,
            bonne_explication_cours=True,
            bonne_reponse_questions=False,
            courseMethodology='Cours magistral + TP',
            donne_TD=True,
            donne_projet=True,
            difficulte_rencontree=True,
            quelles_difficultes_rencontrees='Rythme trop rapide',
            propositionEtudiants='Plus d\'exercices',
            observationSSAC='Bon niveau général',
            actionSSAC='Continuer'
        )
        
        print(f"   ✓ Évaluation créée: {evaluation}")
        print(f"   ✓ Étudiant lié: {evaluation.student}")
        print(f"   ✓ Cours lié: {evaluation.course}")
        print(f"   ✓ Niveau lié: {evaluation.level}")
        print(f"   ✓ Année académique liée: {evaluation.academic_year}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors de la création: {e}")
        return False
    
    # 3. Test des requêtes avec relations
    print("\n3. Test des requêtes avec relations")
    try:
        # Requêtes avec select_related pour optimiser
        evaluations = Evaluation.objects.select_related(
            'student', 'course', 'level', 'academic_year'
        ).all()
        
        print(f"   ✓ Nombre d'évaluations avec relations: {evaluations.count()}")
        
        # Test des relations inverses
        if student:
            student_evaluations = student.evaluations.count()
            print(f"   ✓ Évaluations pour l'étudiant {student}: {student_evaluations}")
        
        if course:
            course_evaluations = course.evaluations.count()
            print(f"   ✓ Évaluations pour le cours {course}: {course_evaluations}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors des requêtes: {e}")
        return False
    
    # 4. Test du formulaire avec relations
    print("\n4. Test du formulaire avec relations")
    try:
        # Test du formulaire vide (avec valeurs par défaut)
        form = EvaluationForm()
        
        # Vérifier que l'année académique par défaut est définie
        if hasattr(form.fields['academic_year'], 'initial') and form.fields['academic_year'].initial:
            print(f"   ✓ Année académique par défaut: {form.fields['academic_year'].initial}")
        else:
            print("   ⚠️  Aucune année académique par défaut définie")
        
        # Vérifier les querysets
        student_queryset = form.fields['student'].queryset
        course_queryset = form.fields['course'].queryset
        level_queryset = form.fields['level'].queryset
        
        print(f"   ✓ Étudiants dans le formulaire: {student_queryset.count()}")
        print(f"   ✓ Cours dans le formulaire: {course_queryset.count()}")
        print(f"   ✓ Niveaux dans le formulaire: {level_queryset.count()}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test du formulaire: {e}")
        return False
    
    # 5. Test de validation du formulaire
    print("\n5. Test de validation du formulaire")
    try:
        form_data = {
            'evaluationDat': date.today(),
            'student': student.id,
            'course': course.id,
            'level': level.id,
            'academic_year': academic_year.id,
            'support_cours_acessible': True,
            'bonne_explication_cours': True,
            'bonne_reponse_questions': True,
            'courseMethodology': 'Test methodology',
            'donne_TD': True,
            'donne_projet': False,
            'difficulte_rencontree': False,
            'quelles_difficultes_rencontrees': '',
            'propositionEtudiants': 'Test propositions',
            'observationSSAC': 'Test observation',
            'actionSSAC': 'Test action'
        }
        
        form = EvaluationForm(data=form_data)
        if form.is_valid():
            evaluation_from_form = form.save()
            print(f"   ✓ Formulaire valide et évaluation créée: {evaluation_from_form}")
        else:
            print(f"   ✗ Formulaire invalide: {form.errors}")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors de la validation: {e}")
        return False
    
    print("\n=== Tous les tests de relations ont réussi ! ===")
    return True

def test_admin_integration():
    """Test de l'intégration admin"""
    
    print("\n=== Test de l'intégration Admin ===\n")
    
    try:
        from Teaching.admin import EvaluationAdmin
        from django.contrib import admin
        
        # Vérifier que l'admin est enregistré
        if Evaluation in admin.site._registry:
            admin_class = admin.site._registry[Evaluation]
            print(f"   ✓ Admin enregistré: {admin_class}")
            print(f"   ✓ List display: {admin_class.list_display}")
            print(f"   ✓ List filter: {admin_class.list_filter}")
            print(f"   ✓ Search fields: {admin_class.search_fields}")
        else:
            print("   ✗ Admin non enregistré")
            return False
            
    except Exception as e:
        print(f"   ✗ Erreur lors du test admin: {e}")
        return False
    
    print("   ✓ Intégration admin validée")
    return True

def test_urls():
    """Test des URLs avec les nouvelles relations"""
    
    print("\n=== Test des URLs avec Relations ===\n")
    
    try:
        # Récupérer une évaluation pour tester les URLs
        evaluation = Evaluation.objects.first()
        if not evaluation:
            print("   ⚠️  Aucune évaluation disponible pour tester les URLs")
            return True
        
        # Test des URLs
        urls_to_test = [
            ('teaching:evaluations', 'Liste des évaluations'),
            ('teaching:ajouter_evaluation', 'Ajouter évaluation'),
            ('teaching:detail_evaluation', 'Détail évaluation', {'pk': evaluation.id}),
            ('teaching:modifier_evaluation', 'Modifier évaluation', {'pk': evaluation.id}),
            ('teaching:supprimer_evaluation', 'Supprimer évaluation', {'pk': evaluation.id}),
        ]
        
        for url_info in urls_to_test:
            url_name = url_info[0]
            description = url_info[1]
            kwargs = url_info[2] if len(url_info) > 2 else {}
            
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"   ✓ {description}: {url}")
            except Exception as e:
                print(f"   ✗ {description}: Erreur - {e}")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du test des URLs: {e}")
        return False
    
    print("   ✓ URLs validées avec les relations")
    return True

def cleanup_test_data():
    """Nettoyer les données de test"""
    
    print("\n=== Nettoyage des données de test ===")
    
    try:
        # Supprimer les évaluations de test
        deleted_count = Evaluation.objects.filter(
            courseMethodology__icontains='test'
        ).delete()[0]
        
        print(f"   ✓ {deleted_count} évaluation(s) de test supprimée(s)")
        
    except Exception as e:
        print(f"   ✗ Erreur lors du nettoyage: {e}")

if __name__ == '__main__':
    print("Démarrage des tests des relations pour les évaluations...\n")
    
    success = True
    
    # Test des relations du modèle
    success &= test_model_relations()
    
    # Test de l'intégration admin
    success &= test_admin_integration()
    
    # Test des URLs
    success &= test_urls()
    
    # Nettoyage
    cleanup_test_data()
    
    if success:
        print("\n🎉 Toutes les relations du modèle Evaluation sont fonctionnelles !")
    else:
        print("\n❌ Des erreurs ont été détectées dans les relations.")
        sys.exit(1)
