from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import re
from .models import Classroom, TimeSlot, CourseSession, Schedule, LecturerAvailability, ScheduleSession
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear


class ClassroomForm(forms.ModelForm):
    """
    Formulaire pour la création et modification des salles de classe
    """
    
    class Meta:
        model = Classroom
        fields = ['code', 'name', 'capacity', 'building', 'floor', 'equipment', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A101, B205...',
                'maxlength': 20
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salle A101, Amphithéâtre...',
                'maxlength': 100
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de places',
                'min': 1,
                'max': 1000
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bâtiment A, Bloc principal...',
                'maxlength': 100
            }),
            'floor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1er étage, RDC, Sous-sol...',
                'maxlength': 20
            }),
            'equipment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Décrivez les équipements disponibles (projecteur, tableau interactif, climatisation...)',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'code': 'Code de la salle *',
            'name': 'Nom de la salle *',
            'capacity': 'Capacité *',
            'building': 'Bâtiment',
            'floor': 'Étage',
            'equipment': 'Équipements disponibles',
            'is_active': 'Salle active'
        }
        help_texts = {
            'code': 'Code unique pour identifier la salle',
            'name': 'Nom descriptif de la salle',
            'capacity': 'Nombre maximum de personnes pouvant être accueillies',
            'building': 'Nom ou référence du bâtiment',
            'floor': 'Étage où se trouve la salle',
            'equipment': 'Liste des équipements et matériels disponibles',
            'is_active': 'Décochez pour désactiver temporairement la salle'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marquer les champs obligatoires
        for field_name in ['code', 'name', 'capacity']:
            self.fields[field_name].required = True
        
        # Validation personnalisée pour la capacité
        self.fields['capacity'].validators = [
            MinValueValidator(1, message="La capacité doit être d'au moins 1 personne"),
            MaxValueValidator(1000, message="La capacité ne peut pas dépasser 1000 personnes")
        ]

    def clean_code(self):
        """Validation personnalisée pour le code de la salle"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # Vérifier l'unicité du code (sauf pour la modification)
            existing = Classroom.objects.filter(code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Une salle avec ce code existe déjà.")
        return code

    def clean_capacity(self):
        """Validation personnalisée pour la capacité"""
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("La capacité doit être d'au moins 1 personne.")
        return capacity

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        name = cleaned_data.get('name')
        
        # Vérifier que le nom n'est pas vide si fourni
        if name and not name.strip():
            self.add_error('name', "Le nom de la salle ne peut pas être vide.")
        
        return cleaned_data

    def save(self, commit=True):
        """Sauvegarde personnalisée"""
        classroom = super().save(commit=False)
        
        # Normaliser le code en majuscules
        if classroom.code:
            classroom.code = classroom.code.upper().strip()
        
        # Nettoyer le nom
        if classroom.name:
            classroom.name = classroom.name.strip()
        
        if commit:
            classroom.save()
        return classroom


class ClassroomSearchForm(forms.Form):
    """
    Formulaire de recherche et filtrage des salles de classe
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par code, nom ou bâtiment...'
        }),
        label='Recherche'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous les statuts'),
            ('active', 'Actives'),
            ('inactive', 'Inactives')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Statut'
    )
    
    building = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrer par bâtiment...'
        }),
        label='Bâtiment'
    )
    
    min_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Capacité minimum',
            'min': 1
        }),
        label='Capacité minimum'
    )
    
    max_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Capacité maximum',
            'min': 1
        }),
        label='Capacité maximum'
    )

    def clean(self):
        """Validation du formulaire de recherche"""
        cleaned_data = super().clean()
        min_capacity = cleaned_data.get('min_capacity')
        max_capacity = cleaned_data.get('max_capacity')
        
        if min_capacity and max_capacity and min_capacity > max_capacity:
            raise forms.ValidationError(
                "La capacité minimum ne peut pas être supérieure à la capacité maximum."
            )
        
        return cleaned_data


class LecturerForm(forms.ModelForm):
    """
    Formulaire pour la création et modification des enseignants
    """

    class Meta:
        model = Lecturer
        fields = ['matricule', 'firstname', 'lastname', 'date_naiss', 'grade', 'gender', 'lang', 'phone_number', 'email']
        widgets = {
            'matricule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: ENS001, PROF123...',
                'maxlength': 50
            }),
            'firstname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom de l\'enseignant',
                'maxlength': 100
            }),
            'lastname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de famille de l\'enseignant',
                'maxlength': 100
            }),
            'date_naiss': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Professeur, Maître de conférences, Docteur...',
                'maxlength': 50
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lang': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +237 6XX XXX XXX',
                'maxlength': 20
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            })
        }
        labels = {
            'matricule': 'Matricule *',
            'firstname': 'Prénom *',
            'lastname': 'Nom de famille *',
            'date_naiss': 'Date de naissance *',
            'grade': 'Grade/Titre *',
            'gender': 'Genre *',
            'lang': 'Langue de préférence',
            'phone_number': 'Numéro de téléphone',
            'email': 'Adresse email'
        }
        help_texts = {
            'matricule': 'Identifiant unique de l\'enseignant',
            'firstname': 'Prénom de l\'enseignant',
            'lastname': 'Nom de famille de l\'enseignant',
            'date_naiss': 'Date de naissance de l\'enseignant',
            'grade': 'Grade académique ou titre professionnel',
            'gender': 'Genre de l\'enseignant',
            'lang': 'Langue de préférence pour les communications',
            'phone_number': 'Numéro de téléphone (optionnel)',
            'email': 'Adresse email professionnelle (optionnel)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Marquer les champs obligatoires
        required_fields = ['matricule', 'firstname', 'lastname', 'date_naiss', 'grade', 'gender']
        for field_name in required_fields:
            self.fields[field_name].required = True

        # Définir les choix pour les champs de sélection
        self.fields['gender'].choices = [('', 'Sélectionner...')] + list(Lecturer._meta.get_field('gender').choices)
        self.fields['lang'].choices = [('', 'Sélectionner...'), ('fr', 'Français'), ('en', 'Anglais')]
        self.fields['lang'].initial = 'fr'

    def clean_matricule(self):
        """Validation personnalisée pour le matricule"""
        matricule = self.cleaned_data.get('matricule')
        if matricule:
            matricule = matricule.upper().strip()

            # Vérifier le format (lettres et chiffres uniquement)
            if not re.match(r'^[A-Z0-9]+$', matricule):
                raise ValidationError("Le matricule ne doit contenir que des lettres et des chiffres.")

            # Vérifier l'unicité du matricule (sauf pour la modification)
            existing = Lecturer.objects.filter(matricule=matricule)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("Un enseignant avec ce matricule existe déjà.")

        return matricule

    def clean_email(self):
        """Validation personnalisée pour l'email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()

            # Vérifier l'unicité de l'email (sauf pour la modification)
            existing = Lecturer.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("Un enseignant avec cette adresse email existe déjà.")

        return email

    def clean_phone_number(self):
        """Validation personnalisée pour le numéro de téléphone"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.strip()

            # Supprimer les espaces et caractères spéciaux pour la validation
            phone_digits = re.sub(r'[^\d+]', '', phone)

            # Vérifier le format basique
            if not re.match(r'^\+?[\d\s\-\(\)]{8,20}$', phone):
                raise ValidationError("Format de numéro de téléphone invalide.")

        return phone

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        firstname = cleaned_data.get('firstname')
        lastname = cleaned_data.get('lastname')

        # Vérifier que les noms ne sont pas vides
        if firstname and not firstname.strip():
            self.add_error('firstname', "Le prénom ne peut pas être vide.")

        if lastname and not lastname.strip():
            self.add_error('lastname', "Le nom de famille ne peut pas être vide.")

        return cleaned_data

    def save(self, commit=True):
        """Sauvegarde personnalisée"""
        lecturer = super().save(commit=False)

        # Normaliser les données
        if lecturer.matricule:
            lecturer.matricule = lecturer.matricule.upper().strip()

        if lecturer.firstname:
            lecturer.firstname = lecturer.firstname.strip().title()

        if lecturer.lastname:
            lecturer.lastname = lecturer.lastname.strip().upper()

        if lecturer.email:
            lecturer.email = lecturer.email.lower().strip()

        if commit:
            lecturer.save()
        return lecturer


class LecturerSearchForm(forms.Form):
    """
    Formulaire de recherche et filtrage des enseignants
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par matricule, nom, prénom ou email...'
        }),
        label='Recherche'
    )

    grade = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrer par grade...'
        }),
        label='Grade'
    )

    gender = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous les genres'),
            ('M', 'Masculin'),
            ('F', 'Féminin')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Genre'
    )

    lang = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Toutes les langues'),
            ('fr', 'Français'),
            ('en', 'Anglais')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Langue'
    )


class ScheduleForm(forms.ModelForm):
    """
    Formulaire pour la création et modification des emplois du temps
    """

    class Meta:
        model = Schedule
        fields = ['name', 'description', 'academic_year', 'level', 'start_date', 'end_date', 'duration_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Emploi du temps Licence 1 - Semestre 1',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description de l\'emploi du temps (optionnel)',
                'rows': 3
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duration_type': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Nom de l\'emploi du temps *',
            'description': 'Description',
            'academic_year': 'Année académique *',
            'level': 'Niveau *',
            'start_date': 'Date de début *',
            'end_date': 'Date de fin *',
            'duration_type': 'Type de durée *'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les années académiques actives
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)

        # Marquer les champs obligatoires
        required_fields = ['name', 'academic_year', 'level', 'start_date', 'end_date', 'duration_type']
        for field_name in required_fields:
            self.fields[field_name].required = True

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        academic_year = cleaned_data.get('academic_year')
        name = cleaned_data.get('name')
        level = cleaned_data.get('level')

        # Vérifier les dates
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")

            # Vérifier que les dates sont dans l'année académique
            if academic_year:
                if (start_date < academic_year.start_at or end_date > academic_year.end_at):
                    raise ValidationError(
                        f"Les dates doivent être comprises dans l'année académique "
                        f"({academic_year.start_at} - {academic_year.end_at})."
                    )

        # Vérifier l'unicité du nom pour l'année académique et le niveau
        if name and academic_year and level:
            existing = Schedule.objects.filter(
                name=name,
                academic_year=academic_year,
                level=level
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    "Un emploi du temps avec ce nom existe déjà pour cette année académique et ce niveau."
                )

        return cleaned_data


class LecturerAvailabilityForm(forms.ModelForm):
    """
    Formulaire pour la gestion de la disponibilité des enseignants
    """

    class Meta:
        model = LecturerAvailability
        fields = ['lecturer', 'time_slot', 'academic_year', 'status', 'start_date', 'end_date', 'notes']
        widgets = {
            'lecturer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'time_slot': forms.Select(attrs={
                'class': 'form-control'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Notes sur la disponibilité (optionnel)',
                'rows': 3
            })
        }
        labels = {
            'lecturer': 'Enseignant *',
            'time_slot': 'Créneau horaire *',
            'academic_year': 'Année académique *',
            'status': 'Statut de disponibilité *',
            'start_date': 'Date de début',
            'end_date': 'Date de fin',
            'notes': 'Notes'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les années académiques actives
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)

        # Filtrer les créneaux actifs du lundi au vendredi
        self.fields['time_slot'].queryset = TimeSlot.objects.filter(
            is_active=True,
            day_of_week__in=['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        ).order_by('day_of_week', 'start_time')

        # Marquer les champs obligatoires
        required_fields = ['lecturer', 'time_slot', 'academic_year', 'status']
        for field_name in required_fields:
            self.fields[field_name].required = True

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        lecturer = cleaned_data.get('lecturer')
        time_slot = cleaned_data.get('time_slot')
        academic_year = cleaned_data.get('academic_year')

        # Vérifier les dates si elles sont fournies
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")

            # Vérifier que les dates sont dans l'année académique
            if academic_year:
                if (start_date < academic_year.start_at or end_date > academic_year.end_at):
                    raise ValidationError(
                        f"Les dates doivent être comprises dans l'année académique "
                        f"({academic_year.start_at} - {academic_year.end_at})."
                    )

        return cleaned_data


class ScheduleGenerationForm(forms.Form):
    """
    Formulaire pour la génération automatique d'emploi du temps
    """
    schedule = forms.ModelChoiceField(
        queryset=Schedule.objects.filter(status='draft'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Emploi du temps *',
        help_text='Sélectionnez l\'emploi du temps à générer'
    )

    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Cours à inclure *',
        help_text='Sélectionnez les cours à inclure dans l\'emploi du temps'
    )

    sessions_per_week = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10
        }),
        label='Séances par semaine et par cours *',
        help_text='Nombre de séances par semaine pour chaque cours'
    )

    prefer_morning = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Privilégier les créneaux du matin',
        help_text='Donner la priorité aux créneaux du matin lors de la génération'
    )

    avoid_consecutive_sessions = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Éviter les séances consécutives',
        help_text='Éviter de programmer des séances consécutives pour le même cours'
    )

    max_daily_sessions = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 8
        }),
        label='Maximum de séances par jour *',
        help_text='Nombre maximum de séances par jour'
    )

    def __init__(self, *args, **kwargs):
        level = kwargs.pop('level', None)
        super().__init__(*args, **kwargs)

        if level:
            # Filtrer les cours par niveau
            self.fields['courses'].queryset = Course.objects.filter(level=level)

            # Filtrer les emplois du temps par niveau
            self.fields['schedule'].queryset = Schedule.objects.filter(
                level=level,
                status='draft'
            )

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        schedule = cleaned_data.get('schedule')
        courses = cleaned_data.get('courses')
        sessions_per_week = cleaned_data.get('sessions_per_week')
        max_daily_sessions = cleaned_data.get('max_daily_sessions')

        if schedule and courses:
            # Vérifier que les cours correspondent au niveau de l'emploi du temps
            invalid_courses = courses.exclude(level=schedule.level)
            if invalid_courses.exists():
                raise ValidationError(
                    f"Les cours suivants ne correspondent pas au niveau {schedule.level.name}: "
                    f"{', '.join([course.label for course in invalid_courses])}"
                )

        # Vérifier la cohérence des paramètres
        if sessions_per_week and max_daily_sessions:
            total_weekly_sessions = len(courses or []) * sessions_per_week
            max_weekly_capacity = max_daily_sessions * 5  # 5 jours de cours

            if total_weekly_sessions > max_weekly_capacity:
                raise ValidationError(
                    f"Impossible de programmer {total_weekly_sessions} séances par semaine "
                    f"avec un maximum de {max_daily_sessions} séances par jour. "
                    f"Capacité maximale: {max_weekly_capacity} séances par semaine."
                )

        return cleaned_data


class TimeSlotForm(forms.ModelForm):
    """
    Formulaire pour la création et modification des créneaux horaires
    """

    class Meta:
        model = TimeSlot
        fields = ['name', 'day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Matin 1, Après-midi 2...',
                'maxlength': 100
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Nom du créneau *',
            'day_of_week': 'Jour de la semaine *',
            'start_time': 'Heure de début *',
            'end_time': 'Heure de fin *',
            'is_active': 'Créneau actif'
        }
        help_texts = {
            'name': 'Nom descriptif du créneau horaire',
            'day_of_week': 'Jour de la semaine pour ce créneau',
            'start_time': 'Heure de début du créneau',
            'end_time': 'Heure de fin du créneau',
            'is_active': 'Décochez pour désactiver temporairement ce créneau'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Marquer les champs obligatoires
        required_fields = ['name', 'day_of_week', 'start_time', 'end_time']
        for field_name in required_fields:
            self.fields[field_name].required = True

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day_of_week = cleaned_data.get('day_of_week')
        name = cleaned_data.get('name')

        # Vérifier que l'heure de fin est après l'heure de début
        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError("L'heure de fin doit être postérieure à l'heure de début.")

            # Vérifier la durée minimale (30 minutes)
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)
            duration = end_datetime - start_datetime

            if duration < timedelta(minutes=30):
                raise ValidationError("La durée minimale d'un créneau est de 30 minutes.")

            if duration > timedelta(hours=8):
                raise ValidationError("La durée maximale d'un créneau est de 8 heures.")

        # Vérifier l'unicité du créneau (jour + heures)
        if day_of_week and start_time and end_time:
            existing = TimeSlot.objects.filter(
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    f"Un créneau avec ces horaires existe déjà pour {dict(TimeSlot.DAYS_OF_WEEK)[day_of_week]}."
                )

        return cleaned_data

    def clean_name(self):
        """Validation du nom du créneau"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise ValidationError("Le nom du créneau doit contenir au moins 3 caractères.")
        return name


class TimeSlotSearchForm(forms.Form):
    """
    Formulaire de recherche et filtrage des créneaux horaires
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        }),
        label='Recherche'
    )

    day_of_week = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les jours')] + TimeSlot.DAYS_OF_WEEK,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Jour de la semaine'
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous les statuts'),
            ('active', 'Actifs'),
            ('inactive', 'Inactifs')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Statut'
    )

    time_period = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Toutes les périodes'),
            ('morning', 'Matin (6h-12h)'),
            ('afternoon', 'Après-midi (12h-18h)'),
            ('evening', 'Soir (18h-22h)')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Période'
    )


class CourseSessionForm(forms.ModelForm):
    """
    Formulaire pour la création et modification des séances de cours
    """

    class Meta:
        model = CourseSession
        fields = [
            'course', 'lecturer', 'classroom', 'time_slot', 'level',
            'academic_year', 'date', 'session_type', 'status',
            'duration_hours', 'topic', 'notes'
        ]
        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lecturer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'classroom': forms.Select(attrs={
                'class': 'form-control'
            }),
            'time_slot': forms.Select(attrs={
                'class': 'form-control'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'session_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.5',
                'max': '8.0'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sujet ou chapitre de la séance (optionnel)',
                'maxlength': 200
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Notes additionnelles (optionnel)',
                'rows': 3
            })
        }
        labels = {
            'course': 'Cours *',
            'lecturer': 'Enseignant *',
            'classroom': 'Salle de classe *',
            'time_slot': 'Créneau horaire *',
            'level': 'Niveau *',
            'academic_year': 'Année académique *',
            'date': 'Date de la séance *',
            'session_type': 'Type de séance *',
            'status': 'Statut *',
            'duration_hours': 'Durée (heures) *',
            'topic': 'Sujet/Chapitre',
            'notes': 'Notes'
        }
        help_texts = {
            'course': 'Cours à enseigner',
            'lecturer': 'Enseignant responsable de la séance',
            'classroom': 'Salle où se déroulera la séance',
            'time_slot': 'Créneau horaire de la séance',
            'level': 'Niveau des étudiants',
            'academic_year': 'Année académique',
            'date': 'Date de la séance',
            'session_type': 'Type de séance (cours, TD, TP, etc.)',
            'status': 'Statut actuel de la séance',
            'duration_hours': 'Durée de la séance en heures',
            'topic': 'Sujet ou chapitre traité (optionnel)',
            'notes': 'Notes ou remarques additionnelles (optionnel)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Marquer les champs obligatoires
        required_fields = [
            'course', 'lecturer', 'classroom', 'time_slot',
            'level', 'academic_year', 'date', 'session_type',
            'status', 'duration_hours'
        ]
        for field_name in required_fields:
            self.fields[field_name].required = True

        # Filtrer les données par année académique active par défaut
        current_year = AcademicYear.objects.filter(is_active=True).first()
        if current_year:
            self.fields['academic_year'].initial = current_year

        # Ordonner les choix
        self.fields['course'].queryset = Course.objects.all().order_by('label')
        self.fields['lecturer'].queryset = Lecturer.objects.all().order_by('lastname', 'firstname')
        self.fields['classroom'].queryset = Classroom.objects.filter(is_active=True).order_by('code')
        self.fields['time_slot'].queryset = TimeSlot.objects.filter(is_active=True).order_by('day_of_week', 'start_time')
        self.fields['level'].queryset = Level.objects.all().order_by('name')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        level = cleaned_data.get('level')
        classroom = cleaned_data.get('classroom')
        time_slot = cleaned_data.get('time_slot')
        date = cleaned_data.get('date')
        academic_year = cleaned_data.get('academic_year')

        # Vérifier que le cours correspond au niveau
        if course and level and course.level != level:
            raise ValidationError(
                f"Le cours '{course.label}' n'est pas disponible pour le niveau '{level.name}'. "
                f"Ce cours est destiné au niveau '{course.level.name}'."
            )

        # Vérifier que la date est dans l'année académique
        if date and academic_year:
            if date < academic_year.start_at or date > academic_year.end_at:
                raise ValidationError(
                    f"La date doit être comprise entre {academic_year.start_at.strftime('%d/%m/%Y')} "
                    f"et {academic_year.end_at.strftime('%d/%m/%Y')} (année académique {academic_year.name})."
                )

        # Vérifier la disponibilité de la salle (pas de conflit)
        if classroom and time_slot and date:
            existing_session = CourseSession.objects.filter(
                classroom=classroom,
                time_slot=time_slot,
                date=date
            )
            if self.instance.pk:
                existing_session = existing_session.exclude(pk=self.instance.pk)

            if existing_session.exists():
                session = existing_session.first()
                raise ValidationError(
                    f"La salle '{classroom.name}' est déjà occupée le {date.strftime('%d/%m/%Y')} "
                    f"de {time_slot.start_time.strftime('%H:%M')} à {time_slot.end_time.strftime('%H:%M')} "
                    f"par le cours '{session.course.label}'."
                )

        return cleaned_data

    def clean_date(self):
        """Validation de la date"""
        date = self.cleaned_data.get('date')
        if date:
            from datetime import date as date_class
            if date < date_class.today():
                raise ValidationError("La date de la séance ne peut pas être dans le passé.")
        return date
