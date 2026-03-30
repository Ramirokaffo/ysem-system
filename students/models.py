# from datetime import timezone

from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import Godfather
from academic.models import AcademicYear, Level, Program, Speciality
from schools.models import School
import secrets
import string


class StudentMetaData(models.Model):
    """
    Métadonnées pour les étudiants (informations complémentaires)
    """
    mother_full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom complet de la mère")
    mother_live_city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville de résidence de la mère")
    mother_email = models.EmailField(blank=True, null=True, verbose_name="Email de la mère")
    mother_occupation = models.CharField(max_length=200, blank=True, null=True, verbose_name="Profession de la mère")
    mother_phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone de la mère")
    
    father_full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom complet du père")
    father_live_city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville de résidence du père")
    father_email = models.EmailField(blank=True, null=True, verbose_name="Email du père")
    father_occupation = models.CharField(max_length=200, blank=True, null=True, verbose_name="Profession du père")
    father_phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone du père")
    
    original_country = models.CharField(max_length=100, verbose_name="Pays d'origine")
    original_region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Région d'origine")
    original_department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Département d'origine")
    original_district = models.CharField(max_length=100, blank=True, null=True, verbose_name="District d'origine")
    residence_city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville de résidence")
    residence_quarter = models.CharField(max_length=100, blank=True, null=True, verbose_name="Quartier de résidence")
    
    is_complete = models.BooleanField(default=False, verbose_name="Dossier complet")
    is_online_registration = models.BooleanField(default=False, verbose_name="Inscription en ligne")

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

    # anciennement relevé du baccalauréat ; aujourd'hui on accepte le relevé de la dernière classe fréquentée
    releve_notes_last_class = models.FileField(
        upload_to='documents/inscription/releve_notes/',
        blank=True,
        null=True,
        verbose_name="Relevé de notes de la dernière classe fréquentée",
        help_text="Photocopie du relevé de notes de la dernière classe fréquentée (PNG/JPG/PDF, max 5Mo)"
    )

    justificatif_dernier_diplome = models.FileField(
        upload_to='documents/inscription/justificatif_diplome/',
        blank=True,
        null=True,
        verbose_name="Justificatif du dernier diplôme obtenu",
        help_text="Photocopie du justificatif du dernier diplôme obtenu (PNG/JPG/PDF, max 5Mo)"
    )

    decharge_equivalence = models.FileField(
        upload_to='documents/inscription/decharge_equivalence/',
        blank=True,
        null=True,
        verbose_name="Décharge de la demande d'équivalence pour les diplômes étrangers",
        help_text="Photocopie de la décharge de la demande d'équivalence pour les diplômes étrangers (PNG/JPG/PDF, max 5Mo)"
    )

    bulletins_terminale = models.FileField(
        upload_to='documents/inscription/bulletins/',
        blank=True,
        null=True,
        verbose_name="Bulletins de la classe de terminale",
        help_text="Photocopie des bulletins de notes de la classe de terminale (PNG/JPG/PDF, max 5Mo)"
    )

    releve_notes_master1 = models.FileField(
        upload_to='documents/inscription/releve_master1/',
        blank=True,
        null=True,
        verbose_name="Relevé de notes du Master 1 ou de tout autre diplôme équivalent",
        help_text="Relevé de notes du Master 1 ou de tout autre diplôme équivalent (PNG/JPG/PDF, max 5Mo)"
    )

    photocopie_bts_hnd = models.FileField(
        upload_to='documents/inscription/bts_hnd/',
        blank=True,
        null=True,
        verbose_name="Photocopie du BTS, HND ou de tout autre diplôme équivalent",
        help_text="Photocopie du BTS, HND ou de tout autre diplôme équivalent (PNG/JPG/PDF, max 5Mo)"
    )

    certificat_nationalite = models.FileField(
        upload_to='documents/inscription/certificat_nationalite/',
        blank=True,
        null=True,
        verbose_name="Certificat de nationalité",
        help_text="Photocopie certifiée conforme du certificat de nationalité (PNG/JPG/PDF, max 5Mo)"
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
    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    dossier_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de dossier")
    firstname = models.CharField(max_length=100, verbose_name="Prénom")
    lastname = models.CharField(max_length=100, verbose_name="Nom de famille")
    date_naiss = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    status = models.CharField(max_length=50, choices=[('pending', 'En attente'), ('approved', 'Examinée & Approuvée'), ('abandoned', 'Abandonné'), ('rejected', 'Rejetée'), ("registered", "Inscrit")], verbose_name="Statut de pré-inscription", default='pending')
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name="Genre")
    lang = models.CharField(max_length=50, choices=[('fr', 'Français'), ('en', 'Anglais')], default='fr', verbose_name="Langue")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    # Relations
    # user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    godfather = models.ForeignKey(Godfather, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Parrain")
    metadata = models.OneToOneField('StudentMetaData', on_delete=models.CASCADE, null=True, blank=True, related_name='student', verbose_name="Métadonnées")
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="École fréquentée")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Programme")
    start_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name='students_start_level', verbose_name="Niveau d'entrée")
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True, verbose_name="Date d'inscription")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de suppression")
    last_registration_date = models.DateTimeField(blank=True, null=True, verbose_name="Date dernière inscription")

    specialite_souhaitee_1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité souhaitée 1")
    specialite_souhaitee_2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité souhaitée 2")
    specialite_souhaitee_3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Spécialité souhaitée 3")

    # Champ pour l'authentification externe des étudiants
    external_password_hash = models.CharField(max_length=128, blank=True, null=True, verbose_name="Mot de passe pour consultation externe")
    external_password_created_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de création du mot de passe")

    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name="Photo de profil")

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

    def get_financial_status(self, academic_year=None, as_of_date=None):
        """Calcule dynamiquement le statut financier de l'étudiant."""
        if not academic_year:
            academic_year = AcademicYear.objects.filter(is_active=True).first()

        if not academic_year:
            return None

        from payments.models import Payment, PaymentInstallment

        current_level = self.student_levels.filter(
            academic_year=academic_year,
        ).select_related('level').order_by(
            '-is_active', 'level__academic_order', 'level__name'
        ).first()

        level_id = current_level.level_id if current_level else None
        base_installments = PaymentInstallment.objects.filter(
            deleted_at__isnull=True,
            academic_year=academic_year,
            program=self.program,
        ).order_by('order_number', 'name', 'pk')

        installments = list(base_installments.filter(level_id=level_id)) if level_id else []
        if not installments:
            installments = list(base_installments.filter(level__isnull=True))

        as_of_date = as_of_date or timezone.localdate()
        amount_paid = Payment.objects.filter(
            student=self,
            academic_year=academic_year,
            category='frais_scolarite',
        ).aggregate(total=models.Sum('amount_paid'))['total'] or Decimal('0.00')

        total_due = sum((installment.amount or Decimal('0.00')) for installment in installments)
        due_amount = sum(
            (installment.amount or Decimal('0.00'))
            for installment in installments
            if installment.due_date and installment.due_date <= as_of_date
        )

        remaining_amount = total_due - amount_paid
        if remaining_amount < Decimal('0.00'):
            remaining_amount = Decimal('0.00')

        overdue_amount = due_amount - amount_paid
        if overdue_amount < Decimal('0.00'):
            overdue_amount = Decimal('0.00')

        return {
            'academic_year': academic_year,
            'current_level': current_level,
            'total_amount_due': total_due,
            'amount_paid': amount_paid,
            'remaining_amount': remaining_amount,
            'due_amount': due_amount,
            'overdue_amount': overdue_amount,
            'status': 'overdue' if overdue_amount > Decimal('0.00') else 'up_to_date',
        }

    def can_withdraw_documents(self, academic_year=None):
        """
        Vérifie si l'étudiant peut retirer des documents selon son statut de paiement
        """
        financial_status = self.get_financial_status(academic_year=academic_year)

        if not financial_status:
            return False, "Aucune année académique active trouvée"

        if financial_status['overdue_amount'] > Decimal('0.00'):
            return False, "Situation financière non régularisée"

        return True, "Autorisation accordée"

    def get_active_level(self):
        """
        Récupère le niveau académique actif de l'étudiant
        """
        active_level = self.student_levels.filter(is_active=True).first()
        return active_level

    def mark_last_registration_date(self):
        self.last_registration_date = timezone.now()
        self.save()

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ['-created_at', 'lastname', 'firstname']


class StudentLevel(models.Model):
    """
    Modèle pour associer les étudiants aux niveaux (relation many-to-many avec attributs)
    """
    name = models.CharField(max_length=100, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_levels', verbose_name="Étudiant")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='student_levels', verbose_name="Niveau")
    academic_year = models.ForeignKey(AcademicYear, null=True, on_delete=models.CASCADE, related_name='student_levels', verbose_name="Année académique")
    speciality = models.ForeignKey(Speciality, null=True, blank=True, on_delete=models.SET_NULL, related_name='student_levels', verbose_name="Spécialité de l'étudiant")
    is_active = models.BooleanField(default=False, verbose_name="Niveau actuel de l'étudiant?")
    is_registered = models.BooleanField(default=False, verbose_name="L'étudiant est-il officiellement inscrit à ce niveau?")
    registered_at = models.DateTimeField(blank=True, null=True, verbose_name="Date d'inscription")

    def save(self, *args, **kwargs):
        # Met à jour le champ name avant de sauvegarder
        level_name = self.level.name if self.level else ''
        year_name = self.academic_year.name if self.academic_year else ''
        self.name = f"{level_name} - {year_name} - {self.speciality}"
        super().save(*args, **kwargs)

    def mark_as_registered(self):
        self.is_registered = True
        self.registered_at = timezone.now()
        self.student.mark_last_registration_date()
        self.save()

    def __str__(self):
        return f"{self.student.matricule} - {self.level.name} - {self.academic_year.name} - {self.speciality}"

    class Meta:
        verbose_name = "Niveau Étudiant"
        verbose_name_plural = "Niveaux Étudiants"
        unique_together = ['student', 'level', 'academic_year']
        ordering = ['student__lastname', 'student__firstname']


class OfficialDocument(models.Model):
    """
    Modèle pour les documents officiels des étudiants
    """
    TYPE_STUDENT_CARD = 'student_card'
    TYPE_TRANSCRIPT = 'transcript'
    TYPE_DIPLOMA = 'diploma'
    TYPE_CERTIFICATE = 'certificate'
    TYPE_REGISTRATION_CERTIFICATE = 'registration_certificate'

    TYPE_CHOICES = [
        (TYPE_STUDENT_CARD, "Carte d'étudiant"),
        (TYPE_TRANSCRIPT, 'Relevé de notes'),
        (TYPE_DIPLOMA, 'Diplôme'),
        (TYPE_CERTIFICATE, 'Certificat de scolarité'),
        (TYPE_REGISTRATION_CERTIFICATE, 'CERTIFICAT D’INSCRIPTION'),
    ]

    student_level = models.ForeignKey(StudentLevel, on_delete=models.CASCADE, null=True, related_name='official_documents')
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='Référence')
    status = models.CharField(max_length=50, choices=[('available', 'Non déchargé'), ('withdrawn', 'Déchargé'), ('returned', 'Retourné'), ('lost', 'Perdu')], default='available')
    withdrawn_date = models.DateField(blank=True, null=True)
    returned_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        reference_suffix = f" ({self.reference})" if self.reference else ''
        return f"{self.get_type_display()} - {str(self.student_level)}{reference_suffix}"

    class Meta:
        verbose_name = "documents officiel"
        verbose_name_plural = "documents officiels"
        ordering = ['-created_at', 'student_level__student__lastname', 'student_level__student__firstname']
