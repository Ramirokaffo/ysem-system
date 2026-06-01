
from django import forms
from students.models import Student, StudentMetaData
from accounts.models import Godfather
from academic.models import Speciality, Program
from academic.document_requirements import (
    PROGRAM_DOCUMENT_FIELD_NAMES,
    PROGRAM_DOCUMENTS_BY_FIELD,
)
from schools.models import School
from main.validators import validate_file_size, validate_phone_number


class SchoolChoiceField(forms.ModelChoiceField):
    """Champ de sélection des établissements avec libellé enrichi."""

    def label_from_instance(self, obj):
        parts = [obj.name]
        if obj.phone_number:
            parts.append(obj.phone_number)
        return " - ".join(parts)



class StudentEditForm(forms.ModelForm):
    """Formulaire de modification des informations principales de l'étudiant"""

    remove_profile_photo = forms.BooleanField(
        required=False,
        label='Supprimer la photo actuelle',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    bac_etablissement_existant = SchoolChoiceField(
        queryset=School.objects.none(),
        label="Établissement d'obtention du Baccalauréat (existant)",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Sélectionner un établissement existant",
        required=False,
    )

    bac_etablissement = forms.CharField(
        max_length=255,
        label="Ou saisir un autre établissement",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom de l'établissement d'obtention du Baccalauréat",
        }),
        required=False,
    )

    specialite_souhaitee_1 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 1",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'disabled': True,
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False,
    )

    specialite_souhaitee_2 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 2",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'disabled': True,
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False,
    )

    specialite_souhaitee_3 = forms.ModelChoiceField(
        queryset=Speciality.objects.none(),
        label="Spécialité souhaitée 3",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'disabled': True,
        }),
        empty_label="Sélectionner d'abord un programme",
        required=False,
    )

    # Desactiver le champs statut
    status = forms.ChoiceField(
        choices=Student.STUDENT_STATUS_CHOICES,
        label="Statut",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'disabled': True,
        }),
        disabled=True,
        required=False,
    )

    class Meta:
        model = Student
        fields = [
            'firstname', 'lastname', 'date_naiss', 'gender', 'lang',
            'phone_number', 'email', 'status', 'school', 'program', 'godfather', 'profile_photo'
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
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/png,image/jpeg,image/jpg'
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
            'profile_photo': 'Photo de profil',
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
        self.fields['profile_photo'].required = False
        self.fields['profile_photo'].validators.append(validate_file_size)
        self.fields['phone_number'].validators.append(validate_phone_number)

        self.fields['school'].queryset = School.objects.all().order_by('name', 'phone_number')
        self.fields['program'].queryset = Program.objects.all().order_by('name')
        self.fields['godfather'].queryset = Godfather.objects.all().order_by('full_name', 'phone_number', 'email')
        self.fields['bac_etablissement_existant'].queryset = School.objects.filter(level='secondary').order_by(
            'name', 'phone_number'
        )

        program_id = None
        if self.data:
            program_id = self.data.get('program')
        elif self.instance and self.instance.program_id:
            program_id = self.instance.program_id
        elif self.initial:
            program_id = self.initial.get('program')

        speciality_field_names = [
            'specialite_souhaitee_1',
            'specialite_souhaitee_2',
            'specialite_souhaitee_3',
        ]

        if program_id:
            try:
                program_id = int(program_id)
                specialities = Speciality.objects.filter(program_id=program_id).order_by('name')
                for index, field_name in enumerate(speciality_field_names, start=1):
                    self.fields[field_name].queryset = specialities
                    self.fields[field_name].widget.attrs.pop('disabled', None)
                    self.fields[field_name].empty_label = (
                        f"Sélectionner la spécialité #{index}"
                        if index == 1 else f"Sélectionner la spécialité #{index} (optionnel)"
                    )
            except (TypeError, ValueError):
                for field_name in speciality_field_names:
                    self.fields[field_name].queryset = Speciality.objects.all().order_by('name')
                    self.fields[field_name].widget.attrs.pop('disabled', None)
        else:
            for field_name in speciality_field_names:
                self.fields[field_name].queryset = Speciality.objects.all().order_by('name')

        if not self.is_bound and self.instance and self.instance.pk:
            if self.instance.school:
                if self.instance.school.level == 'secondary':
                    self.initial.setdefault('bac_etablissement_existant', self.instance.school)
                else:
                    self.initial.setdefault('bac_etablissement', self.instance.school.name)

            if self.instance.program_id:
                for field_name in speciality_field_names:
                    speciality_name = getattr(self.instance, field_name, '')
                    if not speciality_name:
                        continue

                    speciality = Speciality.objects.filter(
                        program_id=self.instance.program_id,
                        name=speciality_name,
                    ).first()
                    if speciality:
                        self.initial.setdefault(field_name, speciality)

    def clean(self):
        cleaned_data = super().clean()
        bac_etablissement_existant = cleaned_data.get('bac_etablissement_existant')
        bac_etablissement = (cleaned_data.get('bac_etablissement') or '').strip()

        cleaned_data['bac_etablissement'] = (
            bac_etablissement_existant.name if bac_etablissement_existant else bac_etablissement
        )
        cleaned_data['school'] = bac_etablissement_existant

        programme = cleaned_data.get('program')
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
                    "La spécialité sélectionnée doit appartenir au programme choisi.",
                )
                continue

            if not specialite:
                continue

            if specialite.pk in selected_specialities:
                self.add_error(field_name, "Veuillez choisir une spécialité différente pour chaque choix.")
                continue

            selected_specialities.append(specialite.pk)

        return cleaned_data

    def save(self, commit=True):
        previous_photo = None
        if self.instance.pk:
            previous_photo = Student.objects.get(pk=self.instance.pk).profile_photo

        uploaded_photo = self.files.get('profile_photo')
        should_remove_photo = self.cleaned_data.get('remove_profile_photo') and not uploaded_photo

        student = super().save(commit=False)

        school = self.cleaned_data.get('bac_etablissement_existant')
        if not school:
            school_name = (self.cleaned_data.get('bac_etablissement') or '').strip()
            if school_name:
                school = School.objects.filter(name__iexact=school_name, level='secondary').first()
                if not school:
                    school = School.objects.create(name=school_name, level='secondary')

        student.school = school
        student.specialite_souhaitee_1 = (
            self.cleaned_data['specialite_souhaitee_1'].name
            if self.cleaned_data.get('specialite_souhaitee_1') else ''
        )
        student.specialite_souhaitee_2 = (
            self.cleaned_data['specialite_souhaitee_2'].name
            if self.cleaned_data.get('specialite_souhaitee_2') else ''
        )
        student.specialite_souhaitee_3 = (
            self.cleaned_data['specialite_souhaitee_3'].name
            if self.cleaned_data.get('specialite_souhaitee_3') else ''
        )

        if should_remove_photo:
            student.profile_photo = None

        if commit:
            student.save()
            self.save_m2m()

            previous_photo_name = getattr(previous_photo, 'name', '')
            current_photo_name = getattr(student.profile_photo, 'name', '')

            if should_remove_photo and previous_photo_name:
                previous_photo.storage.delete(previous_photo_name)
            elif uploaded_photo and previous_photo_name and previous_photo_name != current_photo_name:
                previous_photo.storage.delete(previous_photo_name)

        return student


class StudentMetaDataEditForm(forms.ModelForm):
    """Formulaire de modification des métadonnées de l'étudiant"""

    remove_preuve_baccalaureat = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_acte_naissance = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_certificat_nationalite = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_releve_notes_last_class = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_justificatif_dernier_diplome = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_bulletins_terminale = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_decharge_equivalence = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_releve_notes_master1 = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    remove_photocopie_bts_hnd = forms.BooleanField(
        required=False,
        label='Supprimer le document actuel',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    removable_file_fields = [
        'preuve_baccalaureat',
        'acte_naissance',
        'certificat_nationalite',
        'releve_notes_last_class',
        'justificatif_dernier_diplome',
        'decharge_equivalence',
        'bulletins_terminale',
        'releve_notes_master1',
        'photocopie_bts_hnd',
    ]

    class Meta:
        model = StudentMetaData
        fields = [
            'mother_full_name', 'mother_live_city', 'mother_email',
            'mother_occupation', 'mother_phone_number', 'father_full_name',
            'father_live_city', 'father_email',
            'father_occupation', 'father_phone_number', 'original_country',
            'original_region', 'original_department', 'original_district',
            'residence_city', 'residence_quarter', 'is_complete',
            'preuve_baccalaureat', 'acte_naissance', 'certificat_nationalite', 'releve_notes_last_class',
            'justificatif_dernier_diplome', 'decharge_equivalence', 'bulletins_terminale',
            'releve_notes_master1', 'photocopie_bts_hnd'
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
            'father_live_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville de résidence du père'
            }),
            'father_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email du père'
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
            'certificat_nationalite': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'releve_notes_last_class': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'justificatif_dernier_diplome': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'decharge_equivalence': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'bulletins_terminale': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'releve_notes_master1': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.png,.jpg,.jpeg,.pdf'
            }),
            'photocopie_bts_hnd': forms.FileInput(attrs={
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
            'father_live_city': 'Ville de résidence du père',
            'father_email': 'Email du père',
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
            'certificat_nationalite': 'Certificat de nationalité',
            'releve_notes_last_class': 'Relevé de notes de la dernière classe fréquentée',
            'justificatif_dernier_diplome': 'Justificatif du dernier diplôme obtenu',
            'decharge_equivalence': 'Décharge de la demande d\'équivalence',
            'bulletins_terminale': 'Bulletins de la classe de terminale',
            'releve_notes_master1': 'Relevé de notes du Master 1',
            'photocopie_bts_hnd': 'Photocopie du BTS, HND ou diplôme équivalent',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre tous les champs optionnels sauf le pays d'origine
        for field_name, field in self.fields.items():
            if field_name != 'original_country':
                field.required = False

        for field_name in self.removable_file_fields:
            if field_name in self.fields:
                self.fields[field_name].validators.append(validate_file_size)

        for field_name in ('mother_phone_number', 'father_phone_number'):
            if field_name in self.fields:
                self.fields[field_name].validators.append(validate_phone_number)

        for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
            if field_name not in self.fields:
                continue

            document_definition = PROGRAM_DOCUMENTS_BY_FIELD[field_name]
            self.fields[field_name].label = document_definition['label']
            self.fields[field_name].help_text = document_definition['help_text']

    def save(self, commit=True):
        previous_files = {}
        if self.instance.pk:
            previous_instance = StudentMetaData.objects.get(pk=self.instance.pk)
            previous_files = {
                field_name: getattr(previous_instance, field_name)
                for field_name in self.removable_file_fields
            }

        uploaded_files = {
            field_name: self.files.get(field_name)
            for field_name in self.removable_file_fields
        }
        removal_flags = {
            field_name: bool(self.cleaned_data.get(f'remove_{field_name}')) and not uploaded_files[field_name]
            for field_name in self.removable_file_fields
        }

        metadata = super().save(commit=False)

        for field_name, should_remove in removal_flags.items():
            if should_remove:
                setattr(metadata, field_name, None)

        if commit:
            metadata.save()
            self.save_m2m()

            for field_name in self.removable_file_fields:
                previous_file = previous_files.get(field_name)
                previous_file_name = getattr(previous_file, 'name', '')
                current_file = getattr(metadata, field_name)
                current_file_name = getattr(current_file, 'name', '')

                if removal_flags[field_name] and previous_file_name:
                    previous_file.storage.delete(previous_file_name)
                elif uploaded_files[field_name] and previous_file_name and previous_file_name != current_file_name:
                    previous_file.storage.delete(previous_file_name)

        return metadata
