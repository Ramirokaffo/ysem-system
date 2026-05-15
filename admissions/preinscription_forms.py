"""Formulaires du wizard de pré-inscription du portail d'admission.

Quatre étapes :
    1. Step1IdentificationForm — identité, coordonnées, résidence
    2. Step2FamilyForm — informations sur le père et la mère (pas de parrain)
    3. Step3CursusForm — programme, spécialités et cursus
       (couplé aux formsets SecondaryDiplomaPortalFormSet / UniversityLevelPortalFormSet)
    4. Step4DocumentsForm — pièces justificatives et attestation de véracité

Les widgets n'utilisent volontairement aucune classe ``form-control`` : le portail
d'admission applique son propre design (palette YSEM bleu) via les wrappers
``.form-field`` définis dans ``admissions.css``.
"""
from django import forms
from django.core.validators import RegexValidator
from django.forms import formset_factory

from academic.models import Level, Program, Speciality
from academic.document_requirements import (
    PROGRAM_DOCUMENT_FIELD_NAMES,
    PROGRAM_DOCUMENTS_BY_FIELD,
)
from main.forms import (
    MENTION_CHOICES,
    SECONDARY_DIPLOMA_CHOICES,
    UNIVERSITY_DIPLOMA_CHOICES,
    UNIVERSITY_LEVEL_CHOICES,
    validate_document_file,
)
from main.program_documents import (
    build_program_document_entries,
    get_required_program_document_field_names,
)
from schools.models import School, SecondaryDiploma, UniversityLevel


SEXE_CHOICES = [
    ('', 'Sélectionner'),
    ('M', 'Masculin'),
    ('F', 'Féminin'),
]

LANGUE_CHOICES = [
    ('', 'Sélectionner'),
    ('francais', 'Français'),
    ('anglais', 'Anglais'),
]

PHONE_VALIDATOR = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message="Le numéro doit être au format international, ex: +237 6XX XXX XXX.",
)


class _PartialMixin:
    """Permet de relâcher la contrainte ``required`` quand on sauvegarde un brouillon."""

    def __init__(self, *args, partial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partial = partial
        if partial:
            for field in self.fields.values():
                field.required = False


class Step1IdentificationForm(_PartialMixin, forms.Form):
    """Étape 1 — Identification du candidat."""

    nom = forms.CharField(max_length=100, label="Nom",
        widget=forms.TextInput(attrs={'placeholder': 'Nom de famille', 'autocomplete': 'family-name'}))
    prenom = forms.CharField(max_length=100, label="Prénom(s)",
        widget=forms.TextInput(attrs={'placeholder': 'Prénom(s)', 'autocomplete': 'given-name'}))
    date_naissance = forms.DateField(label="Date de naissance",
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'])
    sexe = forms.ChoiceField(choices=SEXE_CHOICES, label="Sexe")
    premiere_langue_officielle = forms.ChoiceField(
        choices=LANGUE_CHOICES, label="Première langue officielle", initial='francais')

    telephone = forms.CharField(
        max_length=17, label="Téléphone", validators=[PHONE_VALIDATOR],
        widget=forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX', 'autocomplete': 'tel'}))

    profile_photo = forms.ImageField(
        label="Photo de profil", required=False,
        widget=forms.FileInput(attrs={'accept': 'image/png,image/jpeg,image/jpg'}),
        help_text="Formats acceptés : PNG, JPG, JPEG.")

    # Localisation
    pays_origine = forms.CharField(max_length=100, label="Pays d'origine / nationalité",
        initial='Cameroun',
        widget=forms.TextInput(attrs={'placeholder': 'Cameroun'}))
    region_origine = forms.CharField(max_length=100, label="Région d'origine", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Région'}))
    departement_origine = forms.CharField(max_length=100, label="Département d'origine", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Département'}))
    arrondissement_origine = forms.CharField(max_length=100, label="Arrondissement d'origine", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Arrondissement'}))
    ville_residence = forms.CharField(max_length=100, label="Ville de résidence", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Résidence actuelle'}))
    quartier_residence = forms.CharField(max_length=100, label="Quartier de résidence", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Quartier'}))


class Step2FamilyForm(_PartialMixin, forms.Form):
    """Étape 2 — Informations familiales (sans parrain)."""

    # Père
    nom_pere = forms.CharField(max_length=100, label="Nom et prénom du père", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nom et prénom du père'}))
    profession_pere = forms.CharField(max_length=200, label="Profession du père", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Profession du père'}))
    telephone_pere = forms.CharField(max_length=17, label="Téléphone du père", required=False,
        widget=forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX'}))
    courriel_pere = forms.EmailField(label="Courriel du père", required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'email@exemple.com'}))
    ville_residence_pere = forms.CharField(max_length=100, label="Pays & ville de résidence du père", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Adresse de résidence'}))

    # Mère
    nom_mere = forms.CharField(max_length=100, label="Nom et prénom de la mère", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nom et prénom de la mère'}))
    profession_mere = forms.CharField(max_length=200, label="Profession de la mère", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Profession de la mère'}))
    telephone_mere = forms.CharField(max_length=17, label="Téléphone de la mère", required=False,
        widget=forms.TextInput(attrs={'placeholder': '+237 6XX XXX XXX'}))
    courriel_mere = forms.EmailField(label="Courriel de la mère", required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'email@exemple.com'}))
    ville_residence_mere = forms.CharField(max_length=100, label="Pays & ville de résidence de la mère", required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Adresse de résidence'}))



class SecondaryDiplomaPortalForm(forms.ModelForm):
    """Bloc duplicable du formset des diplômes du secondaire (Blue design)."""

    name = forms.ChoiceField(choices=SECONDARY_DIPLOMA_CHOICES, label='Diplôme')
    mention = forms.ChoiceField(choices=MENTION_CHOICES, label='Mention', required=False)
    school_existant = forms.ModelChoiceField(
        queryset=School.objects.none(),
        label="Établissement existant", required=False,
        empty_label="Saisir manuellement un établissement",
    )
    school_name = forms.CharField(
        max_length=200, label="Ou saisir un autre établissement", required=False,
        widget=forms.TextInput(attrs={'placeholder': "Nom de l'établissement"}))

    class Meta:
        model = SecondaryDiploma
        fields = ['name', 'serie', 'obtained_year', 'mention']
        widgets = {
            'serie': forms.TextInput(attrs={'placeholder': 'Ex: C, D, F2'}),
            'obtained_year': forms.NumberInput(attrs={'placeholder': '2023'}),
        }
        labels = {
            'name': 'Diplôme',
            'serie': 'Série / spécialité',
            'obtained_year': "Année d'obtention",
            'mention': 'Mention',
        }

    def __init__(self, *args, partial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partial = partial
        if partial:
            for field in self.fields.values():
                field.required = False
        self.fields['school_existant'].queryset = School.objects.filter(level='secondary').order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        school_existant = cleaned_data.get('school_existant')
        school_name = (cleaned_data.get('school_name') or '').strip()
        cleaned_data['school_name'] = school_existant.name if school_existant else school_name
        return cleaned_data


class UniversityLevelPortalForm(forms.ModelForm):
    """Bloc duplicable du formset des niveaux universitaires (Blue design)."""

    level_name = forms.ChoiceField(choices=UNIVERSITY_LEVEL_CHOICES, label='Niveau')
    diploma_name = forms.ChoiceField(choices=UNIVERSITY_DIPLOMA_CHOICES, label='Diplôme obtenu', required=False)
    university_existant = forms.ModelChoiceField(
        queryset=School.objects.none(),
        label="Université existante", required=False,
        empty_label="Saisir manuellement une université",
    )
    university_name = forms.CharField(
        max_length=200, label="Ou saisir une autre université", required=False,
        widget=forms.TextInput(attrs={'placeholder': "Nom de l'université"}))

    class Meta:
        model = UniversityLevel
        fields = ['level_name', 'diploma_name', 'speciality', 'academic_year']
        widgets = {
            'speciality': forms.TextInput(attrs={'placeholder': 'Spécialité'}),
            'academic_year': forms.TextInput(attrs={'placeholder': 'Ex: 2022/2023'}),
        }
        labels = {
            'level_name': 'Niveau',
            'diploma_name': 'Diplôme obtenu',
            'speciality': 'Spécialité',
            'academic_year': 'Année académique',
        }

    def __init__(self, *args, partial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.partial = partial
        if partial:
            for field in self.fields.values():
                field.required = False
        self.fields['university_existant'].queryset = School.objects.filter(level='higher').order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        university_existant = cleaned_data.get('university_existant')
        university_name = (cleaned_data.get('university_name') or '').strip()
        cleaned_data['university_name'] = university_existant.name if university_existant else university_name
        return cleaned_data


SecondaryDiplomaPortalFormSet = formset_factory(SecondaryDiplomaPortalForm, extra=0, can_delete=True)
UniversityLevelPortalFormSet = formset_factory(UniversityLevelPortalForm, extra=0, can_delete=True)



class Step3CursusForm(_PartialMixin, forms.Form):
    """Étape 3 — Programme, spécialités et cursus.

    Les formsets ``SecondaryDiplomaPortalFormSet`` et ``UniversityLevelPortalFormSet``
    sont gérés côté vue. Ce formulaire s'occupe :
      * du programme + des trois choix de spécialité (dynamique) ;
      * du niveau d'entrée souhaité.
    """

    programme = forms.ModelChoiceField(
        queryset=Program.objects.all().order_by('name'),
        label="Programme visé",
        empty_label="Sélectionner un programme",
    )
    niveau = forms.ModelChoiceField(
        queryset=Level.objects.all().order_by('name'),
        label="Niveau d'entrée souhaité",
        empty_label="Sélectionner un niveau",
        required=False,
    )

    specialite_souhaitee_1 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(), label="Spécialité souhaitée 1",
        empty_label="Sélectionner d'abord un programme", required=False)
    specialite_souhaitee_2 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(), label="Spécialité souhaitée 2 (optionnelle)",
        empty_label="Sélectionner d'abord un programme", required=False)
    specialite_souhaitee_3 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(), label="Spécialité souhaitée 3 (optionnelle)",
        empty_label="Sélectionner d'abord un programme", required=False)

    def __init__(self, *args, program=None, **kwargs):
        super().__init__(*args, **kwargs)
        selected_program = _resolve_program_value(self, program)
        self._wire_speciality_fields(selected_program)

    def _wire_speciality_fields(self, program):
        if program is None:
            queryset = Speciality.objects.all().order_by('name')
        else:
            queryset = Speciality.objects.filter(program=program).order_by('name')
        for index, field_name in enumerate([
            'specialite_souhaitee_1', 'specialite_souhaitee_2', 'specialite_souhaitee_3',
        ], start=1):
            self.fields[field_name].queryset = queryset
            self.fields[field_name].empty_label = (
                f"Sélectionner la spécialité #{index}" if index == 1
                else f"Spécialité #{index} (optionnelle)"
            )

    def clean(self):
        cleaned_data = super().clean()
        programme = cleaned_data.get('programme')
        selected = []
        for field_name in [
            'specialite_souhaitee_1', 'specialite_souhaitee_2', 'specialite_souhaitee_3',
        ]:
            specialite = cleaned_data.get(field_name)
            if not specialite:
                continue
            if programme and specialite.program_id != programme.id:
                self.add_error(field_name,
                    "La spécialité doit appartenir au programme choisi.")
                continue
            if specialite.pk in selected:
                self.add_error(field_name,
                    "Veuillez choisir une spécialité différente pour chaque choix.")
                continue
            selected.append(specialite.pk)
        return cleaned_data


def _resolve_program_value(form, program):
    """Récupère un :class:`Program` à partir d'un argument explicite ou des données du formulaire."""
    if isinstance(program, Program):
        return program
    program_value = None
    if form.data:
        program_value = form.data.get('programme')
    elif form.initial:
        program_value = form.initial.get('programme')
    if isinstance(program_value, Program):
        return program_value
    if program_value:
        try:
            return Program.objects.filter(pk=int(program_value)).first()
        except (TypeError, ValueError):
            return None
    return None


class Step4DocumentsForm(_PartialMixin, forms.Form):
    """Étape 4 — Pièces justificatives et attestation de véracité.

    Les champs documents sont construits dynamiquement en fonction du programme
    sélectionné à l'étape 3 (via ``program``). Le formulaire expose
    ``program_document_entries`` pour le rendu côté template (label, help_text,
    indicateur ``has_file`` / ``current_file_name``).
    """

    attestation_veracite = forms.BooleanField(
        label="J'atteste que les informations indiquées sont complètes, authentiques et exactes.",
        required=True,
    )

    def __init__(self, *args, program=None, metadata=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._metadata = metadata
        self._required_document_fields = set(
            get_required_program_document_field_names(program)
        )
        self._wire_document_fields(program)
        if self.partial:
            self.fields['attestation_veracite'].required = False

    def _wire_document_fields(self, program):
        for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
            definition = PROGRAM_DOCUMENTS_BY_FIELD[field_name]
            self.fields[field_name] = forms.FileField(
                label=definition['label'],
                help_text=definition['help_text'],
                validators=[validate_document_file],
                widget=forms.FileInput(attrs={'accept': '.png,.jpg,.jpeg,.pdf'}),
                required=False,
            )
        self.program_document_entries = [
            {**entry, 'field': self[entry['field_name']]}
            for entry in build_program_document_entries(
                program=program, metadata=self._metadata,
                force_optional=self.partial,
            )
            if entry['should_display']
        ]

    def clean(self):
        cleaned_data = super().clean()
        if self.partial:
            return cleaned_data
        # En soumission stricte, chaque document requis doit avoir été fourni
        # (téléversement courant ou fichier déjà enregistré dans la métadonnée).
        for field_name in self._required_document_fields:
            if field_name not in self.fields:
                continue
            uploaded = cleaned_data.get(field_name)
            existing = getattr(self._metadata, field_name, None) if self._metadata else None
            if not uploaded and not existing:
                self.add_error(
                    field_name,
                    "Ce document est obligatoire pour soumettre le dossier.",
                )
        return cleaned_data
