#!/usr/bin/env python
"""
Script pour appliquer la migration et tester la fonctionnalité de décharge/retour
"""
import os
import sys
import django
import subprocess

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

def apply_migration():
    """Appliquer la migration"""
    print("🔄 Application de la migration...")
    try:
        result = subprocess.run(['python', 'manage.py', 'migrate', 'students'], 
                              capture_output=True, text=True, check=True)
        print("✅ Migration appliquée avec succès!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'application de la migration: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False
    return True

def test_functionality():
    """Tester la fonctionnalité"""
    print("\n🧪 Test de la fonctionnalité de décharge/retour...")
    
    from students.models import OfficialDocument
    from django.utils import timezone
    
    # Vérifier les choix de statut
    status_choices = dict(OfficialDocument._meta.get_field('status').choices)
    print(f"   Statuts disponibles: {list(status_choices.keys())}")
    
    # Vérifier si le champ returned_at existe
    doc = OfficialDocument.objects.first()
    if doc:
        has_returned_at = hasattr(doc, 'returned_at')
        print(f"   Champ 'returned_at': {'✅ Disponible' if has_returned_at else '❌ Non disponible'}")
        
        if has_returned_at:
            print(f"   Valeur actuelle de returned_at: {doc.returned_at}")
    
    # Test de création d'un document avec le nouveau statut
    try:
        from students.models import StudentLevel
        student_level = StudentLevel.objects.first()
        
        if student_level:
            # Créer un document de test
            test_doc = OfficialDocument.objects.create(
                student_level=student_level,
                type='certificate',
                status='returned',  # Nouveau statut
                returned_at=timezone.now().date()
            )
            print(f"   ✅ Document de test créé avec statut 'returned': {test_doc.pk}")
            
            # Nettoyer
            test_doc.delete()
            print("   🗑️  Document de test supprimé")
        else:
            print("   ⚠️  Aucun StudentLevel trouvé pour le test")
    
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")

def main():
    print("🚀 Application de la migration et test de la fonctionnalité")
    print("=" * 60)
    
    # Appliquer la migration
    if apply_migration():
        # Tester la fonctionnalité
        test_functionality()
    
    print("\n✅ Script terminé!")

if __name__ == '__main__':
    main()
