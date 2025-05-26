from django import forms
from django.core.validators import RegexValidator
from students.models import Student
from accounts.models import BaseUser, Godfather
from academic.models import Speciality


class InscriptionEtape1Form(forms.Form):
    """Formulaire pour l'étape 1 : Informations administratives"""

    # Cadre réservé à l'administration
    candidat_numero = forms.CharField(
        max_length=50,
        label="Candidat N°",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro du candidat'
        }),
        required=False
    )

    moyenne = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        label="Moyenne",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        required=False
    )

    DECISION_CHOICES = [
        ('', 'Sélectionner'),
        ('AD', 'AD'),
        ('NAD', 'NAD'),
    ]

    decision_jury = forms.ChoiceField(
        choices=DECISION_CHOICES,
        label="Décision du Jury",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    numero_matricule = forms.CharField(
        max_length=50,
        label="Numéro du Matricule",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de matricule'
        }),
        required=False
    )

    annee_academique = forms.CharField(
        max_length=20,
        label="Année Académique",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '20__/20__'
        }),
        required=False
    )

    type_bourse = forms.CharField(
        max_length=100,
        label="Type de Bourse",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type de bourse'
        }),
        required=False
    )

    recommande_par = forms.CharField(
        max_length=200,
        label="Recommandé par",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de la personne/institution'
        }),
        required=False
    )

    date_decision = forms.DateField(
        label="Date de la décision",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    LETTRE_CHOICES = [
        ('', 'Sélectionner'),
        ('oui', 'Oui'),
        ('non', 'Non'),
    ]

    lettre_admission = forms.ChoiceField(
        choices=LETTRE_CHOICES,
        label="Lettre d'admission",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    date_lettre_admission = forms.DateField(
        label="Date de la lettre d'admission",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )


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
            'class': 'form-control',
            'type': 'date'
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
            'placeholder': 'Région d\'origine'
        })
    )

    departement_origine = forms.CharField(
        max_length=100,
        label="Département d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Département d\'origine'
        })
    )

    arrondissement_origine = forms.CharField(
        max_length=100,
        label="Arrondissement d'origine",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Arrondissement d\'origine'
        })
    )

    ville_residence = forms.CharField(
        max_length=100,
        label="Ville de résidence",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville de résidence actuelle'
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
            'placeholder': 'Profession actuelle (si applicable)'
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
        label="Probatoire - Série",
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

    # Choix de spécialité
    SPECIALITE_CHOICES = [
        ('', 'Sélectionner une spécialité'),
        ('communication_entreprise', 'Communication d\'Entreprise'),
        ('edition', 'Édition'),
        ('information_documentaire', 'Information Documentaire'),
        ('journalisme', 'Journalisme'),
        ('publicite_marketing', 'Publicité et Marketing'),
    ]

    specialite_choisie_1 = forms.ChoiceField(
        choices=SPECIALITE_CHOICES,
        label="Première spécialité choisie",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    specialite_choisie_2 = forms.ChoiceField(
        choices=SPECIALITE_CHOICES,
        label="Deuxième spécialité choisie",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    # Constitution du dossier
    preuve_baccalaureat = forms.BooleanField(
        label="Preuve d'obtention du Baccalauréat ou tout autre document équivalent",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    photocopie_acte_naissance = forms.BooleanField(
        label="Photocopie certifiée de l'acte de naissance",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    photocopie_releve_notes = forms.BooleanField(
        label="Une photocopie certifiée du relevé des notes du Baccalauréat",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
    )

    photocopie_bulletins = forms.BooleanField(
        label="Photocopie des bulletins de la classe de Terminale",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False
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
