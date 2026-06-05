from django import forms
from django.forms import inlineformset_factory

from academic.models import Course, Subject
from lecturers.models import Lecturer
from main.forms import RELATIONSHIP_CHOICES
from main.validators import validate_file_size, validate_phone_number

from .models import LecturerSubject


_INPUT = 'form-control'
_TEXTAREA = 'form-control form-textarea'


class ProfileStep1Form(forms.ModelForm):
    """Étape 1 — Informations personnelles de l'enseignant."""

    emergency_contact_relationship = forms.ChoiceField(
        choices=RELATIONSHIP_CHOICES,
        required=False,
        label="Contact d'urgence - Relation",
        widget=forms.Select(attrs={'class': _INPUT}),
    )

    class Meta:
        model = Lecturer
        fields = [
            'firstname', 'lastname', 'date_naiss', 'place_of_birth',
            'gender', 'nationality', 'marital_status', 'number_of_dependent_children',
            'phone_number', 'phone_number_2', 'address',
            'nic', 'niu',
            'has_health_problem', 'health_problem_description',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_email', 'emergency_contact_relationship',
            'photo',
        ]
        widgets = {
            'firstname': forms.TextInput(attrs={'class': _INPUT}),
            'lastname': forms.TextInput(attrs={'class': _INPUT}),
            'date_naiss': forms.DateInput(
                attrs={'class': _INPUT, 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'place_of_birth': forms.TextInput(attrs={'class': _INPUT}),
            'gender': forms.Select(attrs={'class': _INPUT}),
            'nationality': forms.TextInput(attrs={'class': _INPUT}),
            'marital_status': forms.Select(attrs={'class': _INPUT}),
            'number_of_dependent_children': forms.NumberInput(attrs={'class': _INPUT, 'min': 0}),
            'phone_number': forms.TextInput(attrs={'class': _INPUT}),
            'phone_number_2': forms.TextInput(attrs={'class': _INPUT}),
            'address': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 2}),
            'nic': forms.TextInput(attrs={'class': _INPUT}),
            'niu': forms.TextInput(attrs={'class': _INPUT}),
            'has_health_problem': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'health_problem_description': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 2}),
            'emergency_contact_name': forms.TextInput(attrs={'class': _INPUT}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': _INPUT}),
            'emergency_contact_email': forms.EmailInput(attrs={'class': _INPUT}),
            'photo': forms.FileInput(attrs={'class': _INPUT, 'accept': 'image/png,image/jpeg,image/jpg'}),
        }

    # Champs obligatoires pour valider l'étape (en plus des contraintes du modèle)
    REQUIRED_FIELDS = (
        'firstname', 'lastname', 'date_naiss', 'place_of_birth', 'gender',
        'nationality', 'phone_number', 'address', 'nic',
        'emergency_contact_name', 'emergency_contact_phone',
        'emergency_contact_relationship',
    )

    def __init__(self, *args, partial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partial = partial
        self.fields['photo'].validators.append(validate_file_size)
        for name in ('phone_number', 'phone_number_2', 'emergency_contact_phone'):
            self.fields[name].validators.append(validate_phone_number)
        if not partial:
            for name in self.REQUIRED_FIELDS:
                if name in self.fields:
                    self.fields[name].required = True

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('has_health_problem') and not cleaned.get('health_problem_description'):
            self.add_error(
                'health_problem_description',
                "Veuillez décrire le problème de santé indiqué."
            )
        return cleaned


class DiplomaStep2Form(forms.ModelForm):
    """Étape 2 — Plus haut diplôme + CV."""

    class Meta:
        model = Lecturer
        fields = ['highest_diploma_obtained', 'grade', 'cv']
        widgets = {
            'highest_diploma_obtained': forms.Select(attrs={'class': _INPUT}),
            'grade': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ex. : Assistant, Maître-assistant, …'}),
            'cv': forms.ClearableFileInput(attrs={'class': _INPUT, 'accept': '.pdf,.doc,.docx'}),
        }

    def __init__(self, *args, partial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partial = partial
        self.fields['cv'].validators.append(validate_file_size)
        if not partial:
            self.fields['highest_diploma_obtained'].required = True
            # Le CV n'est obligatoire que s'il n'a pas déjà été uploadé.
            if not (self.instance and self.instance.cv):
                self.fields['cv'].required = True


class LecturerSubjectForm(forms.ModelForm):
    class Meta:
        model = LecturerSubject
        fields = ['subject', 'practice_experience_years', 'teaching_experience_years', 'proof_document']
        widgets = {
            'subject': forms.Select(attrs={'class': _INPUT}),
            'practice_experience_years': forms.NumberInput(attrs={'class': _INPUT, 'min': 0}),
            'teaching_experience_years': forms.NumberInput(attrs={'class': _INPUT, 'min': 0}),
            'proof_document': forms.ClearableFileInput(attrs={'class': _INPUT, 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.order_by('name')
        self.fields['proof_document'].validators.append(validate_file_size)


LecturerSubjectFormSet = inlineformset_factory(
    parent_model=Lecturer,
    model=LecturerSubject,
    form=LecturerSubjectForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class AdminLecturerSubjectForm(LecturerSubjectForm):
    """Variante administrateur : permet en plus de modifier le statut de
    validation de la matière (validée / refusée) à tout moment."""

    class Meta(LecturerSubjectForm.Meta):
        fields = LecturerSubjectForm.Meta.fields + ['status']
        widgets = {
            **LecturerSubjectForm.Meta.widgets,
            'status': forms.Select(attrs={'class': _INPUT}),
        }


AdminLecturerSubjectFormSet = inlineformset_factory(
    parent_model=Lecturer,
    model=LecturerSubject,
    form=AdminLecturerSubjectForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class CourseSelectionForm(forms.Form):
    """Étape 4 — sélection des cours proposés (filtrés selon diplôme/expérience)."""

    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Cours que vous souhaitez enseigner",
    )

    def __init__(self, *args, eligible_courses=None, **kwargs):
        super().__init__(*args, **kwargs)
        if eligible_courses is not None:
            self.fields['courses'].queryset = eligible_courses

    def clean_courses(self):
        courses = self.cleaned_data.get('courses')
        if not courses:
            raise forms.ValidationError(
                "Veuillez sélectionner au moins un cours que vous souhaitez enseigner."
            )
        return courses
