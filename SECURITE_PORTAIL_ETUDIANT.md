# Sécurité du Portail Étudiant YSEM

## Vue d'ensemble

Ce document décrit les mesures de sécurité mises en place pour protéger le portail étudiant et empêcher l'accès non autorisé aux zones d'administration.

## Mesures de Sécurité Implémentées

### 1. Séparation des Sessions

**Problème** : Éviter les conflits entre les sessions administrateur et étudiant.

**Solution** :
- Sessions complètement séparées pour les étudiants et les administrateurs
- Les étudiants utilisent `request.session['student_authenticated']`
- Les administrateurs utilisent le système d'authentification Django standard
- Middleware de nettoyage automatique des sessions en cas de conflit

### 2. Middleware de Sécurité

**Fichier** : `student_portal/middleware.py`

#### StudentPortalSecurityMiddleware
- **Fonction** : Bloque l'accès des étudiants aux URLs d'administration
- **URLs protégées** :
  - `/admin/` - Interface d'administration Django
  - `/auth/` - Authentification administrateur
  - `/scholar` - Dashboard scolarité
  - `/etudiants/` - Gestion des étudiants
  - `/documents/` - Gestion des documents
  - `/statistiques/` - Statistiques
  - `/parametres/` - Paramètres système
  - `/etudiant/` - Détails des étudiants
  - `/document/` - Actions sur les documents
  - `/inscription/` - Gestion des inscriptions
  - `/teach/` - Module enseignement

#### StudentSessionCleanupMiddleware
- **Fonction** : Nettoie automatiquement les sessions étudiants en cas de conflit
- **Déclenchement** : Quand un utilisateur Django est connecté ET qu'il y a une session étudiant active

### 3. Décorateurs de Protection

**Fichier** : `student_portal/decorators.py`

#### @admin_required
- Vérifie que l'utilisateur est un vrai administrateur
- Bloque les étudiants connectés au portail
- Redirige vers la connexion si non authentifié

#### @scholar_admin_required
- Vérifie que l'utilisateur est un responsable de scolarité
- Utilise `user.is_scholar_admin()`
- Protection renforcée pour les actions sensibles

#### @no_student_portal_access
- Bloque explicitement l'accès aux étudiants du portail
- Retourne une erreur 403 Forbidden

### 4. Protection des Vues Sensibles

**Vues protégées** :
- `generate_student_external_password` : Génération de mots de passe (décorateur @scholar_admin_required)
- Toutes les vues de gestion des étudiants
- Toutes les vues de gestion des documents
- Interface d'administration Django

### 5. Template Tags de Sécurité

**Fichier** : `student_portal/templatetags/security_tags.py`

#### Template Tags Disponibles
- `{% is_student_session %}` : Vérifie si c'est une session étudiant
- `{% is_admin_session %}` : Vérifie si c'est une session admin
- `{% show_security_warning %}` : Affiche des avertissements de sécurité

### 6. Pages d'Erreur Personnalisées

**Page 403** : `student_portal/templates/student_portal/403.html`
- Design cohérent avec le portail étudiant
- Messages d'erreur clairs
- Boutons de navigation appropriés selon le contexte

## Tests de Sécurité

### Script de Test Automatisé

**Fichier** : `test_security.py`

**Tests effectués** :
1. ✅ Accès aux URLs d'administration sans authentification
2. ✅ Connexion étudiant au portail
3. ✅ Tentative d'accès aux URLs d'administration avec session étudiant
4. ✅ Accès aux vues sensibles spécifiques
5. ✅ Vérification de l'accès au portail étudiant
6. ✅ Test de déconnexion et perte d'accès
7. ✅ Test de conflit de sessions admin/étudiant

### Résultats des Tests

Tous les tests passent avec succès :
- ✅ URLs d'administration correctement bloquées
- ✅ Redirections vers le dashboard étudiant
- ✅ Accès au portail étudiant préservé
- ✅ Déconnexion fonctionnelle
- ✅ Gestion des conflits de sessions

## Flux de Sécurité

### Connexion Étudiant
1. Étudiant accède à `/portail-etudiant/`
2. Saisie matricule + mot de passe
3. Vérification des identifiants
4. Création de session étudiant (`student_authenticated = True`)
5. Redirection vers dashboard étudiant

### Tentative d'Accès Admin par Étudiant
1. Étudiant connecté tente d'accéder à `/scholar`
2. Middleware `StudentPortalSecurityMiddleware` intercepte
3. Vérification de `request.session['student_authenticated']`
4. Blocage et redirection vers dashboard étudiant
5. Message d'erreur affiché

### Protection des Vues Sensibles
1. Accès à une vue protégée (ex: génération mot de passe)
2. Décorateur `@scholar_admin_required` vérifie :
   - Pas de session étudiant active
   - Utilisateur Django authentifié
   - Rôle de responsable de scolarité
3. Accès autorisé ou blocage selon les critères

## Recommandations de Sécurité

### Pour les Développeurs

1. **Toujours utiliser les décorateurs** sur les vues sensibles
2. **Tester régulièrement** avec le script `test_security.py`
3. **Vérifier les nouvelles URLs** ajoutées dans le middleware
4. **Utiliser les template tags** pour conditionner l'affichage

### Pour les Administrateurs

1. **Éviter les sessions mixtes** : Se déconnecter avant de changer de rôle
2. **Surveiller les logs** pour détecter les tentatives d'accès non autorisées
3. **Former les utilisateurs** sur les bonnes pratiques
4. **Tester périodiquement** l'accès avec des comptes étudiants

### Pour les Étudiants

1. **Utiliser uniquement le portail étudiant** (`/portail-etudiant/`)
2. **Se déconnecter après utilisation**
3. **Ne pas partager les identifiants**
4. **Signaler tout comportement anormal**

## Monitoring et Logs

### Événements à Surveiller

- Tentatives d'accès aux URLs d'administration par des étudiants
- Échecs de connexion répétés
- Sessions simultanées admin/étudiant
- Accès à des vues sensibles

### Logs Recommandés

```python
# Exemple de logging dans les vues sensibles
import logging
logger = logging.getLogger(__name__)

def sensitive_view(request):
    logger.info(f"Accès à vue sensible par {request.user} - Session: {request.session.session_key}")
```

## Maintenance

### Mise à Jour des Protections

1. **Nouvelles URLs** : Ajouter dans `forbidden_paths` du middleware
2. **Nouvelles vues** : Appliquer les décorateurs appropriés
3. **Tests** : Mettre à jour `test_security.py`
4. **Documentation** : Maintenir ce guide à jour

### Vérifications Périodiques

- [ ] Exécuter `python test_security.py` mensuellement
- [ ] Vérifier les logs d'accès
- [ ] Tester avec de nouveaux comptes étudiants
- [ ] Réviser les permissions des rôles

---

*Document de sécurité pour YSEM - Portail Étudiant*
*Dernière mise à jour : {{ "now"|date:"d/m/Y" }}*
