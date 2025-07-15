#!/usr/bin/env python
"""
Test de la fonctionnalité de décharge/retour des documents
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from students.models import OfficialDocument, Student, StudentLevel
from academic.models import Level, AcademicYear
from django.utils import timezone

def test_document_toggle_functionality():
    """Test de la fonctionnalité de décharge/retour des documents"""
    print("🚀 Test de la fonctionnalité de décharge/retour des documents")
    print("=" * 70)
    
    # Vérifier les modèles
    print("\n📋 Vérification des modèles...")
    print(f"   Documents officiels: {OfficialDocument.objects.count()}")
    print(f"   Étudiants: {Student.objects.count()}")
    print(f"   Niveaux d'étudiants: {StudentLevel.objects.count()}")
    
    # Vérifier les choix de statut
    print("\n🔍 Vérification des choix de statut...")
    status_choices = OfficialDocument._meta.get_field('status').choices
    print("   Statuts disponibles:")
    for value, label in status_choices:
        print(f"     - {value}: {label}")
    
    # Vérifier les champs du modèle
    print("\n📊 Vérification des champs du modèle...")
    fields = [field.name for field in OfficialDocument._meta.fields]
    print("   Champs disponibles:")
    for field in fields:
        print(f"     - {field}")
    
    # Test avec un document existant
    print("\n🧪 Test avec les documents existants...")
    documents = OfficialDocument.objects.all()[:3]
    
    for doc in documents:
        print(f"\n   📄 Document: {doc.get_type_display()}")
        print(f"      Étudiant: {doc.student_level.student.matricule} - {doc.student_level.student.firstname} {doc.student_level.student.lastname}")
        print(f"      Statut actuel: {doc.get_status_display()}")
        print(f"      Date de décharge: {doc.withdrawn_date or 'Non définie'}")
        print(f"      Date de retour: {getattr(doc, 'returned_at', 'Champ non disponible')}")
    
    # Test de création d'un document de test
    print("\n🔧 Test de création d'un document de test...")
    try:
        # Récupérer un étudiant et un niveau
        student_level = StudentLevel.objects.first()
        if student_level:
            # Créer un document de test
            test_doc = OfficialDocument.objects.create(
                student_level=student_level,
                type='certificate',
                status='available'
            )
            print(f"   ✅ Document de test créé: {test_doc.pk}")
            
            # Test de décharge
            test_doc.status = 'withdrawn'
            test_doc.withdrawn_date = timezone.now().date()
            test_doc.save()
            print(f"   ✅ Document déchargé: {test_doc.get_status_display()}")
            
            # Test de retour
            if hasattr(test_doc, 'returned_at'):
                test_doc.status = 'returned'
                test_doc.returned_at = timezone.now().date()
                test_doc.save()
                print(f"   ✅ Document retourné: {test_doc.get_status_display()}")
            else:
                print("   ⚠️  Champ 'returned_at' non disponible - migration nécessaire")
            
            # Nettoyer
            test_doc.delete()
            print("   🗑️  Document de test supprimé")
        else:
            print("   ⚠️  Aucun StudentLevel trouvé pour le test")
    
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    print("\n✅ Test terminé!")

def test_migration_status():
    """Vérifier si la migration a été appliquée"""
    print("\n🔍 Vérification du statut de la migration...")
    
    try:
        # Tester si le champ returned_at existe
        doc = OfficialDocument.objects.first()
        if doc:
            returned_at = getattr(doc, 'returned_at', None)
            print(f"   Champ 'returned_at': {'✅ Disponible' if hasattr(doc, 'returned_at') else '❌ Non disponible'}")
        
        # Tester les choix de statut
        status_choices = dict(OfficialDocument._meta.get_field('status').choices)
        has_returned = 'returned' in status_choices
        print(f"   Statut 'returned': {'✅ Disponible' if has_returned else '❌ Non disponible'}")
        
        if has_returned:
            print(f"   Label du statut 'returned': {status_choices['returned']}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification: {e}")

if __name__ == '__main__':
    test_migration_status()
    test_document_toggle_functionality()
