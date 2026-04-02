from collections import defaultdict
from decimal import Decimal
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from payments.forms import PaymentForm, get_remaining_installments_data
from students.models import Student, StudentLevel
from payments.models import Payment, PaymentInstallment
from academic.models import AcademicYear, Level, Program
from student_portal.decorators import scholar_admin_required
from django.utils.decorators import method_decorator
from payments.utils import get_installment_paid_amount, get_student_installments_queryset


def _format_amount(value):
    value = (value or Decimal('0.00')).quantize(Decimal('0.01'))
    formatted = f"{value:,.2f}".replace(',', ' ')
    return formatted[:-3] if formatted.endswith('.00') else formatted


def _get_selected_academic_year_from_request(request):
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        academic_year = AcademicYear.objects.filter(pk=academic_year_id).first()
        if academic_year:
            return academic_year

    return AcademicYear.get_active_year() or AcademicYear.objects.order_by('-start_at').first()


def _get_student_level_for_academic_year(student, academic_year):
    if not academic_year:
        return None

    return student.student_levels.filter(
        academic_year=academic_year,
    ).select_related('level', 'academic_year', 'speciality').order_by(
        '-is_active', 'level__academic_order', 'level__name'
    ).first()


def _get_student_installments(student, academic_year, current_level=None):
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


def _build_student_financial_statement(student, academic_year):
    current_level = _get_student_level_for_academic_year(student, academic_year)
    installments = _get_student_installments(student, academic_year, current_level=current_level)
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


def _build_installment_summary(student, academic_year):
    empty_summary = {
        'student': {
            'id': student.pk,
            'label': PaymentForm.get_student_label(student),
        },
        'program_name': student.program.name if student.program_id else '',
        'academic_year_name': getattr(academic_year, 'name', str(academic_year)),
        'installments': [],
        'message': '',
        'totals': {
            'amount': '0.00',
            'amount_paid': '0.00',
            'remaining_amount': '0.00',
            'amount_display': '0 FCFA',
            'amount_paid_display': '0 FCFA',
            'remaining_amount_display': '0 FCFA',
        },
    }

    if not student.program_id:
        empty_summary['message'] = "L'étudiant sélectionné n'est rattaché à aucun programme."
        return empty_summary

    installments = get_student_installments_queryset(
        student=student,
        academic_year=academic_year,
    ).annotate(
        amount_paid_total=Coalesce(
            models.Sum(
                'payments__amount_paid',
                filter=models.Q(
                    payments__student=student,
                    payments__academic_year=academic_year,
                ),
            ),
            Decimal('0.00'),
        )
    ).order_by('order_number', 'name')

    if not installments.exists():
        empty_summary['message'] = "Aucune tranche de paiement n'est configurée pour ce programme et cette année académique."
        return empty_summary

    total_amount = Decimal('0.00')
    total_paid = Decimal('0.00')
    payload = []

    for installment in installments:
        amount = installment.amount or Decimal('0.00')
        amount_paid = installment.amount_paid_total or Decimal('0.00')
        remaining_amount = amount - amount_paid

        if remaining_amount <= Decimal('0.00'):
            status = 'paid'
            status_label = 'Soldé'
            status_badge_class = 'bg-success'
        elif amount_paid > Decimal('0.00'):
            status = 'partial'
            status_label = 'Partiellement soldé'
            status_badge_class = 'bg-warning text-dark'
        else:
            status = 'unpaid'
            status_label = 'Non soldé'
            status_badge_class = 'bg-secondary'

        display_remaining_amount = remaining_amount if remaining_amount > Decimal('0.00') else Decimal('0.00')
        total_amount += amount
        total_paid += amount_paid

        payload.append({
            'id': installment.pk,
            'name': installment.name or f"Tranche {installment.order_number}",
            'label': (
                f"{installment.name or f'Tranche {installment.order_number}'} - "
                f"{_format_amount(amount)} FCFA"
            ),
            'order_number': installment.order_number,
            'due_date': installment.due_date.isoformat() if installment.due_date else '',
            'due_date_display': installment.due_date.strftime('%d/%m/%Y') if installment.due_date else '—',
            'amount': f"{amount:.2f}",
            'amount_display': f"{_format_amount(amount)} FCFA",
            'amount_paid': f"{amount_paid:.2f}",
            'amount_paid_display': f"{_format_amount(amount_paid)} FCFA",
            'remaining_amount': f"{display_remaining_amount:.2f}",
            'remaining_amount_display': f"{_format_amount(display_remaining_amount)} FCFA",
            'is_selectable': display_remaining_amount > Decimal('0.00'),
            'status': status,
            'status_label': status_label,
            'status_badge_class': status_badge_class,
        })

    remaining_total = total_amount - total_paid
    display_remaining_total = remaining_total if remaining_total > Decimal('0.00') else Decimal('0.00')

    empty_summary['installments'] = payload
    empty_summary['totals'] = {
        'amount': f"{total_amount:.2f}",
        'amount_paid': f"{total_paid:.2f}",
        'remaining_amount': f"{display_remaining_total:.2f}",
        'amount_display': f"{_format_amount(total_amount)} FCFA",
        'amount_paid_display': f"{_format_amount(total_paid)} FCFA",
        'remaining_amount_display': f"{_format_amount(display_remaining_total)} FCFA",
    }
    return empty_summary


def _create_remaining_balance_payments(form, author):
    student = form.cleaned_data['student']
    academic_year = form.cleaned_data['academic_year']
    payment_date = form.cleaned_data['payment_date']
    source = form.cleaned_data['source']
    receipt_number = form.cleaned_data.get('receipt_number')
    category = form.cleaned_data['category']

    remaining_installments, remaining_total = get_remaining_installments_data(
        student=student,
        academic_year=academic_year,
    )

    created_payments = []
    with transaction.atomic():
        for item in remaining_installments:
            created_payments.append(Payment.objects.create(
                student=student,
                installment=item['installment'],
                academic_year=academic_year,
                category=category,
                author=author,
                amount_paid=item['remaining_amount'],
                payment_date=payment_date,
                receipt_number=receipt_number,
                source=source,
            ))

    return created_payments, remaining_total


def _get_registration_flow_context(request):
    params = request.POST if request.method == 'POST' else request.GET
    is_registration_flow = str(params.get('registration_flow') or '').lower() in {'1', 'true', 'on', 'yes'}

    if not is_registration_flow:
        return {
            'registration_flow': False,
            'registration_student': None,
            'registration_academic_year': None,
            'registration_installment': None,
            'registration_return_url': '',
        }

    student = Student.objects.select_related('program').filter(
        pk=params.get('registration_student_id') or params.get('student')
    ).first()
    academic_year = AcademicYear.objects.filter(
        pk=params.get('registration_academic_year_id') or params.get('academic_year')
    ).first()
    installment = PaymentInstallment.objects.select_related('level').filter(
        pk=params.get('registration_installment_id') or params.get('installment')
    ).first()

    return {
        'registration_flow': True,
        'registration_student': student,
        'registration_academic_year': academic_year,
        'registration_installment': installment,
        'registration_return_url': params.get('return_url') or '',
    }


def _build_payment_create_query_string(flow_context):
    if not flow_context.get('registration_flow'):
        return ''

    student = flow_context.get('registration_student')
    academic_year = flow_context.get('registration_academic_year')
    installment = flow_context.get('registration_installment')

    if not student or not academic_year:
        return ''

    query_params = {
        'student': student.pk,
        'academic_year': academic_year.pk,
        'category': 'frais_scolarite',
        'registration_flow': '1',
        'registration_student_id': student.pk,
        'registration_academic_year_id': academic_year.pk,
    }

    if installment:
        query_params['installment'] = installment.pk
        query_params['registration_installment_id'] = installment.pk

    if flow_context.get('registration_return_url'):
        query_params['return_url'] = flow_context['registration_return_url']

    return urlencode(query_params)


def _build_payment_form_initial(flow_context):
    initial = {}
    student = flow_context.get('registration_student')
    academic_year = flow_context.get('registration_academic_year')
    installment = flow_context.get('registration_installment')

    if student:
        initial['student'] = student.pk
    if academic_year:
        initial['academic_year'] = academic_year.pk
        initial['category'] = 'frais_scolarite'
    if installment:
        initial['installment'] = installment.pk
        amount_paid = (installment.amount or Decimal('0.00')) - get_installment_paid_amount(
            student=student,
            installment=installment,
            academic_year=academic_year,
        )
        if amount_paid > Decimal('0.00'):
            initial['amount_paid'] = amount_paid.quantize(Decimal('0.01'))

    return initial


def _validate_registration_flow_payment(form, flow_context):
    if not flow_context.get('registration_flow'):
        return

    expected_student = flow_context.get('registration_student')
    expected_academic_year = flow_context.get('registration_academic_year')
    expected_installment = flow_context.get('registration_installment')

    selected_student = form.cleaned_data.get('student')
    selected_academic_year = form.cleaned_data.get('academic_year')
    selected_installment = form.cleaned_data.get('installment')
    category = form.cleaned_data.get('category')
    settle_remaining_balance = form.cleaned_data.get('settle_remaining_balance')

    if expected_student and selected_student != expected_student:
        form.add_error('student', "Ce paiement doit être enregistré pour l'étudiant en cours d'inscription définitive.")

    if expected_academic_year and selected_academic_year != expected_academic_year:
        form.add_error('academic_year', "Ce paiement doit être enregistré sur l'année académique du niveau actif à inscrire.")

    if category != 'frais_scolarite':
        form.add_error('category', "Le flux d'inscription définitive exige un paiement de frais de scolarité.")

    if expected_installment and not settle_remaining_balance and selected_installment != expected_installment:
        form.add_error('installment', "Veuillez solder au minimum la première tranche requise avant l'inscription définitive.")


@method_decorator(scholar_admin_required, name='dispatch')
class PaymentListView(LoginRequiredMixin, TemplateView):
    """Vue principale pour la liste des paiements étudiants."""
    template_name = 'payments/payments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paiements'

        payments = Payment.objects.select_related(
            'student', 'student__program', 'installment', 'installment__program', 'academic_year', 'author'
        ).all().order_by('-payment_date', '-created_at')

        search = (self.request.GET.get('search') or '').strip()
        academic_year_id = self.request.GET.get('academic_year')
        program_id = self.request.GET.get('program')
        installment_id = self.request.GET.get('installment')
        category = self.request.GET.get('category')
        source = self.request.GET.get('source')
        date_from = (self.request.GET.get('date_from') or '').strip()
        date_to = (self.request.GET.get('date_to') or '').strip()

        # Utiliser l'année active par défaut si aucun filtre n'est fourni
        selected_academic_year = None
        if academic_year_id:
            selected_academic_year = AcademicYear.objects.filter(pk=academic_year_id).first()
        else:
            selected_academic_year = AcademicYear.get_active_year()

        if search:
            payments = payments.filter(
                models.Q(student__matricule__icontains=search)
                | models.Q(student__firstname__icontains=search)
                | models.Q(student__lastname__icontains=search)
                | models.Q(receipt_number__icontains=search)
                | models.Q(transaction_id__icontains=search)
            )

        if selected_academic_year:
            payments = payments.filter(academic_year=selected_academic_year)

        if program_id:
            payments = payments.filter(student__program_id=program_id)

        if installment_id:
            payments = payments.filter(installment_id=installment_id)

        if category:
            payments = payments.filter(category=category)

        if source:
            payments = payments.filter(source=source)

        if date_from:
            payments = payments.filter(payment_date__date__gte=date_from)

        if date_to:
            payments = payments.filter(payment_date__date__lte=date_to)

        filtered_payments_count = payments.count()
        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        try:
            per_page = int(per_page)
            if per_page not in [5, 10, 25, 50, 100]:
                per_page = 10
        except (TypeError, ValueError):
            per_page = 10

        paginator = Paginator(payments, per_page)
        page_obj = paginator.get_page(page)

        has_filter = any(
            value for key, value in self.request.GET.items() if key not in {'page', 'per_page'}
        )

        context.update({
            'payments': page_obj.object_list,
            'page_obj': page_obj,
            'filtered_payments_count': filtered_payments_count,
            'has_filter': has_filter,
            'per_page': per_page,
            'per_page_choices': [5, 10, 25, 50, 100],
            'academic_years': AcademicYear.objects.all().order_by('-start_at'),
            'selected_academic_year': selected_academic_year,
            'programs': Program.objects.all().order_by('name'),
            'installments': PaymentInstallment.objects.select_related('program', 'academic_year')
            .filter(deleted_at__isnull=True)
            .order_by('program__name', 'order_number', 'name'),
            'payment_categories': Payment.PAYMENTS_CATEGORIES,
            'payment_sources': Payment.PAYMENT_SOURCES,
        })
        return context


@scholar_admin_required
def payment_create(request):
    """Vue pour enregistrer un nouveau paiement."""
    flow_context = _get_registration_flow_context(request)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            _validate_registration_flow_payment(form, flow_context)

        if form.is_valid():
            payment = None
            created_payments = []

            if form.cleaned_data.get('settle_remaining_balance') and form.cleaned_data.get('category') == 'frais_scolarite':
                created_payments, remaining_total = _create_remaining_balance_payments(form, request.user)
            else:
                payment = form.save(commit=False)
                payment.author = request.user
                payment.save()

            if 'save_and_add' in request.POST:
                if created_payments:
                    messages.success(
                        request,
                        f'Paiement enregistré avec succès pour {form.cleaned_data["student"]} : '
                        f'{_format_amount(remaining_total)} FCFA répartis sur {len(created_payments)} tranche(s). '
                        'Vous pouvez en ajouter un autre.',
                    )
                else:
                    messages.success(
                        request,
                        f'Paiement enregistré avec succès pour {payment.student}. Vous pouvez en ajouter un autre.',
                    )
                redirect_url = reverse('payments:payment_create')
                query_string = _build_payment_create_query_string(flow_context)
                if query_string:
                    redirect_url = f'{redirect_url}?{query_string}'
                return redirect(redirect_url)

            if created_payments:
                messages.success(
                    request,
                    f'Paiement enregistré avec succès pour {form.cleaned_data["student"]} : '
                    f'{_format_amount(remaining_total)} FCFA répartis sur {len(created_payments)} tranche(s).',
                )
            else:
                messages.success(request, f'Paiement enregistré avec succès pour {payment.student}.')

            if flow_context.get('registration_flow') and flow_context.get('registration_student'):
                from main.custom_views.pre_inscriptions_views import pre_inscription_register

                return pre_inscription_register(request, flow_context['registration_student'].matricule)

            return redirect('payments:payments_list')

        messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = PaymentForm(initial=_build_payment_form_initial(flow_context))

    context = {
        'form': form,
        'page_title': 'Créer un paiement',
        'action': 'create',
        **flow_context,
    }
    return render(request, 'payments/payment_form.html', context)


@scholar_admin_required
def payment_detail(request, pk):
    """Affiche les détails complets d'un paiement."""
    payment = get_object_or_404(
        Payment.objects.select_related(
            'student',
            'student__program',
            'installment',
            'installment__program',
            'academic_year',
            'author',
        ),
        pk=pk,
    )

    installment_total_paid = None
    installment_remaining_amount = None

    if payment.installment_id and payment.academic_year_id:
        installment_total_paid = Payment.objects.filter(
            student=payment.student,
            installment=payment.installment,
            academic_year=payment.academic_year,
        ).aggregate(
            total=Coalesce(models.Sum('amount_paid'), Decimal('0.00')),
        )['total']
        installment_remaining_amount = (payment.installment.amount or Decimal('0.00')) - installment_total_paid

        if installment_remaining_amount < Decimal('0.00'):
            installment_remaining_amount = Decimal('0.00')

    context = {
        'page_title': 'Détails du paiement',
        'payment': payment,
        'installment_total_paid': installment_total_paid,
        'installment_remaining_amount': installment_remaining_amount,
    }
    return render(request, 'payments/payment_detail.html', context)


@scholar_admin_required
def payment_student_search(request):
    """Endpoint JSON de recherche d'étudiants pour l'autocomplete du formulaire."""
    query = (request.GET.get('q') or '').strip()

    if not query:
        return JsonResponse({'results': []})

    students = Student.objects.select_related('program').filter(
        deleted_at__isnull=True,
        status='registered',
    ).filter(
        models.Q(matricule__icontains=query)
        | models.Q(firstname__icontains=query)
        | models.Q(lastname__icontains=query)
        | models.Q(program__name__icontains=query)
    ).order_by('matricule')[:10]

    return JsonResponse({
        'results': [
            {
                'id': student.pk,
                'text': PaymentForm.get_student_label(student),
                'matricule': student.matricule,
                'firstname': student.firstname,
                'lastname': student.lastname,
                'program_id': student.program_id or '',
                'program_name': student.program.name if student.program_id else '',
            }
            for student in students
        ]
    })


@scholar_admin_required
def payment_installment_summary(request):
    """Endpoint JSON de synthèse des tranches pour un étudiant et une année académique."""
    student_id = request.GET.get('student_id')
    academic_year_id = request.GET.get('academic_year_id')

    if not student_id or not academic_year_id:
        return JsonResponse({
            'installments': [],
            'message': "Sélectionnez d'abord un étudiant et une année académique.",
        }, status=400)

    student = Student.objects.select_related('program').filter(
        deleted_at__isnull=True,
        pk=student_id,
    ).first()
    academic_year = AcademicYear.objects.filter(pk=academic_year_id).first()

    if not student or not academic_year:
        return JsonResponse({
            'installments': [],
            'message': "Étudiant ou année académique introuvable.",
        }, status=404)

    return JsonResponse(_build_installment_summary(student, academic_year))


# ===== VUES POUR LA GESTION DES STATUTS DE PAIEMENT =====

@method_decorator(scholar_admin_required, name='dispatch')
class PaymentStatusView(LoginRequiredMixin, TemplateView):
    """Vue principale pour la liste des statuts de paiement"""
    template_name = 'payments/payment_status.html'

    STATUS_CHOICES = [
        ('up_to_date', 'À jour'),
        ('overdue', 'En retard'),
    ]
    PER_PAGE_CHOICES = [10, 25, 50, 100]

    def _get_selected_academic_year(self):
        return _get_selected_academic_year_from_request(self.request)

    def _get_per_page(self):
        try:
            per_page = int(self.request.GET.get('per_page', self.PER_PAGE_CHOICES[0]))
        except (TypeError, ValueError):
            per_page = self.PER_PAGE_CHOICES[0]

        if per_page not in self.PER_PAGE_CHOICES:
            return self.PER_PAGE_CHOICES[0]
        return per_page

    @staticmethod
    def _get_student_level(student):
        levels = getattr(student, 'payment_status_levels', [])
        if not levels:
            return None

        active_level = next((level for level in levels if level.is_active), None)
        return active_level or levels[0]

    def _build_payment_rows(self, academic_year, search, program_id, level_id, status_filter):
        if not academic_year:
            return []

        students = Student.objects.select_related('program').filter(
            status='registered',
            deleted_at__isnull=True,
        ).filter(
            models.Q(student_levels__academic_year=academic_year)
            | models.Q(payments__academic_year=academic_year, payments__category='frais_scolarite')
        ).distinct()

        if search:
            students = students.filter(
                models.Q(matricule__icontains=search)
                | models.Q(firstname__icontains=search)
                | models.Q(lastname__icontains=search)
            )

        if program_id:
            students = students.filter(program_id=program_id)

        if level_id:
            students = students.filter(
                student_levels__academic_year=academic_year,
                student_levels__level_id=level_id,
            )

        students = list(
            students.prefetch_related(
                models.Prefetch(
                    'student_levels',
                    queryset=StudentLevel.objects.select_related('level', 'academic_year').filter(
                        academic_year=academic_year,
                    ).order_by('-is_active', 'level__academic_order', 'level__name'),
                    to_attr='payment_status_levels',
                )
            ).order_by('lastname', 'firstname', 'matricule')
        )

        if not students:
            return []

        student_ids = [student.pk for student in students]
        payment_totals = {
            item['student_id']: (item['total_paid'] or Decimal('0.00'))
            for item in Payment.objects.filter(
                student_id__in=student_ids,
                academic_year=academic_year,
                category='frais_scolarite',
            ).values('student_id').annotate(total_paid=models.Sum('amount_paid'))
        }

        print(payment_totals)

        program_ids = {student.program_id for student in students if student.program_id}
        level_ids = {
            current_level.level_id
            for student in students
            for current_level in [self._get_student_level(student)]
            if current_level and current_level.level_id
        }

        installment_queryset = PaymentInstallment.objects.filter(
            deleted_at__isnull=True,
            academic_year=academic_year,
            program_id__in=program_ids,
        ).select_related('program', 'level').order_by('order_number', 'name', 'pk')

        if level_ids:
            installment_queryset = installment_queryset.filter(
                models.Q(level_id__in=level_ids) | models.Q(level__isnull=True)
            )
        else:
            installment_queryset = installment_queryset.filter(level__isnull=True)

        installments_by_key = defaultdict(list)
        for installment in installment_queryset:
            installments_by_key[(installment.program_id, installment.level_id)].append(installment)

        today = timezone.localdate()
        rows = []

        for student in students:
            current_level = self._get_student_level(student)
            current_level_id = current_level.level_id if current_level else None

            installments = installments_by_key.get((student.program_id, current_level_id))
            if not installments:
                installments = installments_by_key.get((student.program_id, None), [])

            total_due = sum((installment.amount or Decimal('0.00')) for installment in installments)
            amount_paid = payment_totals.get(student.pk, Decimal('0.00'))
            remaining_amount = total_due - amount_paid
            if remaining_amount < Decimal('0.00'):
                remaining_amount = Decimal('0.00')

            due_amount = sum(
                (installment.amount or Decimal('0.00'))
                for installment in installments
                if installment.due_date and installment.due_date <= today
            )
            overdue_amount = due_amount - amount_paid
            if overdue_amount < Decimal('0.00'):
                overdue_amount = Decimal('0.00')

            status = 'overdue' if overdue_amount > Decimal('0.00') else 'up_to_date'
            if status_filter and status != status_filter:
                continue

            rows.append({
                'student': student,
                'full_name': f"{student.firstname} {student.lastname}".strip(),
                'academic_year': academic_year,
                'level': current_level.level if current_level and current_level.level_id else None,
                'total_amount_due': total_due,
                'amount_paid': amount_paid,
                'remaining_amount': remaining_amount,
                'overdue_amount': overdue_amount,
                'status': status,
                'status_label': 'En retard' if status == 'overdue' else 'À jour',
                'status_badge_class': 'bg-danger' if status == 'overdue' else 'bg-success',
                'detail_url': (
                    f"{reverse('payments:payment_status_student_detail', args=[student.matricule])}?"
                    f"{urlencode({'academic_year': academic_year.pk, 'return_url': self.request.get_full_path()})}"
                ),
            })

        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statut de paiement'

        academic_year = self._get_selected_academic_year()
        search = (self.request.GET.get('search') or '').strip()
        program_id = self.request.GET.get('program') or ''
        level_id = self.request.GET.get('level') or ''
        status_filter = self.request.GET.get('status') or ''

        if status_filter not in {choice[0] for choice in self.STATUS_CHOICES}:
            status_filter = ''

        payment_rows = self._build_payment_rows(
            academic_year=academic_year,
            search=search,
            program_id=program_id,
            level_id=level_id,
            status_filter=status_filter,
        )

        per_page = self._get_per_page()
        page_obj = Paginator(payment_rows, per_page).get_page(self.request.GET.get('page', 1))

        total_due = sum((row['total_amount_due'] for row in payment_rows), Decimal('0.00'))
        total_paid = sum((row['amount_paid'] for row in payment_rows), Decimal('0.00'))
        total_remaining = sum((row['remaining_amount'] for row in payment_rows), Decimal('0.00'))

        context.update({
            'page_obj': page_obj,
            'payment_rows': page_obj.object_list,
            'filtered_students_count': len(payment_rows),
            'has_filter': any([
                search,
                self.request.GET.get('academic_year'),
                program_id,
                level_id,
                status_filter,
            ]),
            'per_page': per_page,
            'per_page_choices': self.PER_PAGE_CHOICES,
            'selected_academic_year': academic_year,
            'academic_years': AcademicYear.objects.all().order_by('-start_at'),
            'programs': Program.objects.all().order_by('name'),
            'levels': Level.objects.all().order_by('academic_order', 'name'),
            'status_choices': self.STATUS_CHOICES,
            'stats': {
                'total': len(payment_rows),
                'up_to_date': sum(1 for row in payment_rows if row['status'] == 'up_to_date'),
                'overdue': sum(1 for row in payment_rows if row['status'] == 'overdue'),
                'total_due': total_due,
                'total_paid': total_paid,
                'remaining': total_remaining,
            },
        })

        return context


@method_decorator(scholar_admin_required, name='dispatch')
class PaymentStatusStudentDetailView(LoginRequiredMixin, TemplateView):
    """Vue détaillée de la situation financière d'un étudiant."""
    template_name = 'payments/payment_status_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(
            Student.objects.select_related('program').filter(deleted_at__isnull=True),
            matricule=kwargs['pk'],
        )
        academic_year = _get_selected_academic_year_from_request(self.request)
        statement = _build_student_financial_statement(student, academic_year) if academic_year else None

        payment_list_query = {'search': student.matricule}
        if academic_year:
            payment_list_query['academic_year'] = academic_year.pk

        context.update({
            'page_title': 'Situation financière',
            'student': student,
            'selected_academic_year': academic_year,
            'statement': statement,
            'return_url': self.request.GET.get('return_url') or reverse('payments:payment_status'),
            'payment_list_url': f"{reverse('payments:payments_list')}?{urlencode(payment_list_query)}",
            'student_detail_url': reverse('students:etudiant_detail', args=[student.matricule]),
            'generated_on': timezone.localtime(),
        })
        return context


