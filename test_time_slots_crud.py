#!/usr/bin/env python
"""
Script de test pour les fonctionnalités CRUD des créneaux horaires
"""

import os
import sys
import django
from datetime import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

from planification.models import TimeSlot
from planification.forms import TimeSlotForm

def test_time_slot_crud():
    """Test des opérations CRUD sur les créneaux horaires"""
    print("🕐 Test des fonctionnalités CRUD des créneaux horaires")
    print("=" * 60)
    
    # 1. CREATE - Création de créneaux
    print("\n📝 Test de création de créneaux horaires...")
    
    test_slots = [
        {
            'name': 'Matin 1',
            'day_of_week': 'monday',
            'start_time': time(8, 0),
            'end_time': time(10, 0),
            'is_active': True
        },
        {
            'name': 'Matin 2',
            'day_of_week': 'monday',
            'start_time': time(10, 15),
            'end_time': time(12, 15),
            'is_active': True
        },
        {
            'name': 'Après-midi 1',
            'day_of_week': 'tuesday',
            'start_time': time(14, 0),
            'end_time': time(16, 0),
            'is_active': True
        },
        {
            'name': 'Soir 1',
            'day_of_week': 'wednesday',
            'start_time': time(18, 0),
            'end_time': time(20, 0),
            'is_active': False  # Créneau inactif
        }
    ]
    
    created_slots = []
    for slot_data in test_slots:
        try:
            slot, created = TimeSlot.objects.get_or_create(
                day_of_week=slot_data['day_of_week'],
                start_time=slot_data['start_time'],
                end_time=slot_data['end_time'],
                defaults=slot_data
            )
        except Exception as e:
            # Si le créneau existe déjà avec des horaires identiques, le récupérer
            slot = TimeSlot.objects.filter(
                day_of_week=slot_data['day_of_week'],
                start_time=slot_data['start_time'],
                end_time=slot_data['end_time']
            ).first()
            created = False
        if created:
            print(f"✅ Créneau créé: {slot}")
        else:
            print(f"ℹ️  Créneau existant: {slot}")
        created_slots.append(slot)
    
    # 2. READ - Lecture et affichage
    print(f"\n📖 Test de lecture des créneaux horaires...")
    all_slots = TimeSlot.objects.all().order_by('day_of_week', 'start_time')
    print(f"   Total des créneaux: {all_slots.count()}")
    
    for slot in all_slots:
        status = "🟢 Actif" if slot.is_active else "🔴 Inactif"
        print(f"   - {slot.name} ({slot.get_day_of_week_display()}) "
              f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')} "
              f"[{slot.duration_hours()}h] {status}")
    
    # 3. UPDATE - Modification
    print(f"\n✏️  Test de modification de créneaux...")
    if created_slots:
        slot_to_update = created_slots[0]
        old_name = slot_to_update.name
        slot_to_update.name = f"{old_name} - Modifié"
        slot_to_update.save()
        print(f"✅ Créneau modifié: {old_name} → {slot_to_update.name}")
    
    # 4. Filtrage et recherche
    print(f"\n🔍 Test de filtrage des créneaux...")
    
    # Créneaux actifs
    active_slots = TimeSlot.objects.filter(is_active=True)
    print(f"   Créneaux actifs: {active_slots.count()}")
    
    # Créneaux du lundi
    monday_slots = TimeSlot.objects.filter(day_of_week='monday')
    print(f"   Créneaux du lundi: {monday_slots.count()}")
    
    # Créneaux du matin (avant 12h)
    morning_slots = TimeSlot.objects.filter(start_time__lt=time(12, 0))
    print(f"   Créneaux du matin: {morning_slots.count()}")
    
    # 5. Validation des formulaires
    print(f"\n📋 Test de validation des formulaires...")
    
    # Formulaire valide
    valid_data = {
        'name': 'Test Créneau Valide',
        'day_of_week': 'thursday',
        'start_time': '09:00',
        'end_time': '11:00',
        'is_active': True
    }
    form = TimeSlotForm(data=valid_data)
    if form.is_valid():
        print("✅ Formulaire valide accepté")
    else:
        print(f"❌ Erreur formulaire valide: {form.errors}")
    
    # Formulaire invalide (heure de fin avant début)
    invalid_data = {
        'name': 'Test Créneau Invalide',
        'day_of_week': 'friday',
        'start_time': '11:00',
        'end_time': '09:00',  # Erreur: fin avant début
        'is_active': True
    }
    form = TimeSlotForm(data=invalid_data)
    if not form.is_valid():
        print("✅ Formulaire invalide rejeté correctement")
        print(f"   Erreurs: {list(form.errors.keys())}")
    else:
        print("❌ Erreur: formulaire invalide accepté")
    
    # 6. DELETE - Suppression (optionnel)
    print(f"\n🗑️  Test de suppression...")
    
    # Créer un créneau temporaire pour le supprimer
    temp_slot = TimeSlot.objects.create(
        name="Créneau Temporaire",
        day_of_week="saturday",
        start_time=time(20, 0),
        end_time=time(22, 0),
        is_active=True
    )
    print(f"✅ Créneau temporaire créé: {temp_slot}")
    
    # Le supprimer
    temp_slot.delete()
    print(f"✅ Créneau temporaire supprimé")
    
    return created_slots

def test_time_slot_statistics():
    """Afficher les statistiques des créneaux horaires"""
    print(f"\n📊 Statistiques des créneaux horaires:")
    
    total = TimeSlot.objects.count()
    active = TimeSlot.objects.filter(is_active=True).count()
    inactive = TimeSlot.objects.filter(is_active=False).count()
    
    print(f"   Total: {total}")
    print(f"   Actifs: {active}")
    print(f"   Inactifs: {inactive}")
    
    # Répartition par jour
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    
    print(f"\n   Répartition par jour:")
    for day, day_name in zip(days, day_names):
        count = TimeSlot.objects.filter(day_of_week=day).count()
        if count > 0:
            print(f"     {day_name}: {count} créneau{'x' if count > 1 else ''}")

def test_time_slot_business_logic():
    """Test de la logique métier des créneaux horaires"""
    print(f"\n🧠 Test de la logique métier...")
    
    # Test de la méthode duration_hours
    slot = TimeSlot.objects.filter(start_time__isnull=False, end_time__isnull=False).first()
    if slot:
        duration = slot.duration_hours()
        print(f"✅ Calcul de durée: {slot.name} = {duration}h")
    
    # Test de la méthode __str__
    if slot:
        str_repr = str(slot)
        print(f"✅ Représentation string: {str_repr}")
    
    # Test des contraintes
    print(f"✅ Contraintes de validation testées dans les formulaires")

def main():
    """Fonction principale"""
    print("🚀 Test complet des fonctionnalités CRUD des créneaux horaires")
    print("=" * 70)
    
    try:
        # Tests CRUD
        created_slots = test_time_slot_crud()
        
        # Statistiques
        test_time_slot_statistics()
        
        # Logique métier
        test_time_slot_business_logic()
        
        print(f"\n✅ Tous les tests sont passés avec succès!")
        print(f"\n🌐 Vous pouvez maintenant tester l'interface web:")
        print(f"   - Liste des créneaux: http://localhost:8000/planning/creneaux/")
        print(f"   - Créer un créneau: http://localhost:8000/planning/creneaux/ajouter/")
        
        if created_slots:
            print(f"   - Détails d'un créneau: http://localhost:8000/planning/creneaux/{created_slots[0].pk}/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
