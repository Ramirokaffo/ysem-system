# Documents d'inscription obligatoires

## Résumé des modifications

Ce document décrit les modifications apportées pour implémenter les 4 champs de fichiers obligatoires dans le processus d'inscription.

## Nouveaux champs ajoutés

### 1. Preuve d'obtention du baccalauréat
- **Champ**: `preuve_baccalaureat`
- **Description**: Copie du document attestant la réussite du baccalauréat ou équivalent
- **Stockage**: `media/documents/inscription/baccalaureat/`

### 2. Photocopie certifiée de l'acte de naissance
- **Champ**: `acte_naissance`
- **Description**: Photocopie certifiée conforme de l'acte de naissance
- **Stockage**: `media/documents/inscription/acte_naissance/`

### 3. Relevé des notes du Baccalauréat
- **Champ**: `releve_notes_bac`
- **Description**: Photocopie certifiée conforme du relevé des notes du baccalauréat
- **Stockage**: `media/documents/inscription/releve_notes/`

### 4. Bulletins de la classe de terminale
- **Champ**: `bulletins_terminale`
- **Description**: Photocopie des bulletins de notes de la classe de terminale
- **Stockage**: `media/documents/inscription/bulletins/`

## Exigences techniques

### Formats acceptés
- PNG
- JPG/JPEG
- PDF

### Contraintes
- Taille maximale par fichier : **5 Mo**
- Documents doivent être **lisibles et de bonne qualité**
- **Tous les champs sont obligatoires**

### Note importante
Les originaux de ces documents seront demandés après l'inscription.

## Fichiers modifiés

### 1. Modèles (`students/models.py`)
- Ajout de 4 nouveaux champs `FileField` dans `StudentMetaData`
- Configuration des répertoires de stockage
- Ajout des textes d'aide

### 2. Formulaires (`main/forms.py`)
- Ajout des validateurs personnalisés `validate_file_size` et `validate_document_file`
- Modification de `InscriptionEtape4Form` pour remplacer les `BooleanField` par des `FileField`
- Mise à jour de `StudentMetaDataEditForm` pour inclure les nouveaux champs
- Ajout des messages d'aide et de validation

### 3. Vues (`main/views.py`)
- Modification des méthodes POST pour gérer `request.FILES`
- Gestion du stockage des fichiers dans la session
- Sauvegarde des fichiers lors de la création de `StudentMetaData`
- Nettoyage de la session après création

### 4. Templates
- **`inscription_externe/formulaire.html`**: Ajout de `enctype="multipart/form-data"`
- **`nouvelle_inscription.html`**: Ajout de `enctype="multipart/form-data"`
- Remplacement des checkboxes par des champs de fichiers avec validation
- Ajout d'une section d'information sur les exigences

### 5. Migration
- **`students/migrations/0015_studentmetadata_acte_naissance_and_more.py`**
- Ajout des 4 nouveaux champs FileField

## Structure des répertoires créés

```
media/
└── documents/
    └── inscription/
        ├── baccalaureat/
        ├── acte_naissance/
        ├── releve_notes/
        └── bulletins/
```

## Validation des fichiers

### Validateur de taille (`validate_file_size`)
- Vérifie que le fichier ne dépasse pas 5 Mo
- Lève une `ValidationError` si la taille est dépassée

### Validateur de document (`validate_document_file`)
- Combine la validation de taille et d'extension
- Vérifie les formats autorisés (PNG, JPG, JPEG, PDF)
- Messages d'erreur explicites

## Interface utilisateur

### Informations affichées
- Encadré d'information avec les exigences
- Champs de fichiers avec labels clairs
- Textes d'aide sous chaque champ
- Indication des champs obligatoires (*)
- Messages d'erreur en cas de problème

### Expérience utilisateur
- Validation côté client avec attribut `accept`
- Messages d'aide contextuels
- Validation côté serveur robuste
- Gestion des erreurs avec messages explicites

## Tests

Un script de test (`test_file_upload.py`) a été créé pour vérifier :
- ✓ Validation des fichiers (taille, type)
- ✓ Présence des champs dans les formulaires
- ✓ Présence des champs dans les modèles
- ✓ Configuration correcte des répertoires

## Utilisation

1. Les utilisateurs doivent maintenant uploader les 4 documents lors de l'inscription
2. Les fichiers sont validés automatiquement
3. Les documents sont stockés de manière organisée
4. Les administrateurs peuvent accéder aux documents via l'interface d'édition

## Sécurité

- Validation stricte des types de fichiers
- Limitation de la taille des fichiers
- Stockage dans des répertoires dédiés
- Validation côté serveur obligatoire
