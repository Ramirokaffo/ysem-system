#!/usr/bin/env python
"""
Script de test pour vérifier le système CRUD du suivi des cours
"""
import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from Teaching.models import TeachingMonitoring, Lecturer
from academic.models import AcademicYear, Course, Level

def test_suivi_cours_crud():
    """Test du système CRUD pour le suivi des cours"""
    print("=== Test du système CRUD - Suivi des cours ===\n")
    
    try:
        # Vérifier les données nécessaires
        lecturer = Lecturer.objects.first()
        course = Course.objects.first()
        level = Level.objects.first()
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        
        if not all([lecturer, course, level, academic_year]):
            print("❌ Données manquantes pour les tests:")
            print(f"   - Enseignant: {'✓' if lecturer else '✗'}")
            print(f"   - Cours: {'✓' if course else '✗'}")
            print(f"   - Niveau: {'✓' if level else '✗'}")
            print(f"   - Année académique: {'✓' if academic_year else '✗'}")
            return
        
        print(f"Données de test :")
        print(f"   - Enseignant: {lecturer.firstname} {lecturer.lastname}")
        print(f"   - Cours: {course.label}")
        print(f"   - Niveau: {level.name}")
        print(f"   - Année académique: {academic_year}\n")
        
        # Test 1: CREATE - Création d'un suivi
        print("Test 1: Création d'un suivi de cours")
        suivi = TeachingMonitoring.objects.create(
            date=date.today(),
            lecturer=lecturer,
            course=course,
            level=level,
            academic_year=academic_year,
            totalChapterCount=10,
            chapitre_fait=6,
            contenu_seance_prevu=20,
            contenu_effectif_seance=15,
            travaux_preparatoires=True,
            groupWork=True,
            classWork=True,
            homeWork=False,
            pedagogicActivities=True,
            TDandTP=True,
            projet_fin_cours="Application web complète",
            association_pratique_aux_enseigements="Stage en entreprise",
            observation="Bon niveau général des étudiants",
            solution="Renforcer les exercices pratiques",
            generalObservation="Progression satisfaisante"
        )
        print(f"✅ Suivi créé avec l'ID: {suivi.id}")
        print(f"   Taux de couverture chapitres: {suivi.taux_couverture_chapitre()}%")
        print(f"   Taux de couverture séances: {suivi.taux_couverture_seance()}%")
        print(f"   Statut d'avancement: {suivi.statut_avancement()}")
        print(f"   Couleur de barre: {suivi.couleur_barre()}\n")
        
        # Test 2: READ - Lecture des données
        print("Test 2: Lecture des données du suivi")
        suivi_lu = TeachingMonitoring.objects.get(id=suivi.id)
        print(f"✅ Suivi lu: {suivi_lu}")
        print(f"   Date: {suivi_lu.date}")
        print(f"   Enseignant: {suivi_lu.lecturer.firstname} {suivi_lu.lecturer.lastname}")
        print(f"   Cours: {suivi_lu.course.label}\n")
        
        # Test 3: UPDATE - Modification des données
        print("Test 3: Modification du suivi")
        suivi.chapitre_fait = 8
        suivi.contenu_effectif_seance = 18
        suivi.observation = "Amélioration notable de la participation"
        suivi.save()
        
        suivi_modifie = TeachingMonitoring.objects.get(id=suivi.id)
        print(f"✅ Suivi modifié:")
        print(f"   Chapitres faits: {suivi_modifie.chapitre_fait}/{suivi_modifie.totalChapterCount}")
        print(f"   Nouveau taux chapitres: {suivi_modifie.taux_couverture_chapitre()}%")
        print(f"   Nouveau taux séances: {suivi_modifie.taux_couverture_seance()}%")
        print(f"   Nouvelle observation: {suivi_modifie.observation}\n")
        
        # Test 4: Filtrage et recherche
        print("Test 4: Filtrage et recherche")
        
        # Filtrage par enseignant
        suivis_enseignant = TeachingMonitoring.objects.filter(lecturer=lecturer)
        print(f"✅ Suivis pour l'enseignant {lecturer.firstname} {lecturer.lastname}: {suivis_enseignant.count()}")
        
        # Filtrage par cours
        suivis_cours = TeachingMonitoring.objects.filter(course=course)
        print(f"✅ Suivis pour le cours {course.label}: {suivis_cours.count()}")
        
        # Filtrage par année académique
        suivis_annee = TeachingMonitoring.objects.filter(academic_year=academic_year)
        print(f"✅ Suivis pour l'année {academic_year}: {suivis_annee.count()}\n")
        
        # Test 5: Statistiques et méthodes calculées
        print("Test 5: Méthodes calculées et statistiques")
        for s in TeachingMonitoring.objects.all()[:3]:
            print(f"   Suivi {s.id}:")
            print(f"     - Taux chapitres: {s.taux_couverture_chapitre()}%")
            print(f"     - Taux séances: {s.taux_couverture_seance()}%")
            print(f"     - Statut: {s.statut_avancement()}")
            print(f"     - Couleur: {s.couleur_barre()}")
        print()
        
        # Test 6: DELETE - Suppression
        print("Test 6: Suppression du suivi de test")
        suivi_id = suivi.id
        suivi.delete()
        
        # Vérifier que le suivi a été supprimé
        try:
            TeachingMonitoring.objects.get(id=suivi_id)
            print("❌ Erreur: Le suivi n'a pas été supprimé")
        except TeachingMonitoring.DoesNotExist:
            print(f"✅ Suivi {suivi_id} supprimé avec succès\n")
        
        print("=== Tous les tests CRUD sont passés avec succès ! ===")
        
        # Statistiques finales
        total_suivis = TeachingMonitoring.objects.count()
        print(f"\nStatistiques finales:")
        print(f"   - Total des suivis en base: {total_suivis}")
        print(f"   - Enseignants avec suivi: {TeachingMonitoring.objects.values('lecturer').distinct().count()}")
        print(f"   - Cours avec suivi: {TeachingMonitoring.objects.values('course').distinct().count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_suivi_cours_crud()
