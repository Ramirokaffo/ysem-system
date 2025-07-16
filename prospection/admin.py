from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ProspectionConfig, Agent, Campagne, Equipe, Prospect


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
    list_display = ['matricule', 'nom_complet', 'type_agent', 'statut', 'telephone', 'date_embauche']
    list_filter = ['type_agent', 'statut', 'date_embauche']
    search_fields = ['matricule', 'nom', 'prenom', 'telephone', 'email']
    ordering = ['nom', 'prenom']
    
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
    list_display = ['nom', 'campagne', 'chef_equipe', 'etablissement_cible', 'nombre_agents', 'objectif_prospects', 'prospects_collectes', 'taux_realisation_display']
    list_filter = ['campagne', 'date_assignation']
    search_fields = ['nom', 'campagne__nom', 'chef_equipe__nom', 'etablissement_cible__name']
    ordering = ['campagne', 'nom']
    filter_horizontal = ['agents']
    inlines = [ProspectInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'campagne', 'chef_equipe')
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
    
    def taux_realisation_display(self, obj):
        taux = obj.taux_realisation
        if taux >= 100:
            color = 'green'
        elif taux >= 75:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            taux
        )
    taux_realisation_display.short_description = 'Taux de réalisation'


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    """Administration des prospects"""
    list_display = ['nom_complet', 'telephone', 'equipe', 'agent_collecteur', 'etablissement_origine', 'date_collecte']
    list_filter = ['equipe__campagne', 'equipe', 'agent_collecteur', 'etablissement_origine', 'date_collecte']
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
