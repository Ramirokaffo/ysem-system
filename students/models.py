from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import BaseUser, Godfather
from academic.models import AcademicYear, Level, Program
from schools.models import School
import secrets
import string


class StudentMetaData(models.Model):
    """
    Métadonnées pour les étudiants (informations complémentaires)
    """
    mother_full_name = models.CharField(max_length=100, blank=True, null=True)
    mother_live_city = models.CharField(max_length=100, blank=True, null=True)
    mother_email = models.EmailField(blank=True, null=True)
    mother_occupation = models.CharField(max_length=200, blank=True, null=True)
    mother_phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    father_full_name = models.CharField(max_length=100, blank=True, null=True)
    father_live_city = models.CharField(max_length=100, blank=True, null=True)
    father_email = models.EmailField(blank=True, null=True)
    father_occupation = models.CharField(max_length=200, blank=True, null=True)
    father_phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    original_country = models.CharField(max_length=100)
    original_region = models.CharField(max_length=100, blank=True, null=True)
    original_department = models.CharField(max_length=100, blank=True, null=True)
    original_district = models.CharField(max_length=100, blank=True, null=True)
    residence_city = models.CharField(max_length=100, blank=True, null=True)
    residence_quarter = models.CharField(max_length=100, blank=True, null=True)
    
    is_complete = models.BooleanField(default=True, verbose_name="Dossier complet")

    # Documents d'inscription obligatoires
    preuve_baccalaureat = models.FileField(
        upload_to='documents/inscription/baccalaureat/',
        blank=True,
        null=True,
        verbose_name="Preuve d'obtention du baccalauréat",
        help_text="Copie du document attestant la réussite du baccalauréat ou équivalent (PNG/JPG/PDF, max 5Mo)"
    )

    acte_naissance = models.FileField(
        upload_to='documents/inscription/acte_naissance/',
        blank=True,
        null=True,
        verbose_name="Photocopie certifiée de l'acte de naissance",
        help_text="Photocopie certifiée conforme de l'acte de naissance (PNG/JPG/PDF, max 5Mo)"
    )

    releve_notes_bac = models.FileField(
        upload_to='documents/inscription/releve_notes/',
        blank=True,
        null=True,
        verbose_name="Relevé des notes du Baccalauréat",
        help_text="Photocopie certifiée conforme du relevé des notes du baccalauréat (PNG/JPG/PDF, max 5Mo)"
    )

    bulletins_terminale = models.FileField(
        upload_to='documents/inscription/bulletins/',
        blank=True,
        null=True,
        verbose_name="Bulletins de la classe de terminale",
        help_text="Photocopie des bulletins de notes de la classe de terminale (PNG/JPG/PDF, max 5Mo)"
    )

    def __str__(self):
        return f"Métadonnées - {self.mother_full_name} / {self.father_full_name} ({self.original_country})"

    class Meta:
        verbose_name = "Métadonnées Étudiant"
        verbose_name_plural = "Métadonnées Étudiants"


class Student(models.Model):
    """
    Modèle principal pour les étudiants
    """
    matricule = models.CharField(max_length=50, primary_key=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    date_naiss = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    status = models.CharField(max_length=50, choices=[('pending', 'En attente'), ('approved', 'Approuvée'), ('abandoned', 'abandonné'), ('rejected', 'Rejetée')])
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    lang = models.CharField(max_length=50, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Relations
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True, verbose_name="Date d'inscription")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    # Champ pour l'authentification externe des étudiants
    external_password_hash = models.CharField(max_length=128, blank=True, null=True, verbose_name="Mot de passe pour consultation externe")
    external_password_created_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de création du mot de passe")

    def __str__(self):
        return f"{self.matricule} - {self.firstname} {self.lastname}"

    def generate_external_password(self):
        """
        Génère un mot de passe aléatoire pour l'accès externe de l'étudiant
        Retourne le mot de passe en clair (à communiquer à l'étudiant)
        """
        # Génère un mot de passe de 8 caractères avec lettres et chiffres
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))

        # Hash et sauvegarde le mot de passe
        self.external_password_hash = make_password(password)
        from django.utils import timezone
        self.external_password_created_at = timezone.now()
        self.save()

        return password

    def check_external_password(self, password):
        """
        Vérifie si le mot de passe fourni correspond au mot de passe externe de l'étudiant
        """
        if not self.external_password_hash:
            return False
        return check_password(password, self.external_password_hash)

    def has_external_password(self):
        """
        Vérifie si l'étudiant a un mot de passe externe configuré
        """
        return bool(self.external_password_hash)

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"


class StudentLevel(models.Model):
    """
    Modèle pour associer les étudiants aux niveaux (relation many-to-many avec attributs)
    """
    name = models.CharField(max_length=100, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_levels')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='student_levels')
    academic_year = models.ForeignKey(AcademicYear, null=True, on_delete=models.CASCADE, related_name='student_levels')
    is_active = models.BooleanField(default=False, verbose_name="Niveau actuel de l'étudiant?")

    def save(self, *args, **kwargs):
        # Met à jour le champ name avant de sauvegarder
        level_name = self.level.name if self.level else ''
        year_name = self.academic_year.name if self.academic_year else ''
        self.name = f"{level_name} - {year_name}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.matricule} - {self.level.name} - {self.academic_year.name}"

    class Meta:
        verbose_name = "Niveau Étudiant"
        verbose_name_plural = "Niveaux Étudiants"
        unique_together = ['student', 'level', 'academic_year']



class OfficialDocument(models.Model):
    """
    Modèle pour les documents officiels des étudiants
    """
    student_level = models.ForeignKey(StudentLevel, on_delete=models.CASCADE, null=True, related_name='official_documents')
    type = models.CharField(max_length=100, choices=[("student_card", "Carte d'étudiant"), ("transcript", "Relevé de notes"), ("diploma", "Diplôme"), ("certificate", "Certificat de scolarité")])
    status = models.CharField(max_length=50, choices=[('available', 'Non déchargé'), ('withdrawn', 'Déchargé'), ('lost', 'Perdu')], default='available')
    withdrawn_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {str(self.student_level)}"

    class Meta:
        verbose_name = "documents officiel"
        verbose_name_plural = "documents officiels"
