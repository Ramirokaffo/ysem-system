from datetime import datetime
from decimal import Decimal

from django import forms
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from students.models import Student
from academic.models import AcademicYear
from payments.models import Payment, PaymentInstallment
from payments.utils import get_student_installments_queryset


def _format_amount(value):
    value = Decimal(value or '0.00').quantize(Decimal('0.01'))
    formatted = f"{value:,.2f}".replace(',', ' ')
    return formatted[:-3] if formatted.endswith('.00') else formatted


def get_available_installments_queryset(student=None, academic_year=None, include_installment_id=None):
    base_queryset = PaymentInstallment.objects.select_related(
        'program', 'academic_year', 'level'
    ).filter(
        deleted_at__isnull=True,
    ).order_by('program__name', 'order_number', 'name')

    queryset = get_student_installments_queryset(
        student=student,
        academic_year=academic_year,
    )

    if not queryset.exists():
        return base_queryset.filter(pk=include_installment_id) if include_installment_id else base_queryset.none()

    queryset = queryset.annotate(
        amount_paid_total=Coalesce(
            models.Sum(
                'payments__amount_paid',
                filter=models.Q(
                    payments__student=student,
                    payments__academic_year_id=getattr(academic_year, 'pk', academic_year),
                ),
            ),
            Decimal('0.00'),
        ),
    )

    available_filters = Q(amount__gt=models.F('amount_paid_total'))
    if include_installment_id:
        available_filters |= Q(pk=include_installment_id)

    return queryset.filter(available_filters).distinct()


def get_remaining_installments_data(student=None, academic_year=None):
    installments = get_available_installments_queryset(
        student=student,
        academic_year=academic_year,
    )

    remaining_installments = []
    remaining_total = Decimal('0.00')

    for installment in installments:
        remaining_amount = (installment.amount or Decimal('0.00')) - (installment.amount_paid_total or Decimal('0.00'))
        if remaining_amount <= Decimal('0.00'):
            continue

        remaining_installments.append({
            'installment': installment,
            'remaining_amount': remaining_amount.quantize(Decimal('0.01')),
        })
        remaining_total += remaining_amount

    return remaining_installments, remaining_total.quantize(Decimal('0.01'))


class PaymentForm(forms.ModelForm):
    """Formulaire pour l'enregistrement manuel d'un paiement étudiant."""

    student_search = forms.CharField(
        label="Étudiant",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control payment-student-autocomplete',
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
    installment = forms.ModelChoiceField(
        queryset=PaymentInstallment.objects.none(),
        label="Tranche de paiement",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner une tranche",
    )
    settle_remaining_balance = forms.BooleanField(
        label="Solder tout le reste dû",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    payment_date = forms.DateField(
        label="Date du paiement",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.localdate(),
    )

    class Meta:
        model = Payment
        fields = [
            'student', 'installment', 'academic_year', 'category',
            'amount_paid', 'source', 'receipt_number', 'payment_date'
        ]
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
            'source': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de reçu',
            }),
        }
        labels = {
            'academic_year': 'Année académique',
            'category': 'Catégorie de paiement',
            'amount_paid': 'Montant payé (FCFA)',
            'source': 'Source du paiement',
            'receipt_number': 'Numéro de reçu',
        }

    @staticmethod
    def get_student_label(student):
        student_name = f"{student.firstname} {student.lastname}".strip()
        program_name = student.program.name if student.program_id else 'Programme non défini'
        return f"{student.matricule} - {student_name} - {program_name}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def _normalize_pk(value):
            return getattr(value, 'pk', value)

        student_queryset = Student.objects.select_related('program').filter(deleted_at__isnull=True).order_by('matricule')
        self.fields['student'].queryset = student_queryset
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_at')

        selected_student_id = _normalize_pk(
            self.data.get('student') or self.initial.get('student') or getattr(self.instance, 'student_id', None)
        )
        selected_academic_year_id = _normalize_pk(
            self.data.get('academic_year') or self.initial.get('academic_year') or getattr(self.instance, 'academic_year_id', None)
        )
        selected_installment_id = _normalize_pk(
            self.data.get('installment') or self.initial.get('installment') or getattr(self.instance, 'installment_id', None)
        )

        selected_student = None
        if selected_student_id:
            selected_student = student_queryset.filter(pk=selected_student_id).first()

        self.fields['installment'].queryset = get_available_installments_queryset(
            student=selected_student,
            academic_year=selected_academic_year_id,
            include_installment_id=selected_installment_id,
        )

        if not self.is_bound:
            self.fields['payment_date'].initial = timezone.localdate()
            # print(timezone.localdate())
            self.fields['source'].initial = 'cash'
            active_year = AcademicYear.get_active_year()
            if active_year:
                self.fields['academic_year'].initial = active_year

        initial_student = selected_student or self.initial.get('student') or getattr(self.instance, 'student', None)
        if initial_student and not self.is_bound:
            if not isinstance(initial_student, Student):
                initial_student = student_queryset.filter(pk=_normalize_pk(initial_student)).first()
            if initial_student:
                self.fields['student_search'].initial = self.get_student_label(initial_student)

        self.fields['student_search'].widget.attrs['data-selected-student-id'] = str(selected_student.pk) if selected_student else ''
        self.fields['student_search'].widget.attrs['data-selected-program-id'] = str(selected_student.program_id or '') if selected_student else ''
        self.fields['student_search'].widget.attrs['data-selected-program-name'] = (
            selected_student.program.name if selected_student and selected_student.program_id else ''
        )

    def clean_payment_date(self):
        payment_date = self.cleaned_data.get('payment_date')
        if not payment_date:
            return payment_date

        if isinstance(payment_date, datetime):
            return payment_date if timezone.is_aware(payment_date) else timezone.make_aware(payment_date)

        payment_datetime = datetime.combine(payment_date, datetime.min.time().replace(hour=12))
        return timezone.make_aware(payment_datetime)

    def clean(self):
        cleaned_data = super().clean()
        student_search = (cleaned_data.get('student_search') or '').strip()
        student = cleaned_data.get('student')
        installment = cleaned_data.get('installment')
        academic_year = cleaned_data.get('academic_year')
        category = cleaned_data.get('category')
        amount_paid = cleaned_data.get('amount_paid')
        settle_remaining_balance = cleaned_data.get('settle_remaining_balance')

        if not student:
            if student_search:
                self.add_error('student', "Veuillez sélectionner un étudiant dans la liste proposée.")
            else:
                self.add_error('student', "Veuillez sélectionner un étudiant.")

        if amount_paid is not None and amount_paid <= 0:
            self.add_error('amount_paid', "Le montant payé doit être supérieur à zéro.")

        if category == 'frais_scolarite':
            if settle_remaining_balance:
                cleaned_data['installment'] = None
                installment = None
            elif not installment:
                self.add_error('installment', "La tranche de paiement est obligatoire pour les frais de scolarité.")
        else:
            cleaned_data['installment'] = None
            installment = None
            cleaned_data['settle_remaining_balance'] = False
            settle_remaining_balance = False

        installment_is_compatible = True
        if installment and academic_year and installment.academic_year_id != academic_year.pk:
            installment_is_compatible = False
            self.add_error(
                'installment',
                "La tranche sélectionnée n'appartient pas à l'année académique choisie.",
            )

        if student and installment:
            if not student.program_id:
                installment_is_compatible = False
                self.add_error(
                    'student',
                    "L'étudiant sélectionné n'est rattaché à aucun programme.",
                )
            elif installment.program_id != student.program_id:
                installment_is_compatible = False
                self.add_error(
                    'installment',
                    "La tranche sélectionnée ne correspond pas au programme de l'étudiant.",
                )
            elif installment.level_id:
                student_level = student.student_levels.filter(
                    is_active=True,
                    academic_year=academic_year,
                ).first()
                if student_level and installment.level_id != student_level.level_id:
                    installment_is_compatible = False
                    self.add_error(
                        'installment',
                        "La tranche sélectionnée ne correspond pas au niveau actif de l'étudiant pour l'année choisie.",
                    )

        if (
            category == 'frais_scolarite'
            and amount_paid is not None
            and student
            and academic_year
            and settle_remaining_balance
        ):
            remaining_installments, remaining_total = get_remaining_installments_data(
                student=student,
                academic_year=academic_year,
            )

            if not remaining_installments or remaining_total <= Decimal('0.00'):
                self.add_error(
                    'settle_remaining_balance',
                    "Aucun reste dû de scolarité n'est disponible pour cet étudiant sur l'année choisie.",
                )
            elif amount_paid.quantize(Decimal('0.01')) != remaining_total:
                self.add_error(
                    'amount_paid',
                    "Le montant payé doit correspondre exactement au reste total dû "
                    f"({_format_amount(remaining_total)} FCFA).",
                )

        if (
            category == 'frais_scolarite'
            and amount_paid is not None
            and student
            and academic_year
            and installment
            and installment_is_compatible
        ):
            existing_paid_amount = Payment.objects.filter(
                student=student,
                academic_year=academic_year,
                installment=installment,
            ).exclude(
                pk=self.instance.pk,
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

            remaining_amount = (installment.amount or Decimal('0.00')) - existing_paid_amount
            if remaining_amount <= Decimal('0.00'):
                self.add_error(
                    'installment',
                    "Cette tranche est déjà totalement soldée pour cet étudiant.",
                )
            elif amount_paid > remaining_amount:
                self.add_error(
                    'amount_paid',
                    "Le montant payé ne peut pas dépasser le reste dû de la tranche sélectionnée "
                    f"({_format_amount(remaining_amount)} FCFA).",
                )

        return cleaned_data

