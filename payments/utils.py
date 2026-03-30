from decimal import Decimal

from django.db.models import Sum

from payments.models import Payment, PaymentInstallment


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