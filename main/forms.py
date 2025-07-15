from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from students.models import Student, StudentMetaData, OfficialDocument, StudentLevel
from accounts.models import BaseUser, Godfather
from academic.models import Speciality, Program, Level, AcademicYear
from schools.models import School
from .models import SystemSettings


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


# Le formulaire InscriptionEtape1Form a été supprimé car il n'est plus nécessaire
# Les informations administratives sont maintenant intégrées dans le formulaire complet

class InscriptionCompleteForm(forms.Form):
    """Formulaire complet d'inscription combinant toutes les étapes nécessaires"""

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

    # Informations complémentaires
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

    # Informations sur l'année académique et le niveau
    annee_academique = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Année académique",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner une année académique"
    )

    niveau = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        label="Niveau",
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

    # Informations du tuteur/responsable
    nom_tuteur = forms.CharField(
        max_length=100,
        label="Nom et prénom du tuteur/responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom et prénom du tuteur'
        }),
        required=False
    )

    profession_tuteur = forms.CharField(
        max_length=200,
        label="Profession du tuteur/responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Profession du tuteur'
        }),
        required=False
    )

    telephone_tuteur = forms.CharField(
        max_length=17,
        label="Téléphone du tuteur/responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 6XX XXX XXX'
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

    lien_parente_urgence = forms.CharField(
        max_length=100,
        label="Lien de parenté",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Relation avec l\'étudiant'
        }),
        required=False
    )

    # === SECTION 3: CURSUS SCOLAIRE ET UNIVERSITAIRE (ex-étape 4) ===
    # Cursus scolaire
    bepc_cap_serie = forms.CharField(
        max_length=50,
        label="BEPC / CAP - Série",
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

    # Baccalauréat
    bac_serie = forms.CharField(
        max_length=50,
        label="Baccalauréat - Série",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Série'
        }),
        required=False
    )

    bac_annee = forms.IntegerField(
        label="Baccalauréat - Année d'obtention",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2023'
        }),
        required=False
    )

    bac_mention = forms.CharField(
        max_length=50,
        label="Baccalauréat - Mention",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mention'
        }),
        required=False
    )

    bac_etablissement = forms.CharField(
        max_length=200,
        label="Établissement d'obtention du Baccalauréat",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'établissement'
        }),
        required=False
    )

    # Études supérieures
    etudes_superieures = forms.CharField(
        max_length=500,
        label="Études supérieures antérieures",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Détaillez vos études supérieures précédentes'
        }),
        required=False
    )

    # Choix de spécialité (dynamique basé sur le programme sélectionné)
    specialite_souhaitee = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),  # Vide par défaut
        label="Spécialité souhaitée",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True  # Désactivé par défaut jusqu'à ce qu'un programme soit sélectionné
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False
    )

    autre_specialite = forms.CharField(
        max_length=100,
        label="Autre spécialité (précisez)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Précisez la spécialité'
        }),
        required=False
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
                self.fields['specialite_souhaitee'].queryset = Speciality.objects.filter(program_id=program_id)
                self.fields['specialite_souhaitee'].widget.attrs['disabled'] = False
                self.fields['specialite_souhaitee'].empty_label = "Sélectionner une spécialité"
            except (ValueError, TypeError):
                pass

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
        required=True
    )

    certificat_nationalite = forms.FileField(
        label="Certificat de nationalité",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Certificat de nationalité. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    diplome_bac = forms.FileField(
        label="Diplôme du Baccalauréat",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie légalisée du diplôme du Baccalauréat. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
        required=True
    )

    releve_notes_bac = forms.FileField(
        label="Relevé de notes du Baccalauréat",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie du relevé de notes du Baccalauréat. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
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

    # Attestation
    attestation_veracite = forms.BooleanField(
        label="J'atteste que les informations indiquées ci-dessus sont complètes, authentiques et exactes.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordonner les choix
        self.fields['annee_academique'].queryset = AcademicYear.objects.all().order_by('-start_at')
        self.fields['niveau'].queryset = Level.objects.all().order_by('name')
        self.fields['programme'].queryset = Program.objects.all().order_by('name')

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

    releve_notes_bac = forms.FileField(
        label="Photocopie certifiée du relevé des notes du Baccalauréat",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.pdf'
        }),
        help_text="Photocopie certifiée conforme du relevé des notes du baccalauréat. Formats acceptés : PNG, JPG, PDF. Taille max : 5 Mo. Document lisible requis.",
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
                self.fields['specialite_choisie_1'].widget.attrs['disabled'] = False
                self.fields['specialite_choisie_1'].empty_label = "Sélectionner une spécialité"

                self.fields['specialite_choisie_2'].queryset = Speciality.objects.filter(program_id=program_id)
                self.fields['specialite_choisie_2'].widget.attrs['disabled'] = False
                self.fields['specialite_choisie_2'].empty_label = "Sélectionner une spécialité (optionnel)"
            except (ValueError, TypeError):
                pass

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


class StudentEditForm(forms.ModelForm):
    """Formulaire de modification des informations principales de l'étudiant"""

    class Meta:
        model = Student
        fields = [
            'firstname', 'lastname', 'date_naiss', 'gender', 'lang',
            'phone_number', 'email', 'status', 'school', 'program', 'godfather'
        ]
        widgets = {
            'firstname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'lastname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de famille'
            }),
            'date_naiss': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lang': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 6XX XXX XXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemple@email.com'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'school': forms.Select(attrs={
                'class': 'form-select'
            }),
            'program': forms.Select(attrs={
                'class': 'form-select'
            }),
            'godfather': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'firstname': 'Prénom',
            'lastname': 'Nom de famille',
            'date_naiss': 'Date de naissance',
            'gender': 'Genre',
            'lang': 'Langue',
            'phone_number': 'Numéro de téléphone',
            'email': 'Adresse email',
            'status': 'Statut',
            'school': 'École',
            'program': 'Programme',
            'godfather': 'Parrain',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs optionnels
        self.fields['phone_number'].required = False
        self.fields['email'].required = False
        self.fields['school'].required = False
        self.fields['program'].required = False
        self.fields['godfather'].required = False
        self.fields['date_naiss'].required = False


class StudentMetaDataEditForm(forms.ModelForm):
    """Formulaire de modification des métadonnées de l'étudiant"""

    class Meta:
        model = StudentMetaData
        fields = [
            'mother_full_name', 'mother_live_city', 'mother_email',
            'mother_occupation', 'mother_phone_number', 'father_full_name',
            'father_occupation', 'father_phone_number', 'original_country',
            'original_region', 'original_department', 'original_district',
            'residence_city', 'residence_quarter', 'is_complete',
            'preuve_baccalaureat', 'acte_naissance', 'releve_notes_bac', 'bulletins_terminale'
        ]
        widgets = {
            'mother_full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom complet de la mère'
            }),
            'mother_live_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville de résidence de la mère'
            }),
            'mother_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de la mère'
            }),
            'mother_occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profession de la mère'
            }),
            'mother_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone de la mère'
            }),
            'father_full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom complet du père'
            }),
            'father_occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profession du père'
            }),
            'father_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone du père'
            }),
            'original_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pays d\'origine'
            }),
            'original_region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Région d\'origine'
            }),
            'original_department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Département d\'origine'
            }),
            'original_district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Arrondissement d\'origine'
            }),
            'residence_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville de résidence'
            }),
            'residence_quarter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quartier de résidence'
            }),
            'is_complete': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'preuve_baccalaureat': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'acte_naissance': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'releve_notes_bac': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'bulletins_terminale': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
        }
        labels = {
            'mother_full_name': 'Nom complet de la mère',
            'mother_live_city': 'Ville de résidence de la mère',
            'mother_email': 'Email de la mère',
            'mother_occupation': 'Profession de la mère',
            'mother_phone_number': 'Téléphone de la mère',
            'father_full_name': 'Nom complet du père',
            'father_occupation': 'Profession du père',
            'father_phone_number': 'Téléphone du père',
            'original_country': 'Pays d\'origine',
            'original_region': 'Région d\'origine',
            'original_department': 'Département d\'origine',
            'original_district': 'Arrondissement d\'origine',
            'residence_city': 'Ville de résidence',
            'residence_quarter': 'Quartier de résidence',
            'is_complete': 'Dossier complet',
            'preuve_baccalaureat': 'Preuve d\'obtention du baccalauréat',
            'acte_naissance': 'Photocopie certifiée de l\'acte de naissance',
            'releve_notes_bac': 'Relevé des notes du Baccalauréat',
            'bulletins_terminale': 'Bulletins de la classe de terminale',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre tous les champs optionnels sauf le pays d'origine
        for field_name, field in self.fields.items():
            if field_name != 'original_country':
                field.required = False


class OfficialDocumentForm(forms.ModelForm):
    """Formulaire pour la création et modification des documents officiels"""

    # Champs séparés pour permettre la sélection individuelle
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        label="Étudiant",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label="Sélectionner un étudiant"
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

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label="Année académique",
        widget=forms.Select(attrs={
            'class': 'form-select',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre la date de retrait optionnelle
        self.fields['withdrawn_date'].required = False

        # Si on modifie un document existant, pré-remplir les champs
        if self.instance and self.instance.pk and self.instance.student_level:
            self.fields['student'].initial = self.instance.student_level.student
            self.fields['level'].initial = self.instance.student_level.level
            self.fields['academic_year'].initial = self.instance.student_level.academic_year

        # Personnaliser l'affichage des étudiants
        self.fields['student'].queryset = Student.objects.all().order_by('matricule')

        # Personnaliser les choix pour afficher matricule - nom prénom
        student_choices = [('', 'Sélectionner un étudiant')]
        for student in self.fields['student'].queryset:
            label = f"{student.matricule} - {student.firstname} {student.lastname}"
            student_choices.append((student.pk, label))
        self.fields['student'].choices = student_choices

        # Personnaliser l'affichage des niveaux
        self.fields['level'].queryset = Level.objects.all().order_by('name')

        # Personnaliser l'affichage des années académiques (les plus récentes en premier)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        withdrawn_date = cleaned_data.get('withdrawn_date')
        student = cleaned_data.get('student')
        level = cleaned_data.get('level')
        academic_year = cleaned_data.get('academic_year')

        # Validation : si le statut est 'withdrawn', la date de retrait est obligatoire
        if status == 'withdrawn' and not withdrawn_date:
            raise forms.ValidationError(
                "La date de retrait est obligatoire lorsque le statut est 'Déchargé'."
            )

        # Validation : si le statut n'est pas 'withdrawn', la date de retrait doit être vide
        if status != 'withdrawn' and withdrawn_date:
            cleaned_data['withdrawn_date'] = None

        # Vérifier qu'on a tous les champs nécessaires pour créer/trouver le StudentLevel
        if student and level and academic_year:
            # Rechercher ou créer le StudentLevel
            student_level, created = StudentLevel.objects.get_or_create(
                student=student,
                level=level,
                academic_year=academic_year
            )

            # Vérifier s'il existe déjà un document du même type pour ce StudentLevel
            if not self.instance.pk:  # Seulement pour la création, pas la modification
                existing_doc = OfficialDocument.objects.filter(
                    student_level=student_level,
                    type=cleaned_data.get('type')
                ).first()

                if existing_doc:
                    raise forms.ValidationError(
                        f"Un document de type '{cleaned_data.get('type')}' existe déjà pour "
                        f"{student.firstname} {student.lastname} en {level.name} "
                        f"({academic_year.name})."
                    )

            # Stocker le student_level pour l'utiliser dans save()
            cleaned_data['student_level'] = student_level

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Assigner le student_level trouvé/créé dans clean()
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
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')
        self.fields['level'].queryset = Level.objects.all().order_by('name')
        self.fields['program'].queryset = Program.objects.all().order_by('name')

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
            status='approved'  # Seulement les étudiants approuvés
        ).distinct()

        # Filtrer par programme si spécifié
        if program:
            students = students.filter(program=program)

        return students

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
            student_level = student.student_levels.filter(
                academic_year=academic_year,
                level=level
            ).first()

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
                # Trouver ou créer le StudentLevel
                student_level, _ = StudentLevel.objects.get_or_create(
                    student=student,
                    academic_year=academic_year,
                    level=level
                )

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
            'email', 'website', 'timezone', 'language'
        ]

        widgets = {
            'institution_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'institution-name'}),
            'institution_code': forms.TextInput(attrs={'class': 'form-control', 'id': 'institution-code'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'id': 'website'}),
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
