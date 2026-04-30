from django.db import models
from django.utils import timezone

from academic.models import AcademicYear, Level, Program
from students.models import Student
from accounts.models import BaseUser


class PaymentInstallment(models.Model):

    """
    Paramétrage des tranches de paiement des frais de la scolarité des étudiants pour chaque programme
    """

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='payment_installments', verbose_name="Programme")
    academic_year = models.ForeignKey(AcademicYear, null=True, on_delete=models.CASCADE, related_name='payment_installments', verbose_name="Année académique")
    level = models.ForeignKey(Level, null=True, on_delete=models.CASCADE, related_name='payment_installments', verbose_name="Niveau d'étude")
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Libellé de la tranche")
    order_number = models.IntegerField(verbose_name="Ordre de la tranche")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant de la tranche")
    due_date = models.DateField(verbose_name="À payer avant le")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de suppression")

    def __str__(self):
        return f"{self.program.name} - {self.name} - {self.level.name} ({self.amount} FCFA)"
    
    class Meta:
        verbose_name = "Tranche de paiement"
        verbose_name_plural = "Tranches de paiement"
        ordering = ['program__name', 'order_number']


class Payment(models.Model):
    """
    Modèle pour les paiements effectués par les étudiants
    """

    PAYMENT_SOURCES = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Espèces'),
        ('other', 'Autre'),
    ]

    PAYMENTS_CATEGORIES = [
        ('inscription', 'Frais d\'inscription'),
        ('frais_ratrappage', 'Frais de ratrappage'),
        ('frais_scolarite', 'Frais de scolarité'),
        ('frais_stage', 'Frais de stage'),
        ('frais_soutenance', 'Frais de soutenance'),
        ('autre', 'Autre'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments', verbose_name="Étudiant")
    installment = models.ForeignKey(
        PaymentInstallment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Tranche de paiement",
    )
    academic_year = models.ForeignKey(AcademicYear, null=True, on_delete=models.CASCADE, related_name='payments', verbose_name="Année académique")
    category = models.CharField(max_length=20, choices=PAYMENTS_CATEGORIES, default='frais_scolarite', verbose_name="Catégorie de paiement")
    author = models.ForeignKey(BaseUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='payments_made', verbose_name="Effectué par") 
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    payment_date = models.DateField(verbose_name="Date de paiement")
    receipt_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Numéro de reçu")
    transaction_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID de transaction")
    group_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Référence de groupe",
        help_text="Identifiant partagé par les paiements créés ensemble (ex. règlement couvrant plusieurs tranches).",
    )
    source = models.CharField(max_length=20, choices=PAYMENT_SOURCES, default='cash', verbose_name="Source du paiement")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    @classmethod
    def _generate_sequenced_reference(cls, field_name, prefix):
        last_value = cls.objects.filter(
            **{f'{field_name}__startswith': prefix},
        ).order_by(f'-{field_name}').values_list(field_name, flat=True).first()

        next_sequence = 1
        if last_value:
            try:
                next_sequence = int(last_value.rsplit('-', 1)[-1]) + 1
            except (TypeError, ValueError):
                next_sequence = cls.objects.filter(**{f'{field_name}__startswith': prefix}).count() + 1

        return f"{prefix}{next_sequence:04d}"

    @classmethod
    def generate_transaction_id(cls):
        date_part = timezone.localdate().strftime('%Y%m%d')
        return cls._generate_sequenced_reference('transaction_id', f"PAY-{date_part}-")

    @classmethod
    def generate_group_reference(cls):
        date_part = timezone.localdate().strftime('%Y%m%d')
        return cls._generate_sequenced_reference('group_reference', f"GRP-{date_part}-")

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)

    def __str__(self):
        student_label = "Étudiant inconnu"
        if self.student_id:
            student_label = f"{self.student.firstname} {self.student.lastname}".strip()

        installment_label = self.installment.name if self.installment_id else self.get_category_display().lower()
        return f"Paiement de {self.amount_paid} FCFA pour {installment_label} par {student_label}"
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date']