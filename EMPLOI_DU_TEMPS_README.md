# 📅 Système de Gestion d'Emploi du Temps - YSEM

## 🎯 Vue d'ensemble

Le système de gestion d'emploi du temps de YSEM permet de créer, gérer et générer automatiquement des emplois du temps pour les différents niveaux d'études. Il prend en compte les disponibilités des enseignants, les salles de classe et les créneaux horaires pour optimiser la planification des cours.

## ✨ Fonctionnalités principales

### 1. 📋 Gestion des Emplois du Temps
- **Création manuelle** d'emplois du temps avec paramètres personnalisables
- **Visualisation détaillée** par semaine avec toutes les séances
- **Filtrage et recherche** avancés
- **Statuts de suivi** : Brouillon, Actif, Archivé

### 2. 🤖 Génération Automatique
- **Algorithme intelligent** qui respecte les contraintes
- **Prise en compte des disponibilités** des enseignants
- **Optimisation des créneaux** (privilégier le matin, éviter les séances consécutives)
- **Paramètres configurables** (nombre de séances par semaine, maximum par jour)

### 3. 👨‍🏫 Gestion des Disponibilités
- **Configuration des disponibilités** par enseignant et créneau
- **Trois statuts** : Disponible, Préféré, Indisponible
- **Périodes spécifiques** pour gérer les congés temporaires
- **Notes contextuelles** pour chaque disponibilité

### 4. 🎨 Interface Utilisateur
- **Design neumorphism** cohérent avec le reste de l'application
- **Menu dédié** dans la sidebar de planification
- **Formulaires intuitifs** avec validation en temps réel
- **Tableaux responsifs** avec pagination et filtres

## 🏗️ Architecture Technique

### Modèles de Données

#### `Schedule` (Emploi du temps)
```python
- name: Nom de l'emploi du temps
- description: Description optionnelle
- academic_year: Année académique
- level: Niveau d'études
- start_date / end_date: Période de validité
- duration_type: Type de durée (1 mois, 3 mois, 6 mois, 1 an, personnalisé)
- status: Statut (brouillon, actif, archivé)
- is_generated: Indique si généré automatiquement
```

#### `LecturerAvailability` (Disponibilité enseignant)
```python
- lecturer: Enseignant concerné
- time_slot: Créneau horaire
- academic_year: Année académique
- status: Statut (disponible, préféré, indisponible)
- start_date / end_date: Période spécifique (optionnel)
- notes: Notes additionnelles
```

#### `ScheduleSession` (Séance d'emploi du temps)
```python
- schedule: Emploi du temps parent
- course_session: Séance de cours liée
- week_number: Numéro de semaine
- is_recurring: Séance récurrente
```

### Services

#### `ScheduleGenerationService`
Service principal pour la génération automatique d'emplois du temps :
- **Préparation des données** : Récupération des créneaux, salles, disponibilités
- **Validation de faisabilité** : Vérification des contraintes
- **Génération des séances** : Algorithme d'attribution optimisé
- **Sauvegarde** : Création des séances et liaisons

## 🚀 Utilisation

### 1. Configuration Préalable

Avant de générer un emploi du temps, assurez-vous d'avoir :
- ✅ **Créneaux horaires** définis (Lundi à Vendredi)
- ✅ **Salles de classe** actives
- ✅ **Enseignants** enregistrés
- ✅ **Cours** configurés pour le niveau
- ✅ **Disponibilités enseignants** renseignées

### 2. Création d'un Emploi du Temps

1. **Accéder au menu** "Emplois du temps" → "Créer un emploi"
2. **Remplir les informations** :
   - Nom descriptif
   - Année académique et niveau
   - Dates de début et fin
   - Type de durée
3. **Enregistrer** en mode brouillon

### 3. Configuration des Disponibilités

1. **Accéder à** "Disponibilités enseignants"
2. **Ajouter une disponibilité** pour chaque enseignant :
   - Sélectionner l'enseignant et le créneau
   - Choisir le statut approprié
   - Ajouter des notes si nécessaire

### 4. Génération Automatique

1. **Accéder à** "Génération automatique"
2. **Sélectionner l'emploi du temps** à générer
3. **Choisir les cours** à inclure
4. **Configurer les paramètres** :
   - Nombre de séances par semaine
   - Maximum de séances par jour
   - Options avancées (privilégier le matin, éviter les séances consécutives)
5. **Lancer la génération**

### 5. Visualisation et Validation

1. **Consulter l'emploi du temps** généré
2. **Vérifier les séances** par semaine
3. **Ajuster manuellement** si nécessaire
4. **Activer l'emploi du temps** une fois validé

## 🔧 Configuration Avancée

### Paramètres de Génération

- **Sessions par semaine** : 1-10 (recommandé : 2-3)
- **Maximum par jour** : 1-8 (recommandé : 4-6)
- **Privilégier le matin** : Donne priorité aux créneaux matinaux
- **Éviter les séances consécutives** : Évite les cours du même type consécutifs

### Statuts de Disponibilité

- **🟢 Disponible** : L'enseignant peut être assigné
- **🔵 Préféré** : Priorité lors de la génération
- **🔴 Indisponible** : Exclusion du créneau

## 📊 Statistiques et Suivi

Le dashboard affiche :
- Nombre total d'emplois du temps
- Emplois du temps actifs
- Emplois du temps en brouillon
- Statistiques par emploi du temps (séances, cours, enseignants)

## 🧪 Tests

Le système inclut des tests complets :
- **Tests de modèles** : Validation, contraintes, méthodes
- **Tests de vues** : CRUD, permissions, formulaires
- **Tests de services** : Génération, algorithmes
- **Tests d'intégration** : Workflow complet

Pour exécuter les tests :
```bash
python manage.py test planification.tests.ScheduleModelTest
python manage.py test planification.tests.ScheduleViewsTest
python manage.py test planification.tests.ScheduleGenerationServiceTest
```

## 🔐 Sécurité et Permissions

- **Accès restreint** aux utilisateurs avec rôle `planning`
- **Validation côté serveur** pour tous les formulaires
- **Protection CSRF** sur toutes les actions
- **Contraintes de base de données** pour l'intégrité

## 🎨 Design et UX

- **Design neumorphism** cohérent
- **Interface responsive** (mobile, tablette, desktop)
- **Feedback utilisateur** avec messages de succès/erreur
- **Navigation intuitive** avec menu dédié
- **Aide contextuelle** sur chaque page

## 🚀 Prochaines Améliorations

- **Export PDF** des emplois du temps
- **Notifications** pour les changements
- **Gestion des conflits** avancée
- **Historique des modifications**
- **API REST** pour intégrations externes

## 📞 Support

Pour toute question ou problème :
1. Consulter cette documentation
2. Vérifier les logs d'erreur
3. Exécuter le script de test : `python test_schedule_functionality.py`
4. Contacter l'équipe de développement

---

**Version** : 1.0  
**Dernière mise à jour** : Décembre 2024  
**Développé pour** : YSEM - Système de Gestion Académique
