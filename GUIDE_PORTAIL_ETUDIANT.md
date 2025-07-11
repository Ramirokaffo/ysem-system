# Guide du Portail Étudiant YSEM

## Vue d'ensemble

Le portail étudiant YSEM permet aux étudiants de consulter en ligne leurs documents officiels et leurs statuts. Cette fonctionnalité offre un accès externe sécurisé, séparé du système d'administration principal.

## Fonctionnalités

### Pour les Étudiants

1. **Connexion sécurisée** avec matricule + mot de passe
2. **Consultation des documents officiels** (cartes d'étudiant, relevés de notes, diplômes, certificats)
3. **Visualisation des statuts** (disponible, retiré, perdu)
4. **Filtrage et recherche** par type, statut, année académique
5. **Interface responsive** avec design neumorphism

### Pour les Responsables de Scolarité

1. **Génération de mots de passe** pour les étudiants
2. **Réinitialisation de mots de passe** en cas d'oubli
3. **Gestion centralisée** depuis l'interface d'administration

## Accès au Portail

### URL d'accès
- **Page d'accueil** : `http://votre-domaine.com/`
- **Portail étudiant** : `http://votre-domaine.com/portail-etudiant/`

### Connexion étudiant
1. Aller sur la page d'accueil
2. Cliquer sur "Accès Étudiant"
3. Saisir le matricule et le mot de passe fourni par la scolarité
4. Cliquer sur "Se connecter"

## Guide d'utilisation pour les Responsables de Scolarité

### Génération d'un mot de passe pour un étudiant

1. Se connecter à l'interface d'administration
2. Aller dans "Étudiants" > "Liste des étudiants"
3. Cliquer sur le matricule de l'étudiant
4. Dans la page de détails, cliquer sur "Générer mot de passe externe"
5. Confirmer l'action
6. **Important** : Noter le mot de passe affiché et le communiquer à l'étudiant

### Réinitialisation d'un mot de passe

1. Suivre les mêmes étapes que pour la génération
2. Le bouton affichera "Réinitialiser mot de passe externe" si un mot de passe existe déjà
3. L'ancien mot de passe sera remplacé par le nouveau

## Guide d'utilisation pour les Étudiants

### Première connexion

1. Récupérer le mot de passe auprès du service scolarité
2. Aller sur le portail étudiant
3. Saisir votre matricule et le mot de passe reçu
4. Se connecter

### Consultation des documents

1. Une fois connecté, le tableau de bord affiche un résumé de vos documents
2. Cliquer sur "Consulter mes documents" pour voir la liste complète
3. Utiliser les filtres pour rechercher des documents spécifiques :
   - **Statut** : Disponible, Retiré, Perdu
   - **Type** : Carte d'étudiant, Relevé de notes, Diplôme, Certificat
   - **Année académique** : Filtrer par année

### Statuts des documents

- **Disponible** (vert) : Le document est prêt à être retiré
- **Retiré** (bleu) : Le document a été remis à l'étudiant
- **Perdu** (orange) : Le document a été déclaré perdu

## Sécurité

### Authentification
- Chaque étudiant a un mot de passe unique généré aléatoirement
- Les mots de passe sont hachés en base de données
- Session séparée du système d'administration

### Permissions
- Seuls les responsables de scolarité peuvent générer/réinitialiser les mots de passe
- Les étudiants ne peuvent voir que leurs propres documents
- Déconnexion automatique pour la sécurité

## Dépannage

### Problèmes de connexion

**"Matricule ou mot de passe incorrect"**
- Vérifier que le matricule est correct
- Vérifier que le mot de passe a été saisi correctement
- Contacter la scolarité si le problème persiste

**"Accès non configuré"**
- Le mot de passe n'a pas encore été généré
- Contacter la scolarité pour obtenir un mot de passe

### Problèmes d'affichage

**Aucun document affiché**
- Vérifier que des documents ont été créés pour l'étudiant
- Essayer de réinitialiser les filtres
- Contacter la scolarité si aucun document n'est visible

## Support Technique

Pour toute assistance technique ou problème d'accès :
1. Contacter le service scolarité
2. Fournir votre matricule
3. Décrire précisément le problème rencontré

## Notes pour les Développeurs

### Structure technique
- Application Django `student_portal`
- Authentification par session séparée
- Templates avec design neumorphism
- Tests automatisés inclus

### Commandes utiles
```bash
# Lancer les tests du portail
python test_student_portal.py

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

### URLs principales
- `/portail-etudiant/` : Page de connexion
- `/portail-etudiant/tableau-de-bord/` : Dashboard
- `/portail-etudiant/mes-documents/` : Liste des documents
- `/portail-etudiant/deconnexion/` : Déconnexion

---

*Guide créé pour YSEM - Système de Gestion Académique*
