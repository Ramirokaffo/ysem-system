from django import forms
from .models import Lecturer, Evaluation, TeachingMonitoring
from students.models import Student
from academic.models import Course, Level, AcademicYear


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
    """Formulaire pour l'ajout d'évaluations"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Définir l'année académique par défaut (année en cours)
        try:
            current_academic_year = AcademicYear.objects.filter(is_active=True).first()
            if current_academic_year:
                self.fields['academic_year'].initial = current_academic_year
        except:
            pass

        # Améliorer les querysets pour les relations
        self.fields['student'].queryset = Student.objects.filter(status='approved').order_by('lastname', 'firstname')
        self.fields['course'].queryset = Course.objects.all().order_by('label')
        self.fields['level'].queryset = Level.objects.all().order_by('name')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')

    class Meta:
        model = Evaluation
        fields = '__all__'
        widgets = {
            'evaluationDat': forms.DateInput(attrs={'type': 'date', 'class': 'form-control shadow-inset border-light bg-primary'}),
            'student': forms.Select(attrs={'class': 'form-control shadow-inset border-light bg-primary'}),
            'course': forms.Select(attrs={'class': 'form-control shadow-inset border-light bg-primary'}),
            'level': forms.Select(attrs={'class': 'form-control shadow-inset border-light bg-primary'}),
            'academic_year': forms.Select(attrs={'class': 'form-control shadow-inset border-light bg-primary'}),
            'courseMethodology': forms.TextInput(attrs={'class': 'form-control shadow-inset border-light bg-primary', 'placeholder': 'Méthodologie du cours'}),
            'quelles_difficultes_rencontrees': forms.Textarea(attrs={'class': 'form-control shadow-inset border-light bg-primary', 'rows': 3, 'placeholder': 'Décrivez les difficultés rencontrées'}),
            'propositionEtudiants': forms.Textarea(attrs={'class': 'form-control shadow-inset border-light bg-primary', 'rows': 3, 'placeholder': 'Propositions des étudiants'}),
            'observationSSAC': forms.Textarea(attrs={'class': 'form-control shadow-inset border-light bg-primary', 'rows': 3, 'placeholder': 'Observations SSAC'}),
            'actionSSAC': forms.Textarea(attrs={'class': 'form-control shadow-inset border-light bg-primary', 'rows': 3, 'placeholder': 'Actions SSAC'}),
            'support_cours_acessible': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
            'bonne_explication_cours': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
            'bonne_reponse_questions': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
            'donne_TD': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
            'donne_projet': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
            'difficulte_rencontree': forms.CheckboxInput(attrs={'class': 'form-check-input shadow-inset border-light'}),
        }

class Suivi_CoursForm(forms.ModelForm):
    class Meta:
        model = TeachingMonitoring
        fields = [
            'date', 'lecturer', 'course', 'level', 'academic_year',
            'totalChapterCount', 'chapitre_fait', 'contenu_seance_prevu',
            'contenu_effectif_seance', 'travaux_preparatoires', 'groupWork',
            'classWork', 'homeWork', 'pedagogicActivities', 'TDandTP',
            'projet_fin_cours', 'association_pratique_aux_enseigements',
            'observation', 'solution', 'generalObservation'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'type': 'date'
            }),
            'lecturer': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'totalChapterCount': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0',
                'placeholder': 'Nombre de chapitres prévus'
            }),
            'chapitre_fait': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0',
                'placeholder': 'Nombre de chapitres réalisés'
            }),
            'contenu_seance_prevu': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0',
                'placeholder': 'Contenu prévu'
            }),
            'contenu_effectif_seance': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0',
                'placeholder': 'Contenu effectif'
            }),
            'travaux_preparatoires': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'groupWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'classWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'homeWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'pedagogicActivities': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'TDandTP': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'projet_fin_cours': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 3,
                'placeholder': 'Décrivez le projet de fin de cours...'
            }),
            'association_pratique_aux_enseigements': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 3,
                'placeholder': 'Décrivez l\'association pratique...'
            }),
            'observation': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 4,
                'placeholder': 'Vos observations...'
            }),
            'solution': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 4,
                'placeholder': 'Solutions proposées...'
            }),
            'generalObservation': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 4,
                'placeholder': 'Observation générale...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir l'année académique active par défaut
        from academic.models import AcademicYear
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if active_year and not self.instance.pk:
            self.fields['academic_year'].initial = active_year

    def clean(self):
        cleaned_data = super().clean()
        chapitre_fait = cleaned_data.get('chapitre_fait')
        total_chapters = cleaned_data.get('totalChapterCount')
        contenu_effectif = cleaned_data.get('contenu_effectif_seance')
        contenu_prevu = cleaned_data.get('contenu_seance_prevu')

        # Validation des chapitres
        if chapitre_fait and total_chapters and chapitre_fait > total_chapters:
            raise forms.ValidationError(
                "Le nombre de chapitres faits ne peut pas être supérieur au nombre total de chapitres prévus."
            )

        # Validation du contenu des séances
        if contenu_effectif and contenu_prevu and contenu_effectif > contenu_prevu:
            raise forms.ValidationError(
                "Le contenu effectif ne peut pas être supérieur au contenu prévu."
            )

        return cleaned_data
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'type': 'date'
            }),
            'lecturer': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control shadow-inset border-light bg-primary'
            }),
            'totalChapterCount': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0'
            }),
            'chapitre_fait': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0'
            }),
            'contenu_seance_prevu': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0'
            }),
            'contenu_effectif_seance': forms.NumberInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'min': '0'
            }),
            'travaux_preparatoires': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'groupWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'classWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'homeWork': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'pedagogicActivities': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'TDandTP': forms.CheckboxInput(attrs={
                'class': 'form-check-input shadow-inset border-light'
            }),
            'projet_fin_cours': forms.TextInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'placeholder': 'Décrivez le projet de fin de cours'
            }),
            'association_pratique_aux_enseigements': forms.TextInput(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'placeholder': 'Association pratique aux enseignements'
            }),
            'observation': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 3,
                'placeholder': 'Observations générales'
            }),
            'solution': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 3,
                'placeholder': 'Solutions proposées'
            }),
            'generalObservation': forms.Textarea(attrs={
                'class': 'form-control shadow-inset border-light bg-primary',
                'rows': 3,
                'placeholder': 'Observation générale'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Définir l'année académique active par défaut
        from academic.models import AcademicYear
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if active_year:
            self.fields['academic_year'].initial = active_year

        # Améliorer les labels
        self.fields['lecturer'].label = "Enseignant"
        self.fields['course'].label = "Cours"
        self.fields['level'].label = "Niveau"
        self.fields['academic_year'].label = "Année académique"
        self.fields['totalChapterCount'].label = "Chapitres prévus"
        self.fields['chapitre_fait'].label = "Chapitres faits"
        self.fields['contenu_seance_prevu'].label = "Contenu séance prévu"
        self.fields['contenu_effectif_seance'].label = "Contenu effectif séance"







