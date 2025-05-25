# Architecture Django YSEM

## Vue d'ensemble

Ce projet Django implémente un système de gestion académique. L'architecture est organisée en 4 applications Django distinctes pour une meilleure modularité et maintenabilité.

## Applications Django

### 1. **accounts** - Gestion des utilisateurs et authentification

**Modèles :**
- `BaseUser` : Extension du modèle User de Django avec des champs supplémentaires
  - **Informations personnelles :**
    - `phone_number` : Numéro de téléphone
    - `date_of_birth` : Date de naissance
    - `address` : Adresse
    - `gender` : Genre (Masculin/Féminin)
  - **Informations professionnelles (ex-Staff) :**
    - `role` : Rôle/fonction dans l'établissement
    - `method_type` : Type de méthode

- `Godfather` : Modèle pour les parrains/tuteurs
  - `user` : Relation OneToOne avec BaseUser
  - `firstname`, `lastname` : Nom et prénom
  - `occupation` : Profession
  - `phone_number`, `email` : Coordonnées

### 2. **academic** - Gestion académique

**Modèles :**
- `Speciality` : Spécialités académiques
- `Department` : Départements (liés aux spécialités)
- `Level` : Niveaux d'études
- `Course` : Cours (liés aux niveaux)
- `Program` : Programmes d'études
- `AcademicYear` : Années académiques

### 3. **students** - Gestion des étudiants

**Modèles :**
- `Student` : Modèle principal des étudiants
  - `matricule` : Clé primaire
  - Informations personnelles (nom, prénom, date de naissance, etc.)
  - Relations avec BaseUser, Godfather, StudentMetaData, School, Program

- `StudentLevel` : Association étudiants-niveaux
  - Relation many-to-many avec attributs supplémentaires

- `StudentMetaData` : Métadonnées des étudiants
  - Informations familiales et géographiques
  - Données sur l'origine et la résidence

### 4. **schools** - Gestion des établissements

**Modèles :**
- `School` : Établissements scolaires
- `UniversityLevel` : Niveaux universitaires
- `SecondaryDiploma` : Diplômes du secondaire



## Relations entre modèles

### Relations principales :
- **Student ↔ BaseUser** : OneToOne (optionnel)
- **Student ↔ Godfather** : ForeignKey (optionnel)
- **Student ↔ StudentMetaData** : OneToOne (optionnel)
- **Student ↔ School** : ForeignKey (optionnel)
- **Student ↔ Program** : ForeignKey (optionnel)
- **Student ↔ Level** : ManyToMany via StudentLevel
- **Department ↔ Speciality** : ForeignKey
- **Course ↔ Level** : ForeignKey

## Configuration

### Modèle User personnalisé
```python
AUTH_USER_MODEL = 'accounts.BaseUser'
```

### Applications installées
```python
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Applications personnalisées
    "accounts",
    "academic",
    "students",
    "schools",
]
```

## Interface d'administration

Chaque application dispose d'une interface d'administration Django configurée avec :
- Affichage en liste des champs principaux
- Filtres appropriés
- Recherche par champs pertinents
- Hiérarchie par date quand applicable

## Base de données

- **SGBD** : MySQL
- **Encodage** : UTF8MB4 avec collation unicode_ci
- **Migrations** : Toutes les migrations ont été appliquées avec succès

## Utilisation

1. **Démarrer le serveur** :
   ```bash
   python manage.py runserver
   ```

2. **Accéder à l'administration** :
   - URL : http://localhost:8000/admin/
   - Utilisateur : admin
   - Mot de passe : [défini lors de la création]

3. **Gérer les données** :
   - Créer des spécialités et départements
   - Ajouter des niveaux et cours
   - Enregistrer des écoles
   - Créer des étudiants avec leurs métadonnées
   - Gérer le personnel

## Avantages de cette architecture

1. **Modularité** : Chaque domaine métier est dans sa propre application
2. **Réutilisabilité** : Les applications peuvent être réutilisées dans d'autres projets
3. **Maintenabilité** : Code organisé et facile à maintenir
4. **Évolutivité** : Facile d'ajouter de nouvelles fonctionnalités
5. **Séparation des responsabilités** : Chaque application a un rôle bien défini
6. **Simplicité** : Intégration des propriétés du personnel dans BaseUser pour éviter la complexité inutile

## Prochaines étapes

1. Ajouter des vues et templates pour l'interface utilisateur
2. Implémenter l'API REST avec Django REST Framework
3. Ajouter des tests unitaires
4. Configurer la sécurité et les permissions
5. Optimiser les requêtes avec select_related/prefetch_related
