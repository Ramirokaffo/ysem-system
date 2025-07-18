from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from academic.models import AcademicYear
from schools.models import School


class ProspectionConfig(models.Model):
    """
    Configuration globale du module de prospection
    """
    is_active = models.BooleanField(
        default=False,
        verbose_name="Prospection activée",
        help_text="Active ou désactive le module de prospection dans l'application"
    )
    activation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'activation"
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    modified_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modifié par"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Notes sur l'activation/désactivation"
    )

    class Meta:
        verbose_name = "Configuration Prospection"
        verbose_name_plural = "Configuration Prospection"

    def __str__(self):
        return f"Prospection {'Activée' if self.is_active else 'Désactivée'}"

    @classmethod
    def is_prospection_active(cls):
        """Méthode utilitaire pour vérifier si la prospection est active"""
        try:
            config = cls.objects.first()
            return config.is_active if config else False
        except:
            return False

    @classmethod
    def get_or_create_config(cls):
        """Récupère ou crée la configuration"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={'is_active': False}
        )
        return config

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule configuration
        self.pk = 1
        super().save(*args, **kwargs)


class Agent(models.Model):
    """
    Modèle pour les agents de prospection (internes ou externes)
    """
    TYPE_CHOICES = [
        ('interne', 'Interne'),
        ('externe', 'Externe'),
    ]
    
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
        ('pending', 'En attente d\'activation'),
    ]

    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(unique=True, verbose_name="Email")
    type_agent = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type d'agent")
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")

    # Champs d'authentification
    password = models.CharField(max_length=128, verbose_name="Mot de passe")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Dernière connexion")
    is_active = models.BooleanField(default=False, verbose_name="Compte activé")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Agent de prospection"
        verbose_name_plural = "Agents de prospection"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"

    def set_password(self, raw_password):
        """Définit le mot de passe de l'agent"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Vérifie le mot de passe de l'agent"""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # Auto-générer le matricule si non fourni
        if not self.matricule:
            # Générer un matricule basé sur l'année et un compteur
            year = timezone.now().year
            count = Agent.objects.filter(matricule__startswith=f"AG{year}").count() + 1
            self.matricule = f"AG{year}{count:04d}"
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        """Propriété pour la compatibilité avec le système d'auth Django"""
        return True

    @property
    def is_anonymous(self):
        """Propriété pour la compatibilité avec le système d'auth Django"""
        return False


class Campagne(models.Model):
    """
    Modèle pour les campagnes de prospection
    """
    STATUS_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('suspendue', 'Suspendue'),
    ]
    
    nom = models.CharField(max_length=200, verbose_name="Nom de la campagne")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    annee_academique = models.ForeignKey(
        AcademicYear, 
        on_delete=models.CASCADE, 
        verbose_name="Année académique"
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planifiee', verbose_name="Statut")
    objectif_global = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Objectif global (nombre de prospects)"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Campagne de prospection"
        verbose_name_plural = "Campagnes de prospection"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.nom} ({self.annee_academique})"
    
    @property
    def is_active(self):
        """Vérifie si la campagne est actuellement active"""
        today = timezone.now().date()
        return (self.statut == 'en_cours' and 
                self.date_debut <= today <= self.date_fin)
    
    @property
    def duree_jours(self):
        """Calcule la durée de la campagne en jours"""
        return (self.date_fin - self.date_debut).days + 1


class Equipe(models.Model):
    """
    Modèle pour les équipes de prospection
    """
    nom = models.CharField(max_length=100, blank=True, verbose_name="Nom de l'équipe")
    seance = models.ForeignKey(
        'SeanceProspection',
        on_delete=models.CASCADE,
        related_name='equipes',
        verbose_name="Séance"
    )
    agents = models.ManyToManyField(
        Agent, 
        related_name='equipes',
        verbose_name="Agents"
    )
    chef_equipe = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='equipes_dirigees',
        verbose_name="Chef d'équipe"
    )
    etablissement_cible = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Établissement cible"
    )
    zone_assignee = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Zone assignée"
    )
    objectif_prospects = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Objectif (nombre de prospects)",
        null=True,
        blank=True
    )
    objectif_equipe = models.PositiveIntegerField(
        default=0,
        verbose_name="Objectif de l'équipe"
    )
    date_assignation = models.DateField(default=timezone.now, verbose_name="Date d'assignation")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Équipe de prospection"
        verbose_name_plural = "Équipes de prospection"
        ordering = ['seance', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.seance.nom}"

    def save(self, *args, **kwargs):
        """Génère automatiquement le nom de l'équipe si non fourni"""
        if not self.nom:
            if self.chef_equipe and self.etablissement_cible:
                self.nom = f"Équipe {self.chef_equipe.nom_complet} - {self.etablissement_cible.name}"
            elif self.chef_equipe:
                self.nom = f"Équipe {self.chef_equipe.nom_complet}"
            else:
                self.nom = "Équipe sans chef"
        super().save(*args, **kwargs)

    @property
    def nombre_agents(self):
        """Retourne le nombre d'agents dans l'équipe"""
        return self.agents.count()

    @property
    def agents_actifs(self):
        """Retourne les agents actifs de l'équipe"""
        return self.agents.filter(is_active=True)

    def peut_ajouter_agent(self, agent):
        """Vérifie si un agent peut être ajouté à l'équipe"""
        if not agent.is_active:
            return False, "L'agent n'est pas actif"
        if agent in self.agents.all():
            return False, "L'agent fait déjà partie de cette équipe"
        if self.seance and not self.seance.peut_etre_modifiee:
            return False, "La séance ne peut plus être modifiée"
        return True, "OK"

    @property
    def campagne(self):
        """Accès à la campagne via la séance"""
        return self.seance.campagne if self.seance else None
    
    @property
    def prospects_collectes(self):
        """Retourne le nombre de prospects collectés par l'équipe"""
        return self.prospects.count()
    
    @property
    def taux_realisation(self):
        """Calcule le taux de réalisation de l'objectif"""
        if not self.objectif_prospects or self.objectif_prospects == 0:
            return 0
        return (self.prospects_collectes / self.objectif_prospects) * 100


class Prospect(models.Model):
    """
    Modèle pour les prospects collectés
    """
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    telephone_pere = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone du père")
    telephone_mere = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone de la mère")
    
    # Relations
    equipe = models.ForeignKey(
        Equipe, 
        on_delete=models.CASCADE, 
        related_name='prospects',
        verbose_name="Équipe"
    )
    agent_collecteur = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='prospects_collectes',
        verbose_name="Agent collecteur"
    )
    etablissement_origine = models.ForeignKey(
        School, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Établissement d'origine"
    )
    
    # Suivi
    date_collecte = models.DateTimeField(default=timezone.now, verbose_name="Date de collecte")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"
        ordering = ['-date_collecte']
        unique_together = ['telephone', 'equipe']  # Éviter les doublons dans la même équipe
    
    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.telephone}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"


class SeanceProspection(models.Model):
    """
    Modèle pour gérer les séances/journées de prospection
    Chaque séance est associée à une campagne
    """
    STATUS_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]

    campagne = models.ForeignKey(
        Campagne,
        on_delete=models.CASCADE,
        related_name='seances',
        verbose_name="Campagne",
        null=True,
        blank=True
    )
    date_seance = models.DateField(
        verbose_name="Date de la séance"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planifiee',
        verbose_name="Statut"
    )

    # Métadonnées
    created_by = models.ForeignKey(
        'accounts.BaseUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seances_creees',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    def __str__(self):
        return f"Séance du {self.date_seance.strftime('%d/%m/%Y')} - {self.campagne.nom}"

    @property
    def nom(self):
        """Nom automatique basé sur la date et la campagne"""
        return f"Séance du {self.date_seance.strftime('%d/%m/%Y')} - {self.campagne.nom}"

    @property
    def nombre_equipes(self):
        return self.equipes.count()

    @property
    def nombre_agents_total(self):
        return sum(equipe.agents.count() for equipe in self.equipes.all())

    @property
    def est_active(self):
        return self.statut == 'en_cours'

    @property
    def peut_etre_modifiee(self):
        return self.statut in ['planifiee']

    @classmethod
    def creer_seance_pour_campagne(cls, campagne, date_seance=None, created_by=None):
        """Créer une séance pour une campagne donnée"""
        from django.utils import timezone
        if date_seance is None:
            date_seance = timezone.now().date()

        seance, created = cls.objects.get_or_create(
            campagne=campagne,
            date_seance=date_seance,
            defaults={
                'created_by': created_by,
                'statut': 'planifiee'
            }
        )
        return seance, created

    @classmethod
    def creer_seance_aujourd_hui(cls, campagne, created_by=None):
        """Créer automatiquement la séance du jour pour une campagne"""
        from django.utils import timezone
        aujourd_hui = timezone.now().date()
        return cls.creer_seance_pour_campagne(campagne, aujourd_hui, created_by)

    class Meta:
        verbose_name = "Séance de prospection"
        verbose_name_plural = "Séances de prospection"
        ordering = ['-date_seance']
        unique_together = ['campagne', 'date_seance']  # Une seule séance par campagne par jour



