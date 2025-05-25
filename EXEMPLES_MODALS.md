# Exemples d'utilisation des modals neumorphism

## Vue d'ensemble

Les modals utilisent le design neumorphism du template original et sont adaptés pour les besoins de l'application YSEM.

## Composants disponibles

### 1. Modal de confirmation (`modal_confirm.html`)

Pour les actions qui nécessitent une confirmation (suppression, déconnexion, etc.)

#### Paramètres :
- `modal_id` : ID unique du modal (requis)
- `modal_title` : Titre du modal (requis)
- `modal_message` : Message à afficher (requis)
- `confirm_text` : Texte du bouton de confirmation (défaut: "Confirmer")
- `cancel_text` : Texte du bouton d'annulation (défaut: "Annuler")
- `confirm_action` : Action JavaScript à exécuter (optionnel)
- `modal_icon` : Classe de l'icône (défaut: "fas fa-exclamation-triangle")

#### Exemple - Suppression d'un étudiant :
```html
<!-- Modal -->
{% include 'components/modal_confirm.html' with 
   modal_id="confirmDeleteStudent" 
   modal_title="Supprimer l'étudiant" 
   modal_message="Êtes-vous sûr de vouloir supprimer cet étudiant ? Cette action est irréversible." 
   confirm_text="Supprimer" 
   cancel_text="Annuler" 
   confirm_action="deleteStudent(123)" 
   modal_icon="fas fa-user-times" %}

<!-- Bouton déclencheur -->
<button class="btn btn-danger btn-sm" data-toggle="modal" data-target="#confirmDeleteStudent">
    <i class="fas fa-trash me-1"></i>
    Supprimer
</button>

<!-- JavaScript -->
<script>
function deleteStudent(studentId) {
    // Logique de suppression
    fetch(`/students/${studentId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
        }
    }).then(response => {
        if (response.ok) {
            location.reload();
        }
    });
}
</script>
```

### 2. Modal de notification (`modal_notification.html`)

Pour afficher des informations, succès, erreurs, etc.

#### Paramètres :
- `modal_id` : ID unique du modal (requis)
- `modal_title` : Titre du modal (requis)
- `modal_message` : Message à afficher (requis)
- `button_text` : Texte du bouton (défaut: "OK")
- `button_action` : Action JavaScript à exécuter (optionnel)
- `modal_icon` : Classe de l'icône (défaut: "fas fa-info-circle")

#### Exemple - Succès d'enregistrement :
```html
<!-- Modal -->
{% include 'components/modal_notification.html' with 
   modal_id="successModal" 
   modal_title="Enregistrement réussi" 
   modal_message="L'étudiant a été enregistré avec succès dans le système." 
   button_text="Continuer" 
   modal_icon="fas fa-check-circle" %}

<!-- Déclenchement via JavaScript -->
<script>
function showSuccessModal() {
    $('#successModal').modal('show');
}
</script>
```

## Exemples par contexte

### 📚 Page Étudiants

#### Suppression d'un étudiant
```html
{% include 'components/modal_confirm.html' with 
   modal_id="deleteStudentModal" 
   modal_title="Supprimer l'étudiant" 
   modal_message="Êtes-vous sûr de vouloir supprimer cet étudiant ? Toutes ses données seront perdues." 
   confirm_text="Supprimer définitivement" 
   cancel_text="Annuler" 
   confirm_action="deleteStudent()" 
   modal_icon="fas fa-user-times" %}
```

#### Archivage d'un étudiant
```html
{% include 'components/modal_confirm.html' with 
   modal_id="archiveStudentModal" 
   modal_title="Archiver l'étudiant" 
   modal_message="Voulez-vous archiver cet étudiant ? Il ne sera plus visible dans la liste active." 
   confirm_text="Archiver" 
   cancel_text="Annuler" 
   confirm_action="archiveStudent()" 
   modal_icon="fas fa-archive" %}
```

### 📄 Page Documents

#### Suppression d'un document
```html
{% include 'components/modal_confirm.html' with 
   modal_id="deleteDocumentModal" 
   modal_title="Supprimer le document" 
   modal_message="Êtes-vous sûr de vouloir supprimer ce document ? Cette action est irréversible." 
   confirm_text="Supprimer" 
   cancel_text="Annuler" 
   confirm_action="deleteDocument()" 
   modal_icon="fas fa-file-times" %}
```

#### Génération réussie
```html
{% include 'components/modal_notification.html' with 
   modal_id="documentGeneratedModal" 
   modal_title="Document généré" 
   modal_message="Le document a été généré avec succès. Vous pouvez le télécharger maintenant." 
   button_text="Télécharger" 
   button_action="downloadDocument()" 
   modal_icon="fas fa-download" %}
```

### ⚙️ Page Paramètres

#### Réinitialisation des paramètres
```html
{% include 'components/modal_confirm.html' with 
   modal_id="resetSettingsModal" 
   modal_title="Réinitialiser les paramètres" 
   modal_message="Êtes-vous sûr de vouloir réinitialiser tous les paramètres ? Cette action ne peut pas être annulée." 
   confirm_text="Réinitialiser" 
   cancel_text="Annuler" 
   confirm_action="resetSettings()" 
   modal_icon="fas fa-undo" %}
```

#### Sauvegarde réussie
```html
{% include 'components/modal_notification.html' with 
   modal_id="settingsSavedModal" 
   modal_title="Paramètres sauvegardés" 
   modal_message="Vos paramètres ont été sauvegardés avec succès." 
   button_text="OK" 
   modal_icon="fas fa-check-circle" %}
```

## Icônes recommandées par contexte

### Actions destructives
- `fas fa-trash` : Suppression générale
- `fas fa-user-times` : Suppression d'utilisateur
- `fas fa-file-times` : Suppression de fichier
- `fas fa-exclamation-triangle` : Avertissement général

### Actions d'archivage/modification
- `fas fa-archive` : Archivage
- `fas fa-edit` : Modification
- `fas fa-undo` : Annulation/Réinitialisation
- `fas fa-sync` : Synchronisation

### Notifications positives
- `fas fa-check-circle` : Succès
- `fas fa-download` : Téléchargement
- `fas fa-save` : Sauvegarde
- `fas fa-thumbs-up` : Approbation

### Notifications d'information
- `fas fa-info-circle` : Information générale
- `fas fa-bell` : Notification
- `fas fa-lightbulb` : Conseil/Astuce
- `fas fa-question-circle` : Question

### Notifications d'erreur
- `fas fa-times-circle` : Erreur
- `fas fa-exclamation-circle` : Avertissement
- `fas fa-ban` : Interdiction
- `fas fa-bug` : Problème technique

## Intégration avec Django

### Dans les vues
```python
from django.contrib import messages

def delete_student(request, student_id):
    if request.method == 'POST':
        # Logique de suppression
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        
        # Message de succès (sera affiché via les alerts)
        messages.success(request, 'L\'étudiant a été supprimé avec succès.')
        
        return redirect('students:list')
```

### Dans les templates
```html
<!-- Affichage des messages Django -->
{% include 'components/messages.html' %}

<!-- Modal pour confirmation -->
{% include 'components/modal_confirm.html' with ... %}
```

## Bonnes pratiques

### 1. Nommage des modals
- Utilisez des IDs descriptifs : `deleteStudentModal`, `confirmLogoutModal`
- Préfixez par l'action : `confirm`, `notify`, `alert`

### 2. Messages clairs
- Soyez explicite sur les conséquences
- Utilisez un langage simple et direct
- Mentionnez si l'action est irréversible

### 3. Icônes appropriées
- Choisissez des icônes qui correspondent au contexte
- Restez cohérent dans l'utilisation des icônes
- Utilisez Font Awesome pour la compatibilité

### 4. Actions JavaScript
- Gardez les fonctions simples
- Gérez les erreurs appropriément
- Fermez le modal après l'action

### 5. Accessibilité
- Utilisez les attributs ARIA appropriés
- Assurez-vous que les modals sont navigables au clavier
- Testez avec des lecteurs d'écran
