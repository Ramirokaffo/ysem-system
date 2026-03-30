from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from academic.models import AcademicYear, Level, Program
from accounts.models import BaseUser
from payments.models import Payment, PaymentInstallment
from students.models import Student, StudentLevel


class PaymentListViewTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_payments',
            password='testpass123',
            role='scholar',
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True,
        )
        self.program = Program.objects.create(name='Informatique')
        self.other_program = Program.objects.create(name='Gestion')

        self.installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            name='Tranche 1',
            order_number=1,
            amount=50000,
            due_date=date(2024, 10, 15),
        )
        self.other_installment = PaymentInstallment.objects.create(
            program=self.other_program,
            academic_year=self.academic_year,
            name='Tranche 2',
            order_number=2,
            amount=75000,
            due_date=date(2024, 11, 15),
        )
        self.second_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            name='Tranche 2',
            order_number=2,
            amount=40000,
            due_date=date(2024, 12, 10),
        )

        self.student = Student.objects.create(
            matricule='PAY001',
            firstname='Jean',
            lastname='Dupont',
            status='registered',
            gender='M',
            program=self.program,
        )
        self.other_student = Student.objects.create(
            matricule='PAY002',
            firstname='Alice',
            lastname='Ngono',
            status='registered',
            gender='F',
            program=self.other_program,
        )

        self.payment = Payment.objects.create(
            student=self.student,
            installment=self.installment,
            academic_year=self.academic_year,
            category='inscription',
            author=self.user,
            amount_paid=25000,
            payment_date=timezone.make_aware(datetime.combine(date(2024, 1, 10), datetime.min.time())),
            receipt_number='REC001',
            transaction_id='TX001',
            source='cash',
        )
        self.other_payment = Payment.objects.create(
            student=self.other_student,
            installment=self.other_installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=45000,
            payment_date=timezone.make_aware(datetime.combine(date(2024, 2, 5), datetime.min.time())),
            receipt_number='REC002',
            transaction_id='TX002',
            source='mobile_money',
        )

        self._set_payment_date(self.payment, date(2024, 1, 10))
        self._set_payment_date(self.other_payment, date(2024, 2, 5))
        self.list_url = reverse('main:payments:payments_list')
        self.create_url = reverse('main:payments:payment_create')
        self.detail_url = reverse('main:payments:payment_detail', args=[self.payment.pk])
        self.student_search_url = reverse('main:payments:payment_student_search')
        self.installment_summary_url = reverse('main:payments:payment_installment_summary')

    def _set_payment_date(self, payment, value):
        aware_datetime = timezone.make_aware(datetime.combine(value, datetime.min.time()))
        Payment.objects.filter(pk=payment.pk).update(payment_date=aware_datetime)
        payment.refresh_from_db()

    def test_payments_list_displays_sidebar_link_and_filter_accordion(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Liste des paiements')
        self.assertContains(response, 'Ajouter un paiement')
        self.assertContains(response, 'id="filtersToggle"')
        self.assertContains(response, reverse('main:payments:payments_list'))
        self.assertContains(response, reverse('main:payments:payment_create'))
        self.assertContains(response, self.detail_url)
        self.assertContains(response, '2 paiement(s) trouvé(s)')

    def test_payment_detail_view_displays_complete_payment_information(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payment'], self.payment)
        self.assertEqual(response.context['installment_total_paid'], Decimal('25000'))
        self.assertEqual(response.context['installment_remaining_amount'], Decimal('25000'))
        self.assertContains(response, 'Détails du paiement')
        self.assertContains(response, 'Jean Dupont')
        self.assertContains(response, self.student.matricule)
        self.assertContains(response, self.program.name)
        self.assertContains(response, self.installment.name)
        self.assertContains(response, self.academic_year.name)
        self.assertContains(response, 'REC001')
        self.assertContains(response, 'TX001')
        self.assertContains(response, reverse('main:payments:payments_list'))

    def test_payments_list_can_filter_by_program_category_source_and_date_interval(self):
        response = self.client.get(self.list_url, {
            'program': self.program.pk,
            'category': 'inscription',
            'source': 'cash',
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtered_payments_count'], 1)
        self.assertContains(response, 'Jean Dupont')
        self.assertContains(response, 'REC001')
        self.assertNotContains(response, 'Alice Ngono')
        self.assertNotContains(response, 'REC002')
        self.assertContains(response, 'Du : 2024-01-01')
        self.assertContains(response, 'Au : 2024-01-31')

    def test_payment_create_view_displays_form(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Créer un paiement')
        self.assertContains(response, 'name="student_search"')
        self.assertContains(response, 'name="student"')
        self.assertContains(response, 'name="installment"')
        self.assertContains(response, 'name="settle_remaining_balance"')
        self.assertContains(response, 'name="payment_date"')
        self.assertContains(response, 'payment-student-results')
        self.assertContains(response, self.student_search_url)
        self.assertContains(response, self.installment_summary_url)
        self.assertContains(response, 'installment-summary-body')
        self.assertContains(response, 'Enregistrer et ajouter')
        self.assertNotContains(response, 'name="transaction_id"')

        form = response.context['form']
        self.assertEqual(form['payment_date'].value(), timezone.localdate())
        self.assertEqual(str(form['academic_year'].value()), str(self.academic_year.pk))
        self.assertEqual(form['source'].value(), 'cash')

    def test_payment_student_search_endpoint_returns_matching_students(self):
        response = self.client.get(self.student_search_url, {'q': 'Jean'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('results', payload)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], self.student.pk)
        self.assertEqual(payload['results'][0]['program_name'], self.program.name)

    def test_payment_installment_summary_endpoint_returns_paid_and_unpaid_installments(self):
        response = self.client.get(self.installment_summary_url, {
            'student_id': self.student.pk,
            'academic_year_id': self.academic_year.pk,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['program_name'], self.program.name)
        self.assertEqual(len(payload['installments']), 2)
        self.assertEqual(payload['installments'][0]['id'], self.installment.pk)
        self.assertEqual(payload['installments'][0]['amount_paid'], '25000.00')
        self.assertEqual(payload['installments'][0]['status'], 'partial')
        self.assertTrue(payload['installments'][0]['is_selectable'])
        self.assertEqual(payload['installments'][1]['id'], self.second_installment.pk)
        self.assertEqual(payload['installments'][1]['amount_paid'], '0.00')
        self.assertEqual(payload['installments'][1]['status'], 'unpaid')
        self.assertTrue(payload['installments'][1]['is_selectable'])
        self.assertEqual(payload['totals']['amount'], '90000.00')
        self.assertEqual(payload['totals']['amount_paid'], '25000.00')
        self.assertEqual(payload['totals']['remaining_amount'], '65000.00')

    def test_payment_installment_summary_marks_fully_paid_installment_as_not_selectable(self):
        Payment.objects.create(
            student=self.student,
            installment=self.installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=25000,
            payment_date=timezone.make_aware(datetime.combine(date(2024, 3, 1), datetime.min.time())),
            receipt_number='REC004A',
            transaction_id='TX004A',
            source='cash',
        )

        response = self.client.get(self.installment_summary_url, {
            'student_id': self.student.pk,
            'academic_year_id': self.academic_year.pk,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_installment = payload['installments'][0]
        self.assertEqual(first_installment['id'], self.installment.pk)
        self.assertEqual(first_installment['status'], 'paid')
        self.assertFalse(first_installment['is_selectable'])

    def test_payment_create_view_rejects_fully_paid_installment_selection(self):
        Payment.objects.create(
            student=self.student,
            installment=self.installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=25000,
            payment_date=timezone.make_aware(datetime.combine(date(2024, 3, 1), datetime.min.time())),
            receipt_number='REC004B',
            transaction_id='TX004B',
            source='cash',
        )

        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'installment': self.installment.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-18',
            'category': 'frais_scolarite',
            'amount_paid': '1000',
            'source': 'cash',
            'receipt_number': 'REC006A',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 3)
        self.assertContains(response, 'Cette tranche est déjà totalement soldée pour cet étudiant.')

    def test_payment_create_view_can_create_payment_and_redirect_to_list(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-12',
            'category': 'inscription',
            'amount_paid': '30000',
            'source': 'cash',
            'receipt_number': 'REC003',
        }, follow=True)

        self.assertRedirects(response, self.list_url)
        self.assertEqual(Payment.objects.count(), 3)

        payment = Payment.objects.get(receipt_number='REC003')
        self.assertEqual(payment.student, self.student)
        self.assertIsNone(payment.installment)
        self.assertEqual(payment.author, self.user)
        self.assertEqual(payment.source, 'cash')
        self.assertEqual(payment.payment_date.date(), date(2024, 3, 12))
        self.assertTrue(payment.transaction_id.startswith(f'PAY-{timezone.localdate():%Y%m%d}-'))
        self.assertContains(response, 'Paiement enregistré avec succès')

    def test_payment_create_view_can_save_and_add_another_payment(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-13',
            'category': 'inscription',
            'amount_paid': '15000',
            'source': 'cash',
            'receipt_number': 'REC003B',
            'save_and_add': '1',
        }, follow=True)

        self.assertRedirects(response, self.create_url)
        self.assertEqual(Payment.objects.count(), 3)
        self.assertContains(response, 'Vous pouvez en ajouter un autre')
        self.assertFalse(response.context['form'].is_bound)

    def test_payment_create_view_requires_installment_for_tuition_fees(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-12',
            'category': 'frais_scolarite',
            'amount_paid': '30000',
            'source': 'cash',
            'receipt_number': 'REC004',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertContains(response, 'La tranche de paiement est obligatoire pour les frais de scolarité.')

    def test_payment_create_view_accepts_matching_installment_for_tuition_fees(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'installment': self.installment.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-18',
            'category': 'frais_scolarite',
            'amount_paid': '25000',
            'source': 'cash',
            'receipt_number': 'REC005',
        }, follow=True)

        self.assertRedirects(response, self.list_url)

        payment = Payment.objects.get(receipt_number='REC005')
        self.assertEqual(payment.installment, self.installment)
        self.assertEqual(payment.category, 'frais_scolarite')

    def test_payment_create_view_can_settle_full_remaining_balance_across_installments(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-20',
            'category': 'frais_scolarite',
            'settle_remaining_balance': 'on',
            'amount_paid': '65000',
            'source': 'cash',
            'receipt_number': 'REC007',
        }, follow=True)

        self.assertRedirects(response, self.list_url)
        self.assertEqual(Payment.objects.count(), 4)

        settled_payments = Payment.objects.filter(receipt_number='REC007').order_by('installment__order_number')
        self.assertEqual(settled_payments.count(), 2)
        self.assertEqual(settled_payments[0].installment, self.installment)
        self.assertEqual(settled_payments[0].amount_paid, Decimal('25000.00'))
        self.assertEqual(settled_payments[1].installment, self.second_installment)
        self.assertEqual(settled_payments[1].amount_paid, Decimal('40000.00'))
        self.assertContains(response, 'répartis sur 2 tranche(s)')

    def test_payment_create_view_rejects_inexact_amount_for_full_remaining_balance_settlement(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-20',
            'category': 'frais_scolarite',
            'settle_remaining_balance': 'on',
            'amount_paid': '64000',
            'source': 'cash',
            'receipt_number': 'REC007B',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertContains(response, 'Le montant payé doit correspondre exactement au reste total dû')

    def test_payment_create_view_rejects_amount_greater_than_installment_remaining_due(self):
        response = self.client.post(self.create_url, {
            'student_search': 'Jean Dupont',
            'student': self.student.pk,
            'installment': self.installment.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2024-03-18',
            'category': 'frais_scolarite',
            'amount_paid': '26000',
            'source': 'cash',
            'receipt_number': 'REC006',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertContains(response, 'Le montant payé ne peut pas dépasser le reste dû')

    def test_payment_installment_summary_filters_installments_by_active_level_when_available(self):
        active_level = Level.objects.create(name='Licence 1')
        other_level = Level.objects.create(name='Master 1')
        StudentLevel.objects.create(
            student=self.student,
            level=active_level,
            academic_year=self.academic_year,
            is_active=True,
        )

        level_first_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=active_level,
            name='Tranche niveau actif',
            order_number=1,
            amount=55000,
            due_date=date(2024, 10, 20),
        )
        PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=other_level,
            name='Tranche autre niveau',
            order_number=1,
            amount=65000,
            due_date=date(2024, 10, 25),
        )

        response = self.client.get(self.installment_summary_url, {
            'student_id': self.student.pk,
            'academic_year_id': self.academic_year.pk,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['installments']), 1)
        self.assertEqual(payload['installments'][0]['id'], level_first_installment.pk)

    def test_payment_create_view_displays_registration_flow_information(self):
        level = Level.objects.create(name='Licence 2')
        StudentLevel.objects.create(
            student=self.student,
            level=level,
            academic_year=self.academic_year,
            is_active=True,
        )
        first_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=level,
            name='Tranche 1 niveau actif',
            order_number=1,
            amount=50000,
            due_date=date(2024, 10, 18),
        )

        response = self.client.get(self.create_url, {
            'student': self.student.pk,
            'academic_year': self.academic_year.pk,
            'category': 'frais_scolarite',
            'installment': first_installment.pk,
            'registration_flow': '1',
            'registration_student_id': self.student.pk,
            'registration_academic_year_id': self.academic_year.pk,
            'registration_installment_id': first_installment.pk,
            'return_url': reverse('main:inscription_detail', kwargs={'pk': self.student.matricule}),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flux d'inscription définitive en cours")
        self.assertContains(response, 'name="registration_flow" value="1"')
        self.assertContains(response, "Payer et finaliser l'inscription")
