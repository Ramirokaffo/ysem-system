from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from payments.models import Payment, PaymentInstallment


_FRENCH_UNITS = [
    '', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
    'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
    'dix-sept', 'dix-huit', 'dix-neuf',
]
_FRENCH_TENS = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante']


def _french_below_100(n):
    if n < 20:
        return _FRENCH_UNITS[n]
    if n < 70:
        tens, units = divmod(n, 10)
        base = _FRENCH_TENS[tens]
        if units == 0:
            return base
        if units == 1:
            return f'{base} et un'
        return f'{base}-{_FRENCH_UNITS[units]}'
    if n < 80:
        units = n - 60
        if units == 11:
            return 'soixante et onze'
        return f'soixante-{_FRENCH_UNITS[units]}'
    if n == 80:
        return 'quatre-vingts'
    if n < 90:
        return f'quatre-vingt-{_FRENCH_UNITS[n - 80]}'
    return f'quatre-vingt-{_FRENCH_UNITS[n - 80]}'


def _french_below_1000(n):
    if n == 0:
        return ''
    if n < 100:
        return _french_below_100(n)
    hundreds, rest = divmod(n, 100)
    if hundreds == 1:
        prefix = 'cent'
    else:
        prefix = f'{_FRENCH_UNITS[hundreds]} cent'
        if rest == 0:
            prefix += 's'
    if rest == 0:
        return prefix
    return f'{prefix} {_french_below_100(rest)}'


def amount_to_french_words(amount):
    """Convertit un montant entier positif en lettres françaises (jusqu'aux milliards)."""
    try:
        n = int(Decimal(amount))
    except (TypeError, ValueError):
        return ''

    if n < 0:
        return f'moins {amount_to_french_words(-n)}'
    if n == 0:
        return 'zéro'

    parts = []
    billions, n = divmod(n, 1_000_000_000)
    millions, n = divmod(n, 1_000_000)
    thousands, units = divmod(n, 1_000)

    if billions:
        parts.append('un milliard' if billions == 1 else f'{_french_below_1000(billions)} milliards')
    if millions:
        parts.append('un million' if millions == 1 else f'{_french_below_1000(millions)} millions')
    if thousands:
        parts.append('mille' if thousands == 1 else f'{_french_below_1000(thousands)} mille')
    if units:
        parts.append(_french_below_1000(units))

    return ' '.join(parts)


def get_student_level_for_academic_year(student, academic_year=None):
    if not student:
        return None

    academic_year_id = getattr(academic_year, 'pk', academic_year)
    queryset = student.student_levels.select_related('level', 'academic_year')

    if academic_year_id:
        return queryset.filter(is_active=True, academic_year_id=academic_year_id).first()

    return queryset.filter(is_active=True).first()


def get_student_installments_queryset(student=None, academic_year=None):
    academic_year_id = getattr(academic_year, 'pk', academic_year)
    student_program_id = getattr(student, 'program_id', None)

    queryset = PaymentInstallment.objects.select_related(
        'program', 'academic_year', 'level'
    ).filter(
        deleted_at__isnull=True,
    ).order_by('program__name', 'order_number', 'name')

    if not student_program_id or not academic_year_id:
        return queryset.none()

    queryset = queryset.filter(
        program__id=student_program_id,
        academic_year__id=academic_year_id,
    )

    student_level = get_student_level_for_academic_year(student, academic_year)
    if not student_level or not student_level.level_id:
        return queryset

    level_specific_queryset = queryset.filter(level_id=student_level.level_id)
    if level_specific_queryset.exists():
        return level_specific_queryset

    generic_queryset = queryset.filter(level__isnull=True)
    if generic_queryset.exists():
        return generic_queryset

    return queryset.none()


def get_first_installment_for_student(student=None, academic_year=None):
    return get_student_installments_queryset(
        student=student,
        academic_year=academic_year,
    ).order_by('order_number', 'due_date', 'pk').first()


def get_installment_paid_amount(student, installment, academic_year):
    if not student or not installment or not academic_year:
        return Decimal('0.00')

    total_paid = Payment.objects.filter(
        student=student,
        installment=installment,
        academic_year=academic_year,
    ).aggregate(total=Sum('amount_paid'))['total']

    return (total_paid or Decimal('0.00')).quantize(Decimal('0.01'))


def _get_student_level_for_statement(student, academic_year):
    if not academic_year:
        return None

    return student.student_levels.filter(
        academic_year=academic_year,
    ).select_related('level', 'academic_year', 'speciality').order_by(
        '-is_active', 'level__academic_order', 'level__name'
    ).first()


def _get_program_installments(student, academic_year, current_level=None):
    if not academic_year or not student.program_id:
        return []

    level_id = current_level.level_id if current_level else None
    base_queryset = PaymentInstallment.objects.filter(
        deleted_at__isnull=True,
        academic_year=academic_year,
        program=student.program,
    ).select_related('program', 'level').order_by('order_number', 'name', 'pk')

    installments = list(base_queryset.filter(level_id=level_id)) if level_id else []
    if not installments:
        installments = list(base_queryset.filter(level__isnull=True))

    return installments


def build_student_financial_statement(student, academic_year):
    """Construit un relevé financier détaillé (tranches + paiements) pour un étudiant."""
    current_level = _get_student_level_for_statement(student, academic_year)
    installments = _get_program_installments(student, academic_year, current_level=current_level)
    payments = list(
        Payment.objects.filter(
            student=student,
            academic_year=academic_year,
            category='frais_scolarite',
        ).select_related(
            'installment', 'author', 'academic_year'
        ).order_by('-payment_date', '-created_at')
    )

    amount_paid = Decimal('0.00')
    paid_by_installment = defaultdict(lambda: Decimal('0.00'))
    for payment in payments:
        payment_amount = payment.amount_paid or Decimal('0.00')
        amount_paid += payment_amount
        if payment.installment_id:
            paid_by_installment[payment.installment_id] += payment_amount

    today = timezone.localdate()
    total_amount_due = Decimal('0.00')
    overdue_amount = Decimal('0.00')
    installment_rows = []

    for installment in installments:
        installment_amount = installment.amount or Decimal('0.00')
        installment_paid = paid_by_installment[installment.pk]
        remaining_amount = installment_amount - installment_paid
        if remaining_amount < Decimal('0.00'):
            remaining_amount = Decimal('0.00')

        is_overdue = bool(
            installment.due_date
            and installment.due_date <= today
            and remaining_amount > Decimal('0.00')
        )

        if remaining_amount <= Decimal('0.00'):
            status_label = 'Soldé'
            status_badge_class = 'bg-success text-white'
        elif installment_paid > Decimal('0.00'):
            status_label = 'Paiement partiel'
            status_badge_class = 'bg-warning text-dark'
        else:
            status_label = 'Non soldé'
            status_badge_class = 'bg-secondary text-white'

        if is_overdue:
            status_label = 'Échu non soldé'
            status_badge_class = 'bg-danger text-white'
            overdue_amount += remaining_amount

        total_amount_due += installment_amount
        installment_rows.append({
            'installment': installment,
            'amount': installment_amount,
            'amount_paid': installment_paid,
            'remaining_amount': remaining_amount,
            'is_overdue': is_overdue,
            'status_label': status_label,
            'status_badge_class': status_badge_class,
        })

    remaining_amount = total_amount_due - amount_paid
    if remaining_amount < Decimal('0.00'):
        remaining_amount = Decimal('0.00')

    completion_percentage = 0
    if total_amount_due > Decimal('0.00'):
        completion_percentage = min(int((amount_paid / total_amount_due) * 100), 100)

    status = 'overdue' if overdue_amount > Decimal('0.00') else 'up_to_date'
    return {
        'current_level': current_level,
        'installments': installment_rows,
        'payments': payments,
        'payments_count': len(payments),
        'installments_count': len(installment_rows),
        'totals': {
            'total_amount_due': total_amount_due,
            'amount_paid': amount_paid,
            'remaining_amount': remaining_amount,
            'overdue_amount': overdue_amount,
        },
        'status': status,
        'status_label': 'En retard' if status == 'overdue' else 'À jour',
        'status_badge_class': 'bg-danger text-white' if status == 'overdue' else 'bg-success text-white',
        'completion_percentage': completion_percentage,
        'last_payment': payments[0] if payments else None,
    }