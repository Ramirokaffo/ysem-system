from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone
from students.models import Student
from academic.models import Course, Level, AcademicYear
from datetime import datetime




class Lecturer(models.Model):
    """
    Modèle pour les enseignants
    """

    DIPLOMAS_CHOICES = [
        ('Licence', 'Licence'),
        ('Master', 'Master'),
        ('Doctorat', 'Doctorat'),
    ]
    LECTURERS_STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente de validation'),
        ('hired', 'Recruté'),
        ('refused', 'Refusé'),
        ('licensed', 'Licencié'),
        ('resigned', 'Démissionnaire'),
    ]

    matricule = models.CharField(blank=True, unique=True, primary_key=True, max_length=50, verbose_name="Matricule")
    firstname = models.CharField(blank=True, null=True, max_length=100, verbose_name="Prénom")
    lastname = models.CharField(blank=True, null=True, max_length=100, verbose_name="Nom de famille")
    date_naiss = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    place_of_birth = models.CharField(blank=True, null=True, max_length=100, verbose_name="Lieu de naissance")
    grade = models.CharField(blank=True, null=True, max_length=50, verbose_name="Grade/Titre")
    gender = models.CharField(blank=True, null=True, max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name="Genre")
    lang = models.CharField(blank=True, null=True, max_length=50, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')   
    phone_number = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de téléphone")
    phone_number_2 = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de téléphone secondaire")
    email = models.EmailField(blank=True, null=True, verbose_name="Adresse email")
    nationality = models.CharField(blank=True, null=True, max_length=50, verbose_name="Nationalité")
    number_of_dependent_children = models.IntegerField(blank=True, null=True, verbose_name="Nombre d'enfants à charge")
    marital_status = models.CharField(blank=True, null=True, max_length=20, choices=[('single', 'Célibataire'), ('married', 'Marié(e)'), ('divorced', 'Divorcé(e)'), ('widowed', 'Veuf/Veuve')], verbose_name="Statut marital")
    has_health_problem = models.BooleanField(default=False, verbose_name="Avez-vous des problèmes de santé?")
    health_problem_description = models.TextField(blank=True, null=True, verbose_name="Description des problèmes de santé")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse de résidence")

    nic = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro de CNI")
    niu = models.CharField(blank=True, null=True, max_length=20, verbose_name="Numéro d'Identification Unique")
    
    emergency_contact_name = models.CharField(blank=True, null=True, max_length=100, verbose_name="Contact d'urgence - Nom")
    emergency_contact_phone = models.CharField(blank=True, null=True, max_length=20, verbose_name="Contact d'urgence - Téléphone")
    emergency_contact_email = models.EmailField(blank=True, null=True, verbose_name="Contact d'urgence - Email")
    emergency_contact_relationship = models.CharField(blank=True, null=True, max_length=50, verbose_name="Contact d'urgence - Relation")
    photo = models.ImageField(upload_to='lecturers/photos/', blank=True, null=True, verbose_name="Photo de profil")
    signature = models.ImageField(upload_to='lecturers/signatures/', blank=True, null=True, verbose_name="Signature")

    cv = models.FileField(upload_to='lecturers/cvs/', blank=True, null=True, verbose_name="Curriculum Vitae")

    highest_diploma_obtained = models.CharField(blank=True, null=True, max_length=100, verbose_name="Dernier diplôme obtenu", choices=DIPLOMAS_CHOICES)

    is_permanent = models.BooleanField(default=False, verbose_name="Enseignant permanent ?")
    status = models.CharField(max_length=20, choices=LECTURERS_STATUS_CHOICES, default='draft', verbose_name="Statut du dossier")

    # Champs pour l'authentification du portail enseignant
    external_password_hash = models.CharField(max_length=128, blank=True, null=True, verbose_name="Mot de passe (portail enseignant)")
    external_password_created_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de création du mot de passe")
    email_verified = models.BooleanField(default=False, verbose_name="Email vérifié")
    email_verified_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de vérification de l'email")
    last_login_date = models.DateTimeField(blank=True, null=True, verbose_name="Date dernière connexion")

    # Suivi du wizard de recrutement
    recruitment_step = models.PositiveSmallIntegerField(default=0, verbose_name="Dernière étape de recrutement complétée")
    recruitment_submitted = models.BooleanField(default=False, verbose_name="Dossier de candidature soumis")
    recruitment_submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de soumission du dossier")

    def save(self, *args, **kwargs):
        # Générer automatiquement le matricule si ce n'est pas déjà fait
        if not self.matricule:
            self.auto_generate_matricule()
        super().save(*args, **kwargs)

    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    def auto_generate_matricule(self):
        """Génère automatiquement un matricule unique pour l'enseignant"""
        if not self.matricule:
            prefix = "LEC"
            last_lecturer = Lecturer.objects.order_by('-matricule').first()
            if last_lecturer and last_lecturer.matricule.startswith(prefix):
                # Ignorer le préfixe et l'année
                last_number = int(last_lecturer.matricule[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            # Ajouter l'année en cours pour garantir l'unicité
            today = datetime.today()
            self.matricule = f"{prefix}{today.year}{new_number:04d}"

    def set_external_password(self, password):
        """Définit le mot de passe utilisé pour le portail enseignant."""
        self.external_password_hash = make_password(password)
        self.external_password_created_at = timezone.now()
        self.save(update_fields=[
            'external_password_hash',
            'external_password_created_at',
        ])

    def check_external_password(self, password):
        """Vérifie le mot de passe du portail enseignant."""
        if not self.external_password_hash:
            return False
        return check_password(password, self.external_password_hash)

    def has_external_password(self):
        return bool(self.external_password_hash)

    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ['lastname', 'firstname']



