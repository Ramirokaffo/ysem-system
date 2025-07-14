from django import forms
from .models import Lecturer
from .models import Evaluation
from .models import TeachingMonitoring


#formulaire pour l'ajout des enseignants
class EnseignantForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = '__all__'
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naiss': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'lang': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
class EvaluationForm(forms.ModelForm):
    class Meta:
        # niveauChoices = [
        #     ('', 'Sélectionner'), ('', 'L1'), ('', 'L2'), ('', 'L3'), ('', 'M1'), ('', 'M2'),
        # ]
        # supportChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        # explicationtChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        # reponseChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        # tdChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        # projetChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        # difficulteChoices = [
        #     ('', 'Sélectionner'), ('', 'True'), ('', 'False'), 
        # ]
        model = Evaluation
        fields = '__all__'
        widgets = {
            'evaluationDat': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nom_et_prenom_etudiant': forms.TextInput(attrs={'class': 'form-control'}),
            'cycle': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'intitule_cours': forms.TextInput(attrs={'class': 'form-control'}),
            'support_cours_acessible': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'bonne_explication_cours': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'bonne_reponse_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'courseMethodology': forms.TextInput(attrs={'class': 'form-control'}),
            'donne_TD': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'donne_projet': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'difficulte_rencontree': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'quelles_difficultes_rencontrees': forms.TextInput(attrs={'class': 'form-control'}),
            'propositionEtudiants': forms.TextInput(attrs={'class': 'form-control'}),
            'observationSSAC': forms.TextInput(attrs={'class': 'form-control'}),
            'actionSSAC': forms.TextInput(attrs={'class': 'form-control'}),
        }

class Suivi_CoursForm(forms.ModelForm):
    class Meta:
        
        model = TeachingMonitoring
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'intitule_cours': forms.TextInput(attrs={'class': 'form-control'}),
            'cycle': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'totalChapterCount': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'chapitre_fait': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'contenu_seance_prevu': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'contenu_effectif_seance': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'taux_couverture_seance': forms.NumberInput(attrs={'class': 'form-number-input'} ),
            'travaux_preparatoires': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'groupWork': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'classWork': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'homeWork': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'pedagogicActivities': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'TDandTP': forms.CheckboxInput(attrs={'class': 'form-check-input'} ),
            'projet_fin_cours': forms.TextInput(attrs={'class': 'form-control'}),
            'association_pratique_aux_enseigements': forms.TextInput(attrs={'class': 'form-control'}),
            'observation': forms.TextInput(attrs={'class': 'form-control'}),
            'solution': forms.TextInput(attrs={'class': 'form-control'}),
            'generalObservation': forms.TextInput(attrs={'class': 'form-control'}),
        }







