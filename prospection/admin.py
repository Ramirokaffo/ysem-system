from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import ProspectionConfig, Agent, Campagne, Equipe, Prospect, SeanceProspection


@admin.register(ProspectionConfig)
class ProspectionConfigAdmin(admin.ModelAdmin):
    """Administration de la configuration de prospection"""
    list_display = ['__str__', 'is_active', 'activation_date', 'last_modified', 'modified_by']
    fields = ['is_active', 'modified_by', 'notes']

    def has_add_permission(self, request):
        # Empêcher la création de multiples configurations
        return not ProspectionConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression de la configuration
        return False

    def save_model(self, request, obj, form, change):
        # Enregistrer qui a modifié la configuration
        obj.modified_by = request.user.username
        super().save_model(request, obj, form, change)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Administration des agents de prospection"""
    list_display = ['matricule', 'nom_complet', 'type_agent', 'statut', 'telephone', 'date_embauche', 'is_active']
    list_filter = ['type_agent', 'statut', 'date_embauche', 'is_active']
    search_fields = ['matricule', 'nom', 'prenom', 'telephone', 'email']
    ordering = ['nom', 'prenom']
    readonly_fields = ['last_login']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'telephone', 'email')
        }),
        ('Informations professionnelles', {
            'fields': ('type_agent', 'statut', 'date_embauche')
        }),
        ('Adresse', {
            'fields': ('adresse',),
            'classes': ('collapse',)
        }),
        ('Authentification', {
            'fields': ('password', 'last_login', 'is_active')
        }),
    )
    
    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom complet'


@admin.register(Campagne)
class CampagneAdmin(admin.ModelAdmin):
    """Administration des campagnes de prospection"""
    list_display = ['nom', 'annee_academique', 'date_debut', 'date_fin', 'statut', 'objectif_global', 'duree_jours']
    list_filter = ['statut', 'annee_academique', 'date_debut']
    search_fields = ['nom', 'description']
    ordering = ['-date_debut']
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'annee_academique')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Objectifs et statut', {
            'fields': ('objectif_global', 'statut')
        }),
    )
    
    def duree_jours(self, obj):
        return f"{obj.duree_jours} jours"
    duree_jours.short_description = 'Durée'


class ProspectInline(admin.TabularInline):
    """Inline pour afficher les prospects d'une équipe"""
    model = Prospect
    extra = 0
    fields = ['nom', 'prenom', 'telephone', 'agent_collecteur', 'date_collecte']
    readonly_fields = ['date_collecte']


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    """Administration des équipes de prospection"""
    list_display = ['nom', 'seance', 'campagne_display', 'chef_equipe', 'etablissement_cible', 'nombre_agents', 'objectif_prospects', 'prospects_collectes', 'taux_realisation_display']
    list_filter = ['seance__campagne', 'seance', 'date_assignation']
    search_fields = ['nom', 'seance__campagne__nom', 'chef_equipe__nom', 'etablissement_cible__name']
    ordering = ['seance', 'nom']
    filter_horizontal = ['agents']
    inlines = [ProspectInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'seance', 'chef_equipe')
        }),
        ('Assignation', {
            'fields': ('etablissement_cible', 'date_assignation')
        }),
        ('Agents', {
            'fields': ('agents',)
        }),
        ('Objectifs', {
            'fields': ('objectif_prospects',)
        }),
    )

    def campagne_display(self, obj):
        return obj.campagne.nom if obj.campagne else '-'
    campagne_display.short_description = 'Campagne'
    
    def taux_realisation_display(self, obj):
        taux = obj.taux_realisation
        if taux >= 100:
            color = 'green'
        elif taux >= 75:
            color = 'orange'
        else:
            color = 'red'
        return mark_safe(f'<span style="color: {color};">{taux:.1f}%</span>')
    taux_realisation_display.short_description = 'Taux de réalisation'


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    """Administration des prospects"""
    list_display = ['nom_complet', 'telephone', 'equipe', 'agent_collecteur', 'etablissement_origine', 'date_collecte']
    list_filter = ['equipe__seance__campagne', 'equipe', 'agent_collecteur', 'etablissement_origine', 'date_collecte']
    search_fields = ['nom', 'prenom', 'telephone', 'telephone_pere', 'telephone_mere']
    ordering = ['-date_collecte']
    date_hierarchy = 'date_collecte'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'telephone')
        }),
        ('Contacts familiaux', {
            'fields': ('telephone_pere', 'telephone_mere')
        }),
        ('Collecte', {
            'fields': ('equipe', 'agent_collecteur', 'etablissement_origine', 'date_collecte')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_collecte']


class EquipeInline(admin.TabularInline):
    """Inline pour afficher les équipes d'une séance"""
    model = Equipe
    extra = 0
    fields = ['nom', 'chef_equipe', 'etablissement_cible', 'nombre_agents', 'objectif_prospects']
    readonly_fields = ['nombre_agents']

    def nombre_agents(self, obj):
        return obj.nombre_agents
    nombre_agents.short_description = 'Nb agents'


@admin.register(SeanceProspection)
class SeanceProspectionAdmin(admin.ModelAdmin):
    """Administration des séances de prospection"""
    list_display = ['nom', 'campagne', 'date_seance', 'statut', 'nombre_equipes', 'nombre_agents_total', 'created_by', 'created_at']
    list_filter = ['statut', 'campagne', 'date_seance', 'created_by']
    search_fields = ['campagne__nom', 'date_seance']
    ordering = ['-date_seance']
    date_hierarchy = 'date_seance'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [EquipeInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('campagne', 'date_seance', 'statut')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Rendre certains champs en lecture seule selon le contexte"""
        readonly = list(self.readonly_fields)

        # Si c'est une modification et que la séance est terminée ou annulée
        if obj and obj.statut in ['terminee', 'annulee']:
            readonly.append('date_seance')

        return readonly

    def save_model(self, request, obj, form, change):
        """Enregistrer qui a créé la séance"""
        if not change:  # Nouvelle séance
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


