from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Agent, Campagne, Equipe, Prospect, SeanceProspection
from academic.models import AcademicYear
from schools.models import School


class AgentForm(forms.ModelForm):
    """Formulaire pour la création et modification des agents"""
    
    class Meta:
        model = Agent
        fields = ['matricule', 'nom', 'prenom', 'telephone', 'email', 'type_agent', 'statut', 'date_embauche', 'adresse']
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AGT001'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +237 6XX XXX XXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'type_agent': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
        }
    
    def clean_matricule(self):
        matricule = self.cleaned_data['matricule']
        if Agent.objects.filter(matricule=matricule).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ce matricule existe déjà.")
        return matricule


class CampagneForm(forms.ModelForm):
    """Formulaire pour la création et modification des campagnes"""
    
    class Meta:
        model = Campagne
        fields = ['nom', 'description', 'annee_academique', 'date_debut', 'date_fin', 'statut', 'objectif_global']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la campagne'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description de la campagne'}),
            'annee_academique': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'objectif_global': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Nombre de prospects à collecter'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        return cleaned_data


class EquipeForm(forms.ModelForm):
    """Formulaire pour la création et modification des équipes"""

    class Meta:
        model = Equipe
        fields = ['nom', 'seance', 'agents', 'chef_equipe', 'etablissement_cible', 'objectif_prospects', 'date_assignation']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom généré automatiquement', 'readonly': True}),
            'seance': forms.Select(attrs={'class': 'form-control'}),
            'agents': forms.CheckboxSelectMultiple(),
            'chef_equipe': forms.Select(attrs={'class': 'form-control'}),
            'etablissement_cible': forms.Select(attrs={'class': 'form-control'}),
            'objectif_prospects': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Nombre de prospects à collecter'}),
            'date_assignation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le champ nom non obligatoire
        self.fields['nom'].required = False

        # Rendre le champ séance non obligatoire
        self.fields['seance'].required = False

        # Filtrer les agents actifs seulement
        self.fields['agents'].queryset = Agent.objects.filter(statut='actif')
        self.fields['chef_equipe'].queryset = Agent.objects.filter(statut='actif')

        # Filtrer les séances des campagnes actives (derniers 30 jours)
        from django.utils import timezone
        from datetime import timedelta
        from .models import SeanceProspection

        date_limite = timezone.now().date() - timedelta(days=30)
        self.fields['seance'].queryset = SeanceProspection.objects.filter(
            campagne__statut__in=['planifiee', 'en_cours'],
            date_seance__gte=date_limite
        ).select_related('campagne').order_by('-date_seance')

        # Sélectionner automatiquement la séance du jour d'une campagne active si elle existe
        if not self.instance.pk:  # Seulement pour les nouvelles équipes
            aujourd_hui = timezone.now().date()
            seance_aujourd_hui = SeanceProspection.objects.filter(
                date_seance=aujourd_hui,
                campagne__statut__in=['planifiee', 'en_cours']
            ).first()
            if seance_aujourd_hui:
                self.fields['seance'].initial = seance_aujourd_hui

    def _generer_nom_equipe(self, chef_equipe, etablissement_cible):
        """Génère automatiquement le nom de l'équipe"""
        if chef_equipe and etablissement_cible:
            return f"Équipe {chef_equipe.nom_complet} - {etablissement_cible.name}"
        elif chef_equipe:
            return f"Équipe {chef_equipe.nom_complet}"
        else:
            return "Équipe sans chef"

    def clean(self):
        cleaned_data = super().clean()
        agents = cleaned_data.get('agents')
        chef_equipe = cleaned_data.get('chef_equipe')
        etablissement_cible = cleaned_data.get('etablissement_cible')

        # Générer automatiquement le nom de l'équipe
        if not cleaned_data.get('nom'):
            cleaned_data['nom'] = self._generer_nom_equipe(chef_equipe, etablissement_cible)

        if chef_equipe and agents and chef_equipe not in agents:
            raise ValidationError("Le chef d'équipe doit faire partie des agents sélectionnés.")

        if agents and agents.count() < 2:
            raise ValidationError("Une équipe doit avoir au moins 2 agents.")

        if agents and agents.count() > 4:
            raise ValidationError("Une équipe ne peut pas avoir plus de 4 agents.")

        return cleaned_data


class ProspectForm(forms.ModelForm):
    """Formulaire pour la création et modification des prospects"""
    
    class Meta:
        model = Prospect
        fields = ['nom', 'prenom', 'telephone', 'telephone_pere', 'telephone_mere', 'equipe', 'agent_collecteur', 'etablissement_origine', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +237 6XX XXX XXX'}),
            'telephone_pere': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone du père (optionnel)'}),
            'telephone_mere': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone de la mère (optionnel)'}),
            'equipe': forms.Select(attrs={'class': 'form-control'}),
            'agent_collecteur': forms.Select(attrs={'class': 'form-control'}),
            'etablissement_origine': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes sur le prospect'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les équipes des séances de campagnes actives
        self.fields['equipe'].queryset = Equipe.objects.filter(seance__campagne__statut__in=['planifiee', 'en_cours'])

        # Filtrer les agents actifs
        self.fields['agent_collecteur'].queryset = Agent.objects.filter(statut='actif')


class AgentSearchForm(forms.Form):
    """Formulaire de recherche pour les agents"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, prénom, matricule...'
        })
    )
    type_agent = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Agent.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Agent.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CampagneSearchForm(forms.Form):
    """Formulaire de recherche pour les campagnes"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        })
    )
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Campagne.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    annee_academique = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        empty_label="Toutes les années",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class EquipeSearchForm(forms.Form):
    """Formulaire de recherche pour les équipes"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom d\'équipe...'
        })
    )
    seance = forms.ModelChoiceField(
        queryset=SeanceProspection.objects.all(),
        required=False,
        empty_label="Toutes les séances",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les séances récentes (derniers 60 jours)
        from django.utils import timezone
        from datetime import timedelta

        date_limite = timezone.now().date() - timedelta(days=60)
        self.fields['seance'].queryset = SeanceProspection.objects.filter(
            date_seance__gte=date_limite
        ).select_related('campagne').order_by('-date_seance')


class ProspectSearchForm(forms.Form):
    """Formulaire de recherche pour les prospects"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, prénom, téléphone...'
        })
    )
    equipe = forms.ModelChoiceField(
        queryset=Equipe.objects.all(),
        required=False,
        empty_label="Toutes les équipes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    agent_collecteur = forms.ModelChoiceField(
        queryset=Agent.objects.filter(statut='actif'),
        required=False,
        empty_label="Tous les agents",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
