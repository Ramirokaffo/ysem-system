from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from students.forms import SchoolChoiceField
from students.models import Student, StudentMetaData, OfficialDocument, StudentLevel
from accounts.models import Godfather
from academic.models import Speciality, Program, Level, AcademicYear
from academic.document_requirements import (
    PROGRAM_DOCUMENT_FIELD_NAMES,
    PROGRAM_DOCUMENTS_BY_FIELD,
)
from schools.models import School, SecondaryDiploma, UniversityLevel
from .models import SystemSettings
from .program_documents import build_program_document_entries



def validate_file_size(value):
    """Validateur pour la taille des fichiers (max 5Mo)"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("La taille du fichier ne doit pas dépasser 5 Mo.")
    return value


def validate_document_file(value):
    """Validateur combiné pour les documents d'inscription"""
    # Vérifier la taille
    validate_file_size(value)

    # Vérifier l'extension
    allowed_extensions = ['png', 'jpg', 'jpeg', 'pdf']
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Type de fichier non autorisé. Formats acceptés : {', '.join(allowed_extensions).upper()}"
        )

    return value


class GodfatherChoiceField(forms.ModelChoiceField):
    """Champ de sélection des parrains avec libellé enrichi."""

    def label_from_instance(self, obj):
        parts = [obj.full_name]
        if obj.phone_number:
            parts.append(obj.phone_number)
        if obj.email:
            parts.append(obj.email)
        return " - ".join(parts)


RELATIONSHIP_CHOICES = [
    ('', 'Sélectionner un lien de parenté'),
    ('pere', 'Père'),
    ('mere', 'Mère'),
    ('frere', 'Frère'),
    ('soeur', 'Sœur'),
    ('oncle', 'Oncle'),
    ('tante', 'Tante'),
    ('cousin', 'Cousin'),
    ('cousine', 'Cousine'),
    ('tuteur', 'Tuteur'),
    ('tutrice', 'Tutrice'),
    ('grand_parent', 'Grand-parent'),
    ('autre', 'Autre'),
]

SECONDARY_DIPLOMA_CHOICES = [
    ('', 'Sélectionner un diplôme'),
    ('BEPC', 'BEPC'),
    ('CAP', 'CAP'),
    ('Probatoire', 'Probatoire'),
    ('Baccalauréat', 'Baccalauréat'),
    ('GCE O-Level', 'GCE O-Level'),
    ('GCE A-Level', 'GCE A-Level'),
    ('BT', 'BT'),
    ('Autre', 'Autre'),
]

MENTION_CHOICES = [
    ('', 'Sélectionner une mention'),
    ('Passable', 'Passable'),
    ('Assez bien', 'Assez bien'),
    ('Bien', 'Bien'),
    ('Très bien', 'Très bien'),
    ('Excellent', 'Excellent'),
]

UNIVERSITY_LEVEL_CHOICES = [
    ('', 'Sélectionner un niveau'),
    ('Niveau 1', 'Niveau 1'),
    ('Niveau 2', 'Niveau 2'),
    ('Niveau 3', 'Niveau 3'),
    ('Niveau 4', 'Niveau 4'),
    ('Niveau 5', 'Niveau 5'),
    ('Niveau 6', 'Niveau 6'),
    ('Niveau 7', 'Niveau 7'),
    ('Niveau 8', 'Niveau 8'),
]

UNIVERSITY_DIPLOMA_CHOICES = [
    ('', 'Sélectionner un diplôme obtenu'),
    ('BTS', 'BTS'),
    ('HND', 'HND'),
    ('DUT', 'DUT'),
    ('Licence', 'Licence'),
    ('Licence professionnelle', 'Licence professionnelle'),
    ('Master', 'Master'),
    ('Doctorat', 'Doctorat'),
    ('Certification', 'Certification'),
    ('Aucun diplome', 'Aucun diplôme'),
    ('Autres', 'Autres'),
]


class SecondaryDiplomaForm(forms.ModelForm):
    """Bloc duplicable pour les diplômes du secondaire."""

    name = forms.ChoiceField(
        choices=SECONDARY_DIPLOMA_CHOICES,
        label='Diplôme',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    mention = forms.ChoiceField(
        choices=MENTION_CHOICES,
        label='Mention',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    school_existant = SchoolChoiceField(
        queryset=School.objects.none(),
        label="Établissement existant",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Saisir manuellement un établissement",
        required=False,
    )
    school_name = forms.CharField(
        max_length=200,
        label="Ou saisir un autre établissement",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement',
        }),
        required=False,
    )

    class Meta:
        model = SecondaryDiploma
        fields = ['name', 'serie', 'obtained_year', 'mention']
        widgets = {
            'serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: C, D, F2',
            }),
            'obtained_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2023',
            }),
        }
        labels = {
            'name': 'Diplôme',
            'serie': 'Série / spécialité',
            'obtained_year': "Année d'obtention",
            'mention': 'Mention',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school_existant'].queryset = School.objects.filter(level='secondary').order_by('name', 'phone_number')

    def clean(self):
        cleaned_data = super().clean()
        school_existant = cleaned_data.get('school_existant')
        school_name = (cleaned_data.get('school_name') or '').strip()
        cleaned_data['school_name'] = school_existant.name if school_existant else school_name
        return cleaned_data


class UniversityLevelForm(forms.ModelForm):
    """Bloc duplicable pour le cursus universitaire."""

    level_name = forms.ChoiceField(
        choices=UNIVERSITY_LEVEL_CHOICES,
        label='Niveau',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    diploma_name = forms.ChoiceField(
        choices=UNIVERSITY_DIPLOMA_CHOICES,
        label='Diplôme obtenu',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    university_existant = SchoolChoiceField(
        queryset=School.objects.none(),
        label="Université existante",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Saisir manuellement une université",
        required=False,
    )
    university_name = forms.CharField(
        max_length=200,
        label="Ou saisir une autre université",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'université',
        }),
        required=False,
    )

    class Meta:
        model = UniversityLevel
        fields = ['level_name', 'diploma_name', 'speciality', 'academic_year']
        widgets = {
            'speciality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Spécialité',
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2022/2023',
            }),
        }
        labels = {
            'level_name': 'Niveau',
            'diploma_name': 'Diplôme obtenu',
            'speciality': 'Spécialité',
            'academic_year': 'Année académique',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['university_existant'].queryset = School.objects.filter(level='higher').order_by('name', 'phone_number')

    def clean(self):
        cleaned_data = super().clean()
        university_existant = cleaned_data.get('university_existant')
        university_name = (cleaned_data.get('university_name') or '').strip()
        cleaned_data['university_name'] = university_existant.name if university_existant else university_name
        return cleaned_data


SecondaryDiplomaFormSet = formset_factory(SecondaryDiplomaForm, extra=0, can_delete=True)
UniversityLevelFormSet = formset_factory(UniversityLevelForm, extra=0, can_delete=True)

class InscriptionCompleteForm(forms.Form):
    """Formulaire complet de pre-inscription combinant toutes les étapes nécessaires"""

    # === SECTION 1: INFORMATIONS PERSONNELLES (ex-étape 2) ===
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille'
        })
    )

    prenom = forms.CharField(
        max_length=100,
        label="Prénom(s)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom(s)'
        })
    )

    date_naissance = forms.DateField(
        label="Date de naissance",
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date',
            'aria-label': "Date with icon left",
            "placeholder": "Select date"
        })
    )

    lieu_naissance = forms.CharField(
        max_length=100,
        label="Lieu de naissance",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville de naissance'
        })
    )

    SEXE_CHOICES = [
        ('', 'Sélectionner'),
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    sexe = forms.ChoiceField(
        choices=SEXE_CHOICES,
        label="Sexe",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Coordonnées
    courriel = forms.EmailField(
        label="Courriel",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )

    telephone = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        })
    )

    LANGUE_CHOICES = [
        ('', 'Sélectionner'),
        ('francais', 'Français'),
        ('anglais', 'Anglais'),
    ]

    premiere_langue_officielle = forms.ChoiceField(
        choices=LANGUE_CHOICES,
        label="Première langue officielle",
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial="francais"
    )

    profile_photo = forms.ImageField(
        label="Photo de profil",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/png,image/jpeg,image/jpg'
        }),
        help_text="Formats acceptés : PNG, JPG, JPEG.",
        required=False
    )

    # Informations sur l'année académique et le niveau
    annee_academique = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Année académique",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner une année académique",
        initial=None
    )

    niveau = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        label="Niveau d'entrée",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner un niveau"
    )

    programme = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        label="Programme",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner un programme",
        required=False
    )


    # Localisation
    region_origine = forms.CharField(
        max_length=100,
        label="Région d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Région'
        }),
        required=False
    )

    departement_origine = forms.CharField(
        max_length=100,
        label="Département d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Département'
        }),
        required=False
    )

    arrondissement_origine = forms.CharField(
        max_length=100,
        label="Arrondissement d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Arrondissement'
        }),
        required=False
    )

    ville_residence = forms.CharField(
        max_length=100,
        label="Ville de résidence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Résidence actuelle'
        }),
        required=False
    )

    quartier_residence = forms.CharField(
        max_length=100,
        label="Quartier de résidence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quartier'
        }),
        required=False
    )

    pays_origine = forms.CharField(
        max_length=100,
        label="Pays d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cameroun'
        }),
        initial='Cameroun'
    )


    # === SECTION 2: INFORMATIONS FAMILIALES (ex-étape 3) ===
    # Informations du père
    nom_pere = forms.CharField(
        max_length=100,
        label="Nom et prénom du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom du père'
        }),
        required=False
    )

    profession_pere = forms.CharField(
        max_length=200,
        label="Profession du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession du père'
        }),
        required=False
    )

    telephone_pere = forms.CharField(
        max_length=17,
        label="Téléphone du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    ville_residence_pere = forms.CharField(
        max_length=100,
        label="Pays & Ville de résidence du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse de résidence'
        }),
        required=False
    )

    courriel_pere = forms.EmailField(
    label="Courriel du père",
    widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'email@exemple.com'
    }),
    required=False
    )

    # Informations de la mère
    nom_mere = forms.CharField(
        max_length=100,
        label="Nom et prénom de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom de la mère'
        }),
        required=False
    )

    profession_mere = forms.CharField(
        max_length=200,
        label="Profession de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession de la mère'
        }),
        required=False
    )

    telephone_mere = forms.CharField(
        max_length=17,
        label="Téléphone de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    ville_residence_mere = forms.CharField(
        max_length=100,
        label="Pays & Ville de résidence de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse de résidence'
        }),
        required=False
    )

    courriel_mere = forms.EmailField(
    label="Courriel de la mère",
    widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'email@exemple.com'
    }),
    required=False
    )

    # Informations du tuteur/parrain
    parrain_existant = GodfatherChoiceField(
        queryset=Godfather.objects.none(),
        label="Parrain/tuteur existant",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Saisir manuellement un nouveau tuteur/parrain",
        help_text="Choisissez un parrain déjà enregistré ou laissez vide pour une saisie manuelle.",
        required=False
    )

    nom_tuteur = forms.CharField(
        max_length=100,
        label="Nom et prénom du tuteur/parrain",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom du tuteur/parrain'
        }),
        required=False
    )

    profession_tuteur = forms.CharField(
        max_length=200,
        label="Profession du tuteur/parrain",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession du tuteur/parrain'
        }),
        required=False
    )

    telephone_tuteur = forms.CharField(
        max_length=17,
        label="Téléphone du tuteur/parrain",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    courriel_tuteur = forms.EmailField(
    label="Courriel du tuteur/parrain",
    widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'email@exemple.com'
    }),
    required=False
    )

    # Personne à contacter en cas d'urgence
    nom_urgence = forms.CharField(
        max_length=100,
        label="Personne à contacter en cas d'urgence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom'
        }),
        required=False
    )

    telephone_urgence = forms.CharField(
        max_length=17,
        label="Téléphone d'urgence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    lien_parente_urgence = forms.ChoiceField(
        choices=RELATIONSHIP_CHOICES,
        label="Lien de parenté",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    # Choix des spécialités (dynamique basé sur le programme sélectionné)
    specialite_souhaitee_1 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 1",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    specialite_souhaitee_2 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 2",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    specialite_souhaitee_3 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 3",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ordonner les choix
        self.fields['annee_academique'].queryset = AcademicYear.objects.all().order_by('-start_at')
        if self.fields['annee_academique'].initial is None:
            self.fields['annee_academique'].initial = AcademicYear.get_active_year()
        self.fields['niveau'].queryset = Level.objects.all().order_by('name')
        self.fields['programme'].queryset = Program.objects.all().order_by('name')
        self.fields['parrain_existant'].queryset = Godfather.objects.all().order_by('full_name', 'phone_number', 'email')

        for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
            if field_name not in self.fields:
                continue

            document_definition = PROGRAM_DOCUMENTS_BY_FIELD[field_name]
            self.fields[field_name].label = document_definition['label']
            self.fields[field_name].help_text = document_definition['help_text']

        # Si un programme est fourni dans les données initiales ou POST
        selected_program = None
        program_value = None
        if self.data:
            program_value = self.data.get('programme')
        elif self.initial:
            program_value = self.initial.get('programme')

        if isinstance(program_value, Program):
            selected_program = program_value
            program_id = program_value.pk
        else:
            program_id = program_value

        if program_id:
            try:
                # Convertir en entier et filtrer les spécialités par programme
                program_id = int(program_id)
                selected_program = Program.objects.filter(pk=program_id).first()
                specialities = Speciality.objects.filter(program_id=program_id).order_by('name')
                for index, field_name in enumerate([
                    'specialite_souhaitee_1',
                    'specialite_souhaitee_2',
                    'specialite_souhaitee_3',
                ], start=1):
                    self.fields[field_name].queryset = specialities
                    self.fields[field_name].widget.attrs.pop('disabled', None)
                    self.fields[field_name].empty_label = (
                        f"Sélectionner la spécialité #{index}" if index == 1
                        else f"Sélectionner la spécialité #{index} (optionnel)"
                    )
            except (ValueError, TypeError):
                # Si la conversion échoue, autoriser toutes les spécialités pour la validation
                for field_name in [
                    'specialite_souhaitee_1',
                    'specialite_souhaitee_2',
                    'specialite_souhaitee_3',
                ]:
                    self.fields[field_name].queryset = Speciality.objects.all().order_by('name')
                    self.fields[field_name].widget.attrs.pop('disabled', None)
        else:
            # Pas de programme sélectionné - autoriser toutes les spécialités pour éviter l'erreur de validation
            for field_name in [
                'specialite_souhaitee_1',
                'specialite_souhaitee_2',
                'specialite_souhaitee_3',
            ]:
                self.fields[field_name].queryset = Speciality.objects.all().order_by('name')

        # Ajouter une note d'information pour les documents
        self.document_info = {
            'title': 'IMPORTANT - Documents requis',
            'requirements': [
                'Tous les documents doivent être lisibles et de bonne qualité',
                'Taille maximale par fichier : 5 Mo',
                'Formats acceptés uniquement : PNG, JPG, PDF',
                # 'Les originaux de ces documents seront demandés après l\'inscription'
            ]
        }
        self.program_document_entries = [
            {
                **document_entry,
                'field': self[document_entry['field_name']],
            }
            for document_entry in build_program_document_entries(
                program=selected_program,
                force_optional=True,
            )
        ]

    # === SECTION 4: DOCUMENTS REQUIS ===
    # Documents obligatoires
    acte_naissance = forms.FileField(
        label="Acte de naissance",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Acte de naissance légalisé. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    certificat_nationalite = forms.FileField(
        label="Certificat de nationalité",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Certificat de nationalité. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    preuve_baccalaureat = forms.FileField(
        label="Preuve du baccalauréat",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Ex: Photocopie légalisée du diplôme du Baccalauréat. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    releve_notes_last_class = forms.FileField(
        label="Relevé de notes de la dernière classe fréquentée",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie du relevé de notes de la dernière classe fréquentée. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    justificatif_dernier_diplome = forms.FileField(
        label="Justificatif du dernier diplôme obtenu",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie du justificatif du dernier diplôme obtenu. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    decharge_equivalence = forms.FileField(
        label="Décharge de la demande d'équivalence",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie de la décharge de la demande d'équivalence. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo.",
        required=False
    )

    bulletins_terminale = forms.FileField(
        label="Photocopie des bulletins de la classe de terminale",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie des bulletins de notes de la classe de terminale. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=False
    )

    releve_notes_master1 = forms.FileField(
        label="Relevé de notes du Master 1",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Relevé de notes du Master 1. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo.",
        required=False
    )

    photocopie_bts_hnd = forms.FileField(
        label="Photocopie du BTS ou HND",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie du BTS, HND ou diplôme équivalent. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo.",
        required=False
    )

    # Documents optionnels
    photos_identite = forms.BooleanField(
        label="4 photos 4 x 4 - Couleur",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    frais_etude_dossier = forms.BooleanField(
        label="Frais d'étude de dossier : 20 000 Fcfa",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    is_complete = forms.BooleanField(
        label="Dossier complet",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        initial=False
    )

    # Attestation
    attestation_veracite = forms.BooleanField(
        label="J'atteste que les informations indiquées ci-dessus sont complètes, authentiques et exactes.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    def clean(self):
        """Validation personnalisée du formulaire"""
        cleaned_data = super().clean()
        programme = cleaned_data.get('programme')
        selected_specialities = []

        for field_name in [
            'specialite_souhaitee_1',
            'specialite_souhaitee_2',
            'specialite_souhaitee_3',
        ]:
            specialite = cleaned_data.get(field_name)

            if programme and specialite and specialite.program_id != programme.id:
                self.add_error(
                    field_name,
                    "La spécialité sélectionnée doit appartenir au programme choisi."
                )
                continue

            if not specialite:
                continue

            if specialite.pk in selected_specialities:
                self.add_error(field_name, "Veuillez choisir une spécialité différente pour chaque choix.")
                continue

            selected_specialities.append(specialite.pk)

        return cleaned_data


class InscriptionEtape2Form(forms.Form):
    """Formulaire pour l'étape 2 : Identification du candidat"""

    # Informations personnelles
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille'
        })
    )

    prenom = forms.CharField(
        max_length=100,
        label="Prénom(s)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom(s)'
        })
    )

    date_naissance = forms.DateField(
        label="Date de naissance",
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date',
            'aria-label':"Date with icon left",
             "placeholder": "Select date"
        })
    )

    lieu_naissance = forms.CharField(
        max_length=100,
        label="Lieu de naissance",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville de naissance'
        })
    )

    SEXE_CHOICES = [
        ('', 'Sélectionner'),
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    sexe = forms.ChoiceField(
        choices=SEXE_CHOICES,
        label="Sexe",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Coordonnées
    courriel = forms.EmailField(
        label="Courriel",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )

    telephone = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        })
    )

    nationalite = forms.CharField(
        max_length=100,
        label="Nationalité",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nationalité'
        })
    )

    LANGUE_CHOICES = [
        ('', 'Sélectionner'),
        ('francais', 'Français'),
        ('anglais', 'Anglais'),
    ]

    premiere_langue_officielle = forms.ChoiceField(
        choices=LANGUE_CHOICES,
        label="Première langue officielle",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Localisation
    region_origine = forms.CharField(
        max_length=100,
        label="Région d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Région'
        })
    )

    departement_origine = forms.CharField(
        max_length=100,
        label="Département d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Département'
        })
    )

    arrondissement_origine = forms.CharField(
        max_length=100,
        label="Arrondissement d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Arrondissement'
        })
    )

    ville_residence = forms.CharField(
        max_length=100,
        label="Ville de résidence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Résidence actuelle'
        })
    )

    quartier_residence = forms.CharField(
        max_length=100,
        label="Quartier de résidence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quartier'
        }),
        required=False
    )

    pays_origine = forms.CharField(
        max_length=100,
        label="Pays d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cameroun'
        }),
        initial='Cameroun'
    )

    # Situation personnelle
    SITUATION_CHOICES = [
        ('', 'Sélectionner'),
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
    ]

    situation_matrimoniale = forms.ChoiceField(
        choices=SITUATION_CHOICES,
        label="Situation matrimoniale",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    profession_actuelle = forms.CharField(
        max_length=200,
        label="Profession actuelle",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession'
        }),
        required=False
    )


class InscriptionEtape3Form(forms.Form):
    """Formulaire pour l'étape 3 : Informations familiales"""

    # Informations du père
    nom_pere = forms.CharField(
        max_length=100,
        label="Nom et prénom du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom du père'
        }),
        required=False
    )

    profession_pere = forms.CharField(
        max_length=200,
        label="Profession du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession du père'
        }),
        required=False
    )

    telephone_pere = forms.CharField(
        max_length=17,
        label="Téléphone du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    courriel_pere = forms.EmailField(
        label="Courriel du père",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        }),
        required=False
    )

    ville_residence_pere = forms.CharField(
        max_length=100,
        label="Ville de résidence du père",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville de résidence'
        }),
        required=False
    )

    # Informations de la mère
    nom_mere = forms.CharField(
        max_length=100,
        label="Nom de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom de la mère'
        }),
        required=False
    )

    profession_mere = forms.CharField(
        max_length=200,
        label="Profession de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession de la mère'
        }),
        required=False
    )

    telephone_mere = forms.CharField(
        max_length=17,
        label="Téléphone de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    courriel_mere = forms.EmailField(
        label="Courriel de la mère",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        }),
        required=False
    )

    ville_residence_mere = forms.CharField(
        max_length=100,
        label="Ville de résidence de la mère",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville de résidence'
        }),
        required=False
    )

    # Informations du tuteur/parrain
    nom_tuteur = forms.CharField(
        max_length=100,
        label="Nom du Tuteur ou parrain",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom du tuteur/parrain'
        }),
        required=False
    )

    profession_tuteur = forms.CharField(
        max_length=200,
        label="Profession du tuteur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession du tuteur'
        }),
        required=False
    )

    telephone_tuteur = forms.CharField(
        max_length=17,
        label="Téléphone du tuteur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
        }),
        required=False
    )

    courriel_tuteur = forms.EmailField(
        label="Courriel du tuteur",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        }),
        required=False
    )


class InscriptionEtape4Form(forms.Form):
    """Formulaire pour l'étape 4 : Cursus scolaire et universitaire + Choix de spécialité"""

    # Cursus scolaire
    bepc_cap_serie = forms.CharField(
        max_length=50,
        label="BEPC / CAP - Série / spécialité",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Série'
        }),
        required=False
    )

    bepc_cap_annee = forms.IntegerField(
        label="BEPC / CAP - Année d'obtention",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2020'
        }),
        required=False
    )

    bepc_cap_mention = forms.CharField(
        max_length=50,
        label="BEPC / CAP - Mention",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mention'
        }),
        required=False
    )

    bepc_cap_etablissement = forms.CharField(
        max_length=200,
        label="BEPC / CAP - Établissement fréquenté",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    probatoire_serie = forms.CharField(
        max_length=50,
        label="Probatoire - Série / spécialité",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Série'
        }),
        required=False
    )

    probatoire_annee = forms.IntegerField(
        label="Probatoire - Année d'obtention",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2020'
        }),
        required=False
    )

    probatoire_mention = forms.CharField(
        max_length=50,
        label="Probatoire - Mention",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mention'
        }),
        required=False
    )

    probatoire_etablissement = forms.CharField(
        max_length=200,
        label="Probatoire - Établissement fréquenté",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    baccalaureat_serie = forms.CharField(
        max_length=50,
        label="Baccalauréat - Série",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Série'
        }),
        required=False
    )

    baccalaureat_annee = forms.IntegerField(
        label="Baccalauréat - Année d'obtention",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2020'
        }),
        required=False
    )

    baccalaureat_mention = forms.CharField(
        max_length=50,
        label="Baccalauréat - Mention",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mention'
        }),
        required=False
    )

    baccalaureat_etablissement = forms.CharField(
        max_length=200,
        label="Baccalauréat - Établissement fréquenté",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    centre_examen = forms.CharField(
        max_length=200,
        label="Centre d'examen",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Centre d\'examen'
        }),
        required=False
    )

    # Cursus universitaire
    diplome_niveau_1 = forms.CharField(
        max_length=200,
        label="Diplôme ou niveau d'étude 1",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Diplôme ou niveau'
        }),
        required=False
    )

    specialite_1 = forms.CharField(
        max_length=200,
        label="Spécialité 1",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Spécialité'
        }),
        required=False
    )

    etablissement_1 = forms.CharField(
        max_length=200,
        label="Établissement 1",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    annee_academique_1 = forms.CharField(
        max_length=20,
        label="Année Académique 1",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '20__/20__'
        }),
        required=False
    )

    diplome_niveau_2 = forms.CharField(
        max_length=200,
        label="Diplôme ou niveau d'étude 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Diplôme ou niveau'
        }),
        required=False
    )

    specialite_2 = forms.CharField(
        max_length=200,
        label="Spécialité 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Spécialité'
        }),
        required=False
    )

    etablissement_2 = forms.CharField(
        max_length=200,
        label="Établissement 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    annee_academique_2 = forms.CharField(
        max_length=20,
        label="Année Académique 2",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '20__/20__'
        }),
        required=False
    )

    # Choix de programme (ajouté pour permettre la sélection dynamique)
    programme = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        label="Programme",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner un programme"
    )

    # Choix de spécialité (dynamique basé sur le programme sélectionné)
    specialite_choisie_1 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),  # Vide par défaut
        label="Première spécialité choisie",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True  # Désactivé par défaut jusqu'à ce qu'un programme soit sélectionné
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    specialite_choisie_2 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),  # Vide par défaut
        label="Deuxième spécialité choisie",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True  # Désactivé par défaut jusqu'à ce qu'un programme soit sélectionné
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    # Constitution du dossier - Documents obligatoires
    preuve_baccalaureat = forms.FileField(
        label="Preuve d'obtention du Baccalauréat ou tout autre document équivalent",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Copie du document attestant la réussite du baccalauréat ou équivalent. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    acte_naissance = forms.FileField(
        label="Photocopie certifiée de l'acte de naissance",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie certifiée conforme de l'acte de naissance. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    releve_notes_last_class = forms.FileField(
        label="Photocopie certifiée du relevé des notes de la dernière classe fréquentée",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie certifiée conforme du relevé des notes de la dernière classe fréquentée. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    justificatif_dernier_diplome = forms.FileField(
        label="Photocopie certifiée du justificatif du dernier diplôme obtenu",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie certifiée conforme du justificatif du dernier diplôme obtenu. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    bulletins_terminale = forms.FileField(
        label="Photocopie des bulletins de la classe de terminale",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie des bulletins de notes de la classe de terminale. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    photos_identite = forms.BooleanField(
        label="4 photos 4 x 4 - Couleur",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    frais_etude_dossier = forms.BooleanField(
        label="Frais d'étude de dossier : 20 000 Fcfa",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    # Attestation
    attestation_veracite = forms.BooleanField(
        label="J'atteste que les informations indiquées ci-dessus sont complètes, authentiques et exactes.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si un programme est fourni dans les données initiales ou POST
        program_id = None
        if self.data:
            program_id = self.data.get('programme')
        elif self.initial:
            program_id = self.initial.get('programme')

        if program_id:
            try:
                # Filtrer les spécialités par programme
                self.fields['specialite_choisie_1'].queryset = Speciality.objects.filter(program_id=program_id)
                # Supprimer l'attribut 'disabled' (ne pas le mettre à False, car Django le rendrait quand même)
                self.fields['specialite_choisie_1'].widget.attrs.pop('disabled', None)
                self.fields['specialite_choisie_1'].empty_label = "Sélectionner une spécialité"

                self.fields['specialite_choisie_2'].queryset = Speciality.objects.filter(program_id=program_id)
                self.fields['specialite_choisie_2'].widget.attrs.pop('disabled', None)
                self.fields['specialite_choisie_2'].empty_label = "Sélectionner une spécialité (optionnel)"
            except (ValueError, TypeError):
                # Si la conversion échoue, autoriser toutes les spécialités pour la validation
                self.fields['specialite_choisie_1'].queryset = Speciality.objects.all()
                self.fields['specialite_choisie_1'].widget.attrs.pop('disabled', None)
                self.fields['specialite_choisie_2'].queryset = Speciality.objects.all()
                self.fields['specialite_choisie_2'].widget.attrs.pop('disabled', None)
        else:
            # Pas de programme sélectionné - autoriser toutes les spécialités pour éviter l'erreur de validation
            self.fields['specialite_choisie_1'].queryset = Speciality.objects.all()
            self.fields['specialite_choisie_2'].queryset = Speciality.objects.all()

        # Ajouter une note d'information pour les documents
        self.document_info = {
            'title': 'IMPORTANT - Documents requis',
            'requirements': [
                'Tous les documents doivent être lisibles et de bonne qualité',
                'Taille maximale par fichier : 5 Mo',
                'Formats acceptés uniquement : PNG, JPG, PDF',
                'Les originaux de ces documents seront demandés après l\'inscription'
            ]
        }


# class StudentEditForm(forms.ModelForm):
#     """Formulaire de modification des informations principales de l'étudiant"""

#     remove_profile_photo = forms.BooleanField(
#         required=False,
#         label='Supprimer la photo actuelle',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )

#     bac_etablissement_existant = SchoolChoiceField(
#         queryset=School.objects.none(),
#         label="Établissement d'obtention du Baccalauréat (existant)",
#         widget=forms.Select(attrs={
#             'class': 'form-select'
#         }),
#         empty_label="Sélectionner un établissement existant",
#         required=False,
#     )

#     bac_etablissement = forms.CharField(
#         max_length=255,
#         label="Ou saisir un autre établissement",
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': "Nom de l'établissement d'obtention du Baccalauréat",
#         }),
#         required=False,
#     )

#     specialite_souhaitee_1 = forms.ModelChoiceField(
#         queryset=Speciality.objects.none(),
#         label="Spécialité souhaitée 1",
#         widget=forms.Select(attrs={
#             'class': 'form-select',
#             'disabled': True,
#         }),
#         empty_label="Sélectionner d'abord un programme",
#         required=False,
#     )

#     specialite_souhaitee_2 = forms.ModelChoiceField(
#         queryset=Speciality.objects.none(),
#         label="Spécialité souhaitée 2",
#         widget=forms.Select(attrs={
#             'class': 'form-select',
#             'disabled': True,
#         }),
#         empty_label="Sélectionner d'abord un programme",
#         required=False,
#     )

#     specialite_souhaitee_3 = forms.ModelChoiceField(
#         queryset=Speciality.objects.none(),
#         label="Spécialité souhaitée 3",
#         widget=forms.Select(attrs={
#             'class': 'form-select',
#             'disabled': True,
#         }),
#         empty_label="Sélectionner d'abord un programme",
#         required=False,
#     )

#     # Desactiver le champs statut
#     status = forms.ChoiceField(
#         choices=Student.STUDENT_STATUS_CHOICES,
#         label="Statut",
#         widget=forms.Select(attrs={
#             'class': 'form-select',
#             'disabled': True,
#         }),
#         disabled=True,
#         required=False,
#     )

#     class Meta:
#         model = Student
#         fields = [
#             'firstname', 'lastname', 'date_naiss', 'gender', 'lang',
#             'phone_number', 'email', 'status', 'school', 'program', 'godfather', 'profile_photo'
#         ]
#         widgets = {
#             'firstname': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Prénom'
#             }),
#             'lastname': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nom de famille'
#             }),
#             'date_naiss': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date'
#             }),
#             'gender': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'lang': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'phone_number': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': '+237 6XX XXX XXX'
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'exemple@email.com'
#             }),
#             'status': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'school': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'program': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'godfather': forms.Select(attrs={
#                 'class': 'form-select'
#             }),
#             'profile_photo': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': 'image/png,image/jpeg,image/jpg'
#             }),
#         }
#         labels = {
#             'firstname': 'Prénom',
#             'lastname': 'Nom de famille',
#             'date_naiss': 'Date de naissance',
#             'gender': 'Genre',
#             'lang': 'Langue',
#             'phone_number': 'Numéro de téléphone',
#             'email': 'Adresse email',
#             'status': 'Statut',
#             'school': 'École',
#             'program': 'Programme',
#             'godfather': 'Parrain',
#             'profile_photo': 'Photo de profil',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Rendre certains champs optionnels
#         self.fields['phone_number'].required = False
#         self.fields['email'].required = False
#         self.fields['school'].required = False
#         self.fields['program'].required = False
#         self.fields['godfather'].required = False
#         self.fields['date_naiss'].required = False
#         self.fields['profile_photo'].required = False

#         self.fields['school'].queryset = School.objects.all().order_by('name', 'phone_number')
#         self.fields['program'].queryset = Program.objects.all().order_by('name')
#         self.fields['godfather'].queryset = Godfather.objects.all().order_by('full_name', 'phone_number', 'email')
#         self.fields['bac_etablissement_existant'].queryset = School.objects.filter(level='secondary').order_by(
#             'name', 'phone_number'
#         )

#         program_id = None
#         if self.data:
#             program_id = self.data.get('program')
#         elif self.instance and self.instance.program_id:
#             program_id = self.instance.program_id
#         elif self.initial:
#             program_id = self.initial.get('program')

#         speciality_field_names = [
#             'specialite_souhaitee_1',
#             'specialite_souhaitee_2',
#             'specialite_souhaitee_3',
#         ]

#         if program_id:
#             try:
#                 program_id = int(program_id)
#                 specialities = Speciality.objects.filter(program_id=program_id).order_by('name')
#                 for index, field_name in enumerate(speciality_field_names, start=1):
#                     self.fields[field_name].queryset = specialities
#                     self.fields[field_name].widget.attrs.pop('disabled', None)
#                     self.fields[field_name].empty_label = (
#                         f"Sélectionner la spécialité #{index}"
#                         if index == 1 else f"Sélectionner la spécialité #{index} (optionnel)"
#                     )
#             except (TypeError, ValueError):
#                 for field_name in speciality_field_names:
#                     self.fields[field_name].queryset = Speciality.objects.all().order_by('name')
#                     self.fields[field_name].widget.attrs.pop('disabled', None)
#         else:
#             for field_name in speciality_field_names:
#                 self.fields[field_name].queryset = Speciality.objects.all().order_by('name')

#         if not self.is_bound and self.instance and self.instance.pk:
#             if self.instance.school:
#                 if self.instance.school.level == 'secondary':
#                     self.initial.setdefault('bac_etablissement_existant', self.instance.school)
#                 else:
#                     self.initial.setdefault('bac_etablissement', self.instance.school.name)

#             if self.instance.program_id:
#                 for field_name in speciality_field_names:
#                     speciality_name = getattr(self.instance, field_name, '')
#                     if not speciality_name:
#                         continue

#                     speciality = Speciality.objects.filter(
#                         program_id=self.instance.program_id,
#                         name=speciality_name,
#                     ).first()
#                     if speciality:
#                         self.initial.setdefault(field_name, speciality)

#     def clean(self):
#         cleaned_data = super().clean()
#         bac_etablissement_existant = cleaned_data.get('bac_etablissement_existant')
#         bac_etablissement = (cleaned_data.get('bac_etablissement') or '').strip()

#         cleaned_data['bac_etablissement'] = (
#             bac_etablissement_existant.name if bac_etablissement_existant else bac_etablissement
#         )
#         cleaned_data['school'] = bac_etablissement_existant

#         programme = cleaned_data.get('program')
#         selected_specialities = []

#         for field_name in [
#             'specialite_souhaitee_1',
#             'specialite_souhaitee_2',
#             'specialite_souhaitee_3',
#         ]:
#             specialite = cleaned_data.get(field_name)

#             if programme and specialite and specialite.program_id != programme.id:
#                 self.add_error(
#                     field_name,
#                     "La spécialité sélectionnée doit appartenir au programme choisi.",
#                 )
#                 continue

#             if not specialite:
#                 continue

#             if specialite.pk in selected_specialities:
#                 self.add_error(field_name, "Veuillez choisir une spécialité différente pour chaque choix.")
#                 continue

#             selected_specialities.append(specialite.pk)

#         return cleaned_data

#     def save(self, commit=True):
#         previous_photo = None
#         if self.instance.pk:
#             previous_photo = Student.objects.get(pk=self.instance.pk).profile_photo

#         uploaded_photo = self.files.get('profile_photo')
#         should_remove_photo = self.cleaned_data.get('remove_profile_photo') and not uploaded_photo

#         student = super().save(commit=False)

#         school = self.cleaned_data.get('bac_etablissement_existant')
#         if not school:
#             school_name = (self.cleaned_data.get('bac_etablissement') or '').strip()
#             if school_name:
#                 school = School.objects.filter(name__iexact=school_name, level='secondary').first()
#                 if not school:
#                     school = School.objects.create(name=school_name, level='secondary')

#         student.school = school
#         student.specialite_souhaitee_1 = (
#             self.cleaned_data['specialite_souhaitee_1'].name
#             if self.cleaned_data.get('specialite_souhaitee_1') else ''
#         )
#         student.specialite_souhaitee_2 = (
#             self.cleaned_data['specialite_souhaitee_2'].name
#             if self.cleaned_data.get('specialite_souhaitee_2') else ''
#         )
#         student.specialite_souhaitee_3 = (
#             self.cleaned_data['specialite_souhaitee_3'].name
#             if self.cleaned_data.get('specialite_souhaitee_3') else ''
#         )

#         if should_remove_photo:
#             student.profile_photo = None

#         if commit:
#             student.save()
#             self.save_m2m()

#             previous_photo_name = getattr(previous_photo, 'name', '')
#             current_photo_name = getattr(student.profile_photo, 'name', '')

#             if should_remove_photo and previous_photo_name:
#                 previous_photo.storage.delete(previous_photo_name)
#             elif uploaded_photo and previous_photo_name and previous_photo_name != current_photo_name:
#                 previous_photo.storage.delete(previous_photo_name)

#         return student


# class StudentMetaDataEditForm(forms.ModelForm):
#     """Formulaire de modification des métadonnées de l'étudiant"""

#     remove_preuve_baccalaureat = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_acte_naissance = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_certificat_nationalite = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_releve_notes_last_class = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_justificatif_dernier_diplome = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_bulletins_terminale = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_decharge_equivalence = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_releve_notes_master1 = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )
#     remove_photocopie_bts_hnd = forms.BooleanField(
#         required=False,
#         label='Supprimer le document actuel',
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         })
#     )

#     removable_file_fields = [
#         'preuve_baccalaureat',
#         'acte_naissance',
#         'certificat_nationalite',
#         'releve_notes_last_class',
#         'justificatif_dernier_diplome',
#         'decharge_equivalence',
#         'bulletins_terminale',
#         'releve_notes_master1',
#         'photocopie_bts_hnd',
#     ]

#     class Meta:
#         model = StudentMetaData
#         fields = [
#             'mother_full_name', 'mother_live_city', 'mother_email',
#             'mother_occupation', 'mother_phone_number', 'father_full_name',
#             'father_live_city', 'father_email',
#             'father_occupation', 'father_phone_number', 'original_country',
#             'original_region', 'original_department', 'original_district',
#             'residence_city', 'residence_quarter', 'is_complete',
#             'preuve_baccalaureat', 'acte_naissance', 'certificat_nationalite', 'releve_notes_last_class',
#             'justificatif_dernier_diplome', 'decharge_equivalence', 'bulletins_terminale',
#             'releve_notes_master1', 'photocopie_bts_hnd'
#         ]
#         widgets = {
#             'mother_full_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nom complet de la mère'
#             }),
#             'mother_live_city': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ville de résidence de la mère'
#             }),
#             'mother_email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Email de la mère'
#             }),
#             'mother_occupation': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Profession de la mère'
#             }),
#             'mother_phone_number': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Téléphone de la mère'
#             }),
#             'father_full_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nom complet du père'
#             }),
#             'father_live_city': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ville de résidence du père'
#             }),
#             'father_email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Email du père'
#             }),
#             'father_occupation': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Profession du père'
#             }),
#             'father_phone_number': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Téléphone du père'
#             }),
#             'original_country': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Pays d\'origine'
#             }),
#             'original_region': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Région d\'origine'
#             }),
#             'original_department': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Département d\'origine'
#             }),
#             'original_district': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Arrondissement d\'origine'
#             }),
#             'residence_city': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ville de résidence'
#             }),
#             'residence_quarter': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Quartier de résidence'
#             }),
#             'is_complete': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'preuve_baccalaureat': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'acte_naissance': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'certificat_nationalite': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'releve_notes_last_class': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'justificatif_dernier_diplome': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'decharge_equivalence': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'bulletins_terminale': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'releve_notes_master1': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#             'photocopie_bts_hnd': forms.FileInput(attrs={
#                 'class': 'form-control',
#                 'accept': '.png,.jpg,.jpeg,.pdf'
#             }),
#         }
#         labels = {
#             'mother_full_name': 'Nom complet de la mère',
#             'mother_live_city': 'Ville de résidence de la mère',
#             'mother_email': 'Email de la mère',
#             'mother_occupation': 'Profession de la mère',
#             'mother_phone_number': 'Téléphone de la mère',
#             'father_full_name': 'Nom complet du père',
#             'father_live_city': 'Ville de résidence du père',
#             'father_email': 'Email du père',
#             'father_occupation': 'Profession du père',
#             'father_phone_number': 'Téléphone du père',
#             'original_country': 'Pays d\'origine',
#             'original_region': 'Région d\'origine',
#             'original_department': 'Département d\'origine',
#             'original_district': 'Arrondissement d\'origine',
#             'residence_city': 'Ville de résidence',
#             'residence_quarter': 'Quartier de résidence',
#             'is_complete': 'Dossier complet',
#             'preuve_baccalaureat': 'Preuve d\'obtention du baccalauréat',
#             'acte_naissance': 'Photocopie certifiée de l\'acte de naissance',
#             'certificat_nationalite': 'Certificat de nationalité',
#             'releve_notes_last_class': 'Relevé de notes de la dernière classe fréquentée',
#             'justificatif_dernier_diplome': 'Justificatif du dernier diplôme obtenu',
#             'decharge_equivalence': 'Décharge de la demande d\'équivalence',
#             'bulletins_terminale': 'Bulletins de la classe de terminale',
#             'releve_notes_master1': 'Relevé de notes du Master 1',
#             'photocopie_bts_hnd': 'Photocopie du BTS, HND ou diplôme équivalent',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Rendre tous les champs optionnels sauf le pays d'origine
#         for field_name, field in self.fields.items():
#             if field_name != 'original_country':
#                 field.required = False

#         for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
#             if field_name not in self.fields:
#                 continue

#             document_definition = PROGRAM_DOCUMENTS_BY_FIELD[field_name]
#             self.fields[field_name].label = document_definition['label']
#             self.fields[field_name].help_text = document_definition['help_text']

#     def save(self, commit=True):
#         previous_files = {}
#         if self.instance.pk:
#             previous_instance = StudentMetaData.objects.get(pk=self.instance.pk)
#             previous_files = {
#                 field_name: getattr(previous_instance, field_name)
#                 for field_name in self.removable_file_fields
#             }

#         uploaded_files = {
#             field_name: self.files.get(field_name)
#             for field_name in self.removable_file_fields
#         }
#         removal_flags = {
#             field_name: bool(self.cleaned_data.get(f'remove_{field_name}')) and not uploaded_files[field_name]
#             for field_name in self.removable_file_fields
#         }

#         metadata = super().save(commit=False)

#         for field_name, should_remove in removal_flags.items():
#             if should_remove:
#                 setattr(metadata, field_name, None)

#         if commit:
#             metadata.save()
#             self.save_m2m()

#             for field_name in self.removable_file_fields:
#                 previous_file = previous_files.get(field_name)
#                 previous_file_name = getattr(previous_file, 'name', '')
#                 current_file = getattr(metadata, field_name)
#                 current_file_name = getattr(current_file, 'name', '')

#                 if removal_flags[field_name] and previous_file_name:
#                     previous_file.storage.delete(previous_file_name)
#                 elif uploaded_files[field_name] and previous_file_name and previous_file_name != current_file_name:
#                     previous_file.storage.delete(previous_file_name)

#         return metadata


class OfficialDocumentForm(forms.ModelForm):
    """Formulaire pour la création et modification des documents officiels"""

    student_search = forms.CharField(
        label="Étudiant",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control shadow-inset border-light bg-primary document-student-autocomplete',
            'placeholder': 'Rechercher par matricule, nom, prénom ou programme...',
            'autocomplete': 'off',
        }),
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        label="Étudiant",
        required=False,
        widget=forms.HiddenInput(),
    )

    level = forms.ModelChoiceField(
        queryset=Level.objects.none(),
        label="Niveau",
        widget=forms.Select(attrs={
            'class': 'form-control shadow-inset border-light bg-primary',
            'required': True
        }),
        empty_label="Sélectionner un niveau"
    )

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        label="Année académique",
        widget=forms.Select(attrs={
            'class': 'form-control shadow-inset border-light bg-primary',
            'required': True
        }),
        empty_label="Sélectionner une année académique"
    )

    class Meta:
        model = OfficialDocument
        fields = ['type', 'status', 'withdrawn_date', 'returned_at']
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'withdrawn_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'returned_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'type': 'Type de document',
            'status': 'Statut',
            'withdrawn_date': 'Date de retrait',
            'returned_at': 'Date de retour',
        }

    @staticmethod
    def get_student_label(student):
        student_name = f"{student.firstname} {student.lastname}".strip()
        program_name = student.program.name if student.program_id else 'Programme non défini'
        return f"{student.matricule} - {student_name} - {program_name}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def normalize_pk(value):
            return getattr(value, 'pk', value)

        # Rendre la date de retrait optionnelle
        self.fields['withdrawn_date'].required = False

        allowed_type_choices = [
            choice
            for choice in OfficialDocument._meta.get_field('type').choices
            if choice[0] != OfficialDocument.TYPE_REGISTRATION_CERTIFICATE
        ]

        student_level = getattr(self.instance, 'student_level', None)
        selected_student_id = normalize_pk(
            self.data.get('student') or self.initial.get('student') or getattr(student_level, 'student_id', None)
        )
        selected_level_id = normalize_pk(
            self.data.get('level') or self.initial.get('level') or getattr(student_level, 'level_id', None)
        )
        selected_academic_year_id = normalize_pk(
            self.data.get('academic_year') or self.initial.get('academic_year') or getattr(student_level, 'academic_year_id', None)
        )

        # Si on modifie un document existant, pré-remplir les champs
        if self.instance and self.instance.pk and student_level:
            self.fields['student'].initial = student_level.student
            self.fields['level'].initial = student_level.level
            self.fields['academic_year'].initial = student_level.academic_year

            if self.instance.type == OfficialDocument.TYPE_REGISTRATION_CERTIFICATE:
                allowed_type_choices = [
                    choice
                    for choice in OfficialDocument._meta.get_field('type').choices
                    if choice[0] == OfficialDocument.TYPE_REGISTRATION_CERTIFICATE
                ]
                self.fields['type'].disabled = True
                self.fields['type'].help_text = (
                    "Le certificat d'inscription est créé automatiquement lors de l'inscription définitive."
                )

        self.fields['type'].choices = allowed_type_choices

        student_queryset = Student.objects.select_related('program').filter(
            student_levels__academic_year__isnull=False,
        ).distinct().order_by('matricule')
        self.fields['student'].queryset = student_queryset

        selected_student = None
        if selected_student_id:
            selected_student = student_queryset.filter(pk=selected_student_id).first()

        level_ids = StudentLevel.objects.filter(
            student_id=selected_student_id,
        ).values_list('level_id', flat=True)
        self.fields['level'].queryset = Level.objects.filter(
            pk__in=level_ids,
        ).distinct().order_by('academic_order', 'name')

        academic_year_ids = StudentLevel.objects.filter(
            student_id=selected_student_id,
            level_id=selected_level_id,
            academic_year__isnull=False,
        ).values_list('academic_year_id', flat=True)
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(
            pk__in=academic_year_ids,
        ).distinct().order_by('-start_at')

        self.fields['level'].empty_label = (
            "Sélectionner un niveau" if selected_student_id else "Sélectionner d'abord un étudiant"
        )
        self.fields['academic_year'].empty_label = (
            "Sélectionner une année académique" if selected_level_id else "Sélectionner d'abord un niveau"
        )

        if selected_student and not self.is_bound:
            self.fields['student_search'].initial = self.get_student_label(selected_student)

        if (
            not self.is_bound
            and selected_student_id
            and selected_level_id
            and not selected_academic_year_id
            and self.fields['academic_year'].queryset.count() == 1
        ):
            self.fields['academic_year'].initial = self.fields['academic_year'].queryset.first()

        self.fields['student_search'].widget.attrs['data-selected-student-id'] = (
            str(selected_student.pk) if selected_student else ''
        )

    def clean(self):
        cleaned_data = super().clean()
        document_type = cleaned_data.get('type') or getattr(self.instance, 'type', None)
        status = cleaned_data.get('status')
        withdrawn_date = cleaned_data.get('withdrawn_date')
        student_search = (cleaned_data.get('student_search') or '').strip()
        student = cleaned_data.get('student')
        level = cleaned_data.get('level')
        academic_year = cleaned_data.get('academic_year')

        if document_type == OfficialDocument.TYPE_REGISTRATION_CERTIFICATE and not (self.instance and self.instance.pk):
            raise forms.ValidationError(
                "Le certificat d'inscription est créé automatiquement lors de l'inscription définitive."
            )

        # Validation : si le statut est 'withdrawn', la date de retrait est obligatoire
        if status == 'withdrawn' and not withdrawn_date:
            raise forms.ValidationError(
                "La date de retrait est obligatoire lorsque le statut est 'Déchargé'."
            )

        # Validation : si le statut n'est pas 'withdrawn', la date de retrait doit être vide
        if status != 'withdrawn' and withdrawn_date:
            cleaned_data['withdrawn_date'] = None

        if not student:
            if student_search:
                self.add_error('student', "Veuillez sélectionner un étudiant dans la liste proposée.")
            else:
                self.add_error('student', "Veuillez sélectionner un étudiant.")

        if student and level and academic_year:
            student_level = StudentLevel.objects.filter(
                student=student,
                level=level,
                academic_year=academic_year
            ).select_related('student', 'level', 'academic_year').first()

            if not student_level:
                self.add_error(
                    'academic_year',
                    "L'année académique sélectionnée n'est pas associée à cet étudiant pour le niveau choisi.",
                )
                return cleaned_data

            if document_type:
                existing_doc = OfficialDocument.objects.filter(
                    student_level=student_level,
                    type=document_type
                ).exclude(pk=self.instance.pk).first()

                if existing_doc:
                    document_label = dict(OfficialDocument.TYPE_CHOICES).get(document_type, document_type)
                    raise forms.ValidationError(
                        f"Un document de type '{document_label}' existe déjà pour "
                        f"{student.firstname} {student.lastname} en {level.name} "
                        f"({academic_year.name})."
                    )

            cleaned_data['student_level'] = student_level

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Assigner le student_level trouvé dans clean()
        if hasattr(self, 'cleaned_data') and 'student_level' in self.cleaned_data:
            instance.student_level = self.cleaned_data['student_level']

        if commit:
            instance.save()

        return instance


class StudentLevelForm(forms.ModelForm):
    """Formulaire pour gérer les niveaux d'un étudiant"""

    class Meta:
        model = StudentLevel
        fields = ['level', 'academic_year']
        widgets = {
            'level': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
        labels = {
            'level': 'Niveau',
            'academic_year': 'Année académique',
        }

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        # Ordonner les choix
        self.fields['level'].queryset = Level.objects.all().order_by('name')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')

    def clean(self):
        cleaned_data = super().clean()
        level = cleaned_data.get('level')
        academic_year = cleaned_data.get('academic_year')

        if self.student and level and academic_year:
            # Vérifier s'il existe déjà un StudentLevel pour cette combinaison
            existing = StudentLevel.objects.filter(
                student=self.student,
                level=level,
                academic_year=academic_year
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise forms.ValidationError(
                    f"L'étudiant est déjà associé au niveau {level.name} "
                    f"pour l'année {academic_year.name}."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.student:
            instance.student = self.student

        if commit:
            instance.save()

        return instance


class BulkDocumentCreationForm(forms.Form):
    """Formulaire pour la création en masse de documents officiels"""

    document_type = forms.ChoiceField(
        choices=OfficialDocument._meta.get_field('type').choices,
        label="Type de document",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Année académique",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label="Sélectionner une année académique"
    )

    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        label="Niveau",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label="Sélectionner un niveau"
    )

    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        label="Programme (optionnel)",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Tous les programmes",
        required=False
    )

    status = forms.ChoiceField(
        choices=OfficialDocument._meta.get_field('status').choices,
        label="Statut initial des documents",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        initial='available'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordonner les choix
        academic_years = AcademicYear.objects.all().order_by('-start_at')
        self.fields['document_type'].choices = [
            choice
            for choice in OfficialDocument._meta.get_field('type').choices
            if choice[0] != OfficialDocument.TYPE_REGISTRATION_CERTIFICATE
        ]
        self.fields['academic_year'].queryset = academic_years
        self.fields['level'].queryset = Level.objects.all().order_by('name')
        self.fields['program'].queryset = Program.objects.all().order_by('name')

        if not self.is_bound and self.fields['academic_year'].initial in (None, ''):
            self.fields['academic_year'].initial = AcademicYear.get_active_year() or academic_years.first()

    def clean_document_type(self):
        document_type = self.cleaned_data.get('document_type')
        if document_type == OfficialDocument.TYPE_REGISTRATION_CERTIFICATE:
            raise forms.ValidationError(
                "Le certificat d'inscription est créé automatiquement lors de l'inscription définitive."
            )
        return document_type

    def get_matching_students(self):
        """Retourne les étudiants qui correspondent aux critères sélectionnés"""
        if not self.is_valid():
            return Student.objects.none()

        academic_year = self.cleaned_data.get('academic_year')
        level = self.cleaned_data.get('level')
        program = self.cleaned_data.get('program')

        # Filtrer les étudiants qui ont un StudentLevel correspondant
        students = Student.objects.filter(
            student_levels__academic_year=academic_year,
            student_levels__level=level,
            student_levels__is_registered=True,
            status='registered'
        ).select_related('program').distinct().order_by('matricule')

        # Filtrer par programme si spécifié
        if program:
            students = students.filter(program=program)

        return students

    @staticmethod
    def _get_registered_student_level(student, academic_year, level):
        return student.student_levels.filter(
            academic_year=academic_year,
            level=level,
            is_registered=True,
        ).order_by('-is_active', '-registered_at', 'pk').first()

    def get_existing_documents_count(self):
        """Retourne le nombre de documents existants pour éviter les doublons"""
        if not self.is_valid():
            return 0

        students = self.get_matching_students()
        document_type = self.cleaned_data.get('document_type')
        academic_year = self.cleaned_data.get('academic_year')
        level = self.cleaned_data.get('level')

        existing_count = 0
        for student in students:
            student_level = self._get_registered_student_level(student, academic_year, level)

            if student_level:
                existing = OfficialDocument.objects.filter(
                    student_level=student_level,
                    type=document_type
                ).exists()
                if existing:
                    existing_count += 1

        return existing_count

    def create_documents(self):
        """Crée les documents pour tous les étudiants correspondants"""
        if not self.is_valid():
            return 0, 0, []

        students = self.get_matching_students()
        document_type = self.cleaned_data.get('document_type')
        academic_year = self.cleaned_data.get('academic_year')
        level = self.cleaned_data.get('level')
        status = self.cleaned_data.get('status')

        created_count = 0
        skipped_count = 0
        errors = []

        for student in students:
            try:
                student_level = self._get_registered_student_level(student, academic_year, level)

                if not student_level:
                    errors.append(
                        f"Aucune inscription valide trouvée pour {student.matricule} au niveau {level.name} "
                        f"pour l'année {academic_year.name}."
                    )
                    continue

                # Vérifier si le document existe déjà
                existing = OfficialDocument.objects.filter(
                    student_level=student_level,
                    type=document_type
                ).exists()

                if not existing:
                    OfficialDocument.objects.create(
                        student_level=student_level,
                        type=document_type,
                        status=status
                    )
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                errors.append(f"Erreur pour {student.matricule}: {str(e)}")

        return created_count, skipped_count, errors


class GeneralSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres généraux uniquement
    """

    class Meta:
        model = SystemSettings
        fields = [
            'institution_name', 'institution_code', 'address', 'phone',
            'email', 'website', 'logo', 'timezone', 'language'
        ]

        widgets = {
            'institution_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'institution-name'}),
            'institution_code': forms.TextInput(attrs={'class': 'form-control', 'id': 'institution-code'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'id': 'website'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'logo', 'accept': 'image/*'}),
            'timezone': forms.Select(attrs={'class': 'form-select', 'id': 'timezone'}, choices=[
                ('Africa/Douala', 'Africa/Douala (GMT+1)'),
                ('UTC', 'UTC (GMT+0)'),
            ]),
            'language': forms.Select(attrs={'class': 'form-select', 'id': 'language'}, choices=[
                ('fr', 'Français'),
                ('en', 'English'),
            ]),
        }


class AcademicSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres académiques
    """

    class Meta:
        model = SystemSettings
        fields = [
            'inscription_period', 'auto_approval', 'require_documents',
            'allow_external_registration'
        ]

        widgets = {
            'inscription_period': forms.Select(attrs={'class': 'form-select', 'id': 'inscription-period'}),
        }


class ProgramLevelSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres des programmes et niveaux
    """

    class Meta:
        model = SystemSettings
        fields = [
            'auto_level_progression', 'allow_level_change', 'require_level_validation',
            'allow_program_change', 'require_program_validation'
        ]


class UserSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres utilisateurs
    """

    class Meta:
        model = SystemSettings
        fields = [
            'default_role', 'session_timeout', 'view_documents',
            'download_docs', 'update_profile', 'view_statistics'
        ]

        widgets = {
            'default_role': forms.Select(attrs={'class': 'form-select', 'id': 'default-role'}, choices=[
                ('student', 'Étudiant'),
                ('scholar', 'Scolarité'),
                ('teaching', 'Suivi des Enseignements'),
                ('super_admin', 'Administrateur'),
            ]),
            'session_timeout': forms.NumberInput(attrs={'class': 'form-control', 'id': 'session-timeout', 'min': 5, 'max': 480}),
        }


class DocumentSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres des documents
    """

    class Meta:
        model = SystemSettings
        fields = [
            'max_file_size', 'allowed_formats', 'student_card_enabled',
            'transcript_enabled', 'certificate_enabled', 'diploma_enabled',
            'require_original_docs'
        ]

        widgets = {
            'max_file_size': forms.NumberInput(attrs={'class': 'form-control', 'id': 'max-file-size', 'min': 1, 'max': 50}),
            'allowed_formats': forms.TextInput(attrs={'class': 'form-control', 'id': 'allowed-formats', 'readonly': True}),
        }


class NotificationSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres de notification
    """

    class Meta:
        model = SystemSettings
        fields = [
            'email_enrollment', 'email_documents', 'email_deadlines',
            'system_errors', 'system_updates'
        ]


class DataManagementSettingsForm(forms.ModelForm):
    """
    Formulaire pour les paramètres de gestion des données
    """

    class Meta:
        model = SystemSettings
        fields = [
            'backup_frequency', 'data_retention', 'audit_log',
            'data_encryption', 'auto_cleanup'
        ]

        widgets = {
            'backup_frequency': forms.Select(attrs={'class': 'form-select', 'id': 'backup-frequency'}),
            'data_retention': forms.NumberInput(attrs={'class': 'form-control', 'id': 'data-retention', 'min': 1, 'max': 20}),
        }
