from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
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
    ]
    
    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    type_agent = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type d'agent")
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='actif', verbose_name="Statut")
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    
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
    campagne = models.ForeignKey(
        Campagne, 
        on_delete=models.CASCADE, 
        related_name='equipes',
        verbose_name="Campagne"
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
    objectif_prospects = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Objectif (nombre de prospects)"
    )
    date_assignation = models.DateField(default=timezone.now, verbose_name="Date d'assignation")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = "Équipe de prospection"
        verbose_name_plural = "Équipes de prospection"
        ordering = ['campagne', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.campagne.nom}"

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
    def prospects_collectes(self):
        """Retourne le nombre de prospects collectés par l'équipe"""
        return self.prospects.count()
    
    @property
    def taux_realisation(self):
        """Calcule le taux de réalisation de l'objectif"""
        if self.objectif_prospects == 0:
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
