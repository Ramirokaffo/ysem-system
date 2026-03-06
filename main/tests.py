from io import BytesIO
from tempfile import TemporaryDirectory
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from academic.models import AcademicYear, Level, Program
from accounts.models import BaseUser, Godfather
from main.forms import InscriptionCompleteForm
from schools.models import School
from students.models import Student, StudentLevel, StudentMetaData


class NouvelleInscriptionViewTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_user',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 1')
        self.existing_godfather = Godfather.objects.create(
            full_name='Parrain Existant',
            occupation='Entrepreneur',
            phone_number='+237699999998',
            email='parrain.existant@example.com',
        )
        self.existing_school = School.objects.create(
            name='Lycée Général Leclerc',
            phone_number='+237677777777',
            level='secondary',
        )
        self.url = reverse('main:nouvelle_inscription')

    def _valid_payload(self):
        return {
            'nom': 'Doe',
            'prenom': 'Jane',
            'date_naissance': '2000-01-15',
            'lieu_naissance': 'Yaounde',
            'sexe': 'F',
            'courriel': 'jane.doe@example.com',
            'telephone': '+237699999999',
            'premiere_langue_officielle': 'francais',
            'annee_academique': self.academic_year.pk,
            'niveau': self.level.pk,
            'pays_origine': 'Cameroun',
        }

    def test_get_displays_existing_godfather_selector(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parrain/tuteur existant')
        self.assertContains(response, 'Parrain Existant')
        self.assertContains(response, 'Établissement existant')
        self.assertContains(response, 'Lycée Général Leclerc')
        self.assertContains(response, 'Dossier complet')
        self.assertFalse(response.context['form'].fields['is_complete'].initial)

    def test_post_with_existing_godfather_reuses_it(self):
        payload = self._valid_payload()
        payload['parrain_existant'] = self.existing_godfather.pk

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Godfather.objects.count(), 1)
        student = Student.objects.get()
        self.assertEqual(student.godfather, self.existing_godfather)

    def test_post_with_manual_godfather_creates_new_one(self):
        payload = self._valid_payload()
        payload.update({
            'nom_tuteur': 'Nouveau Parrain',
            'profession_tuteur': 'Ingénieur',
            'telephone_tuteur': '+237688888888',
            'courriel_tuteur': 'nouveau.parrain@example.com',
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Godfather.objects.count(), 2)
        student = Student.objects.get()
        self.assertEqual(student.godfather.full_name, 'Nouveau Parrain')
        self.assertEqual(student.godfather.email, 'nouveau.parrain@example.com')

    def test_form_uses_existing_bac_school_name_when_selected(self):
        payload = self._valid_payload()
        payload['bac_etablissement_existant'] = self.existing_school.pk
        payload['bac_etablissement'] = ''

        form = InscriptionCompleteForm(data=payload)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['bac_etablissement'], 'Lycée Général Leclerc')

    def test_post_with_is_complete_checked_marks_metadata_complete(self):
        payload = self._valid_payload()
        payload['is_complete'] = 'on'

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        self.assertTrue(student.metadata.is_complete)

    def test_post_with_save_and_new_redirects_back_to_empty_form(self):
        payload = self._valid_payload()
        payload['save_action'] = 'save_and_new'

        response = self.client.post(self.url, payload, follow=True)

        self.assertRedirects(response, self.url)
        self.assertEqual(Student.objects.count(), 1)
        self.assertFalse(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].fields['is_complete'].initial)

    def test_post_without_save_and_new_redirects_to_student_detail(self):
        payload = self._valid_payload()

        response = self.client.post(self.url, payload)

        student = Student.objects.get()
        self.assertRedirects(
            response,
            reverse('main:etudiant_detail', kwargs={'pk': student.matricule}),
            fetch_redirect_response=False,
        )


class InscriptionEditViewTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_editor',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True,
        )
        self.next_academic_year = AcademicYear.objects.create(
            start_at=date(2025, 9, 1),
            end_at=date(2026, 6, 30),
            is_active=False,
        )
        self.level = Level.objects.create(name='Licence 1')
        self.next_level = Level.objects.create(name='Licence 2')
        self.program = Program.objects.create(name='Informatique')
        self.next_program = Program.objects.create(name='Réseaux')
        self.school = School.objects.create(name='Collège A', level='secondary')
        self.next_school = School.objects.create(name='Collège B', level='secondary')
        self.godfather = Godfather.objects.create(full_name='Parrain 1')
        self.next_godfather = Godfather.objects.create(full_name='Parrain 2')

        self.metadata = StudentMetaData.objects.create(
            original_country='Cameroun',
            is_complete=False,
        )
        self.student = Student.objects.create(
            matricule='INT_EDIT_001',
            firstname='Alice',
            lastname='Martin',
            gender='F',
            lang='fr',
            phone_number='+237600000000',
            email='alice@example.com',
            status='pending',
            metadata=self.metadata,
            school=self.school,
            program=self.program,
            godfather=self.godfather,
        )
        self.student_level = StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.edit_url = reverse('main:inscription_edit', kwargs={'pk': self.student.matricule})

    def test_inscription_detail_displays_edit_action(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier la pré-inscription')
        self.assertContains(response, self.edit_url)

    def test_get_inscription_edit_displays_complete_form(self):
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier la pré-inscription')
        self.assertContains(response, 'multipart/form-data')
        self.assertContains(response, 'Niveau d\'inscription')
        self.assertContains(response, 'Documents d\'inscription')

    def test_post_inscription_edit_updates_student_metadata_and_level(self):
        payload = {
            'firstname': 'Alicia',
            'lastname': 'Mballa',
            'date_naiss': '2001-02-03',
            'gender': 'M',
            'lang': 'en',
            'phone_number': '+237611111111',
            'email': 'alicia@example.com',
            'status': 'rejected',
            'school': self.next_school.pk,
            'program': self.next_program.pk,
            'godfather': self.next_godfather.pk,
            'level': self.next_level.pk,
            'academic_year': self.next_academic_year.pk,
            'mother_full_name': 'Marie Mballa',
            'mother_live_city': 'Douala',
            'mother_email': 'marie@example.com',
            'mother_occupation': 'Commerçante',
            'mother_phone_number': '+237622222222',
            'father_full_name': 'Jean Mballa',
            'father_live_city': 'Yaoundé',
            'father_email': 'jean@example.com',
            'father_occupation': 'Professeur',
            'father_phone_number': '+237633333333',
            'original_country': 'Gabon',
            'original_region': 'Estuaire',
            'original_department': 'Libreville',
            'original_district': '1er',
            'residence_city': 'Bafoussam',
            'residence_quarter': 'Djeleng',
            'is_complete': 'on',
        }

        response = self.client.post(self.edit_url, payload)

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()
        self.student_level.refresh_from_db()

        self.assertEqual(self.student.firstname, 'Alicia')
        self.assertEqual(self.student.lastname, 'Mballa')
        self.assertEqual(self.student.gender, 'M')
        self.assertEqual(self.student.lang, 'en')
        self.assertEqual(self.student.status, 'rejected')
        self.assertEqual(self.student.school, self.next_school)
        self.assertEqual(self.student.program, self.next_program)
        self.assertEqual(self.student.godfather, self.next_godfather)
        self.assertTrue(self.student.metadata.is_complete)
        self.assertEqual(self.student.metadata.original_country, 'Gabon')
        self.assertEqual(self.student.metadata.residence_city, 'Bafoussam')
        self.assertEqual(self.student_level.level, self.next_level)
        self.assertEqual(self.student_level.academic_year, self.next_academic_year)
        self.assertTrue(self.student_level.is_active)
        self.assertEqual(self.student.student_levels.count(), 1)


class PreInscriptionPdfExportTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='scholar_pdf',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 1')
        self.program = Program.objects.create(name='Informatique')
        self.other_program = Program.objects.create(name='Gestion')

        self.metadata = StudentMetaData.objects.create(
            original_country='Cameroun',
            is_complete=True,
            acte_naissance=SimpleUploadedFile(
                'acte_naissance.pdf',
                self._build_test_pdf('Acte de naissance de test'),
                content_type='application/pdf',
            ),
            preuve_baccalaureat=SimpleUploadedFile(
                'preuve_baccalaureat.png',
                self._build_test_png(),
                content_type='image/png',
            ),
        )
        self.student = Student.objects.create(
            matricule='PDF001',
            firstname='Jean',
            lastname='Dupont',
            gender='M',
            lang='fr',
            phone_number='+237600000001',
            email='jean.dupont@example.com',
            status='pending',
            metadata=self.metadata,
            program=self.program,
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.second_student = Student.objects.create(
            matricule='PDF002',
            firstname='Alice',
            lastname='Ngono',
            gender='F',
            lang='fr',
            phone_number='+237600000002',
            email='alice.ngono@example.com',
            status='approved',
            metadata=StudentMetaData.objects.create(original_country='Cameroun', is_complete=False),
            program=self.program,
        )
        StudentLevel.objects.create(
            student=self.second_student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.excluded_student = Student.objects.create(
            matricule='PDF003',
            firstname='Marc',
            lastname='Essono',
            gender='M',
            lang='en',
            phone_number='+237600000003',
            email='marc.essono@example.com',
            status='pending',
            metadata=StudentMetaData.objects.create(original_country='Cameroun', is_complete=True),
            program=self.other_program,
        )
        StudentLevel.objects.create(
            student=self.excluded_student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.list_url = reverse('main:inscriptions')
        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.print_url = reverse('main:inscription_print_pdf', kwargs={'pk': self.student.matricule})
        self.batch_print_url = reverse('main:inscriptions_print_pdf')

    def _build_test_pdf(self, text):
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)
        pdf_canvas.drawString(72, 760, text)
        pdf_canvas.showPage()
        pdf_canvas.save()
        return buffer.getvalue()

    def _build_test_png(self):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color='white').save(buffer, format='PNG')
        return buffer.getvalue()

    def test_inscription_detail_displays_pdf_print_link(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.print_url)
        self.assertContains(response, 'Imprimer le dossier PDF complet')

    def test_pdf_export_returns_combined_pdf_with_annexes(self):
        response = self.client.get(self.print_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('preinscription_PDF001.pdf', response['Content-Disposition'])

        reader = PdfReader(BytesIO(response.content))
        self.assertGreaterEqual(len(reader.pages), 5)

        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        self.assertIn('Jean Dupont', full_text)
        self.assertIn('PDF001', full_text)
        self.assertIn('Acte de naissance', full_text)
        self.assertIn('Preuve d\'obtention du baccalauréat', full_text)

    def test_inscriptions_list_displays_filtered_batch_pdf_export_action(self):
        response = self.client.get(self.list_url, {'program': self.program.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.batch_print_url)
        self.assertContains(response, 'Exporter les dossiers filtrés en PDF')
        self.assertContains(response, 'filteredPdfExportModal')
        self.assertContains(response, '2 pré-inscription(s) trouvée(s)')
        self.assertContains(response, f'name="program" value="{self.program.pk}"')
        self.assertContains(response, 'Vous allez générer un seul PDF combiné')

    def test_batch_pdf_export_returns_only_filtered_preinscriptions(self):
        response = self.client.get(self.batch_print_url, {'program': self.program.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('preinscriptions_filtrees.pdf', response['Content-Disposition'])

        reader = PdfReader(BytesIO(response.content))
        self.assertGreaterEqual(len(reader.pages), 6)

        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        self.assertIn('Jean Dupont', full_text)
        self.assertIn('PDF001', full_text)
        self.assertIn('Alice Ngono', full_text)
        self.assertIn('PDF002', full_text)
        self.assertNotIn('Marc Essono', full_text)
        self.assertNotIn('PDF003', full_text)


class EtudiantProfilePhotoTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='scholar_photo',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 1')
        self.program = Program.objects.create(name='Informatique')
        self.school = School.objects.create(name='Collège Photo', level='secondary')
        self.metadata = StudentMetaData.objects.create(original_country='Cameroun')

        self.student = Student.objects.create(
            matricule='PHOTO001',
            firstname='Paul',
            lastname='Atangana',
            gender='M',
            lang='fr',
            email='paul@example.com',
            status='registered',
            metadata=self.metadata,
            school=self.school,
            program=self.program,
            profile_photo=SimpleUploadedFile(
                'photo-initiale.png',
                self._build_test_png(color='navy'),
                content_type='image/png',
            ),
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.detail_url = reverse('main:etudiant_detail', kwargs={'pk': self.student.matricule})
        self.edit_url = reverse('main:etudiant_edit', kwargs={'pk': self.student.matricule})
        self.list_url = reverse('main:etudiants')

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

    def _edit_payload(self, **overrides):
        payload = {
            'firstname': 'Paul',
            'lastname': 'Atangana',
            'date_naiss': '',
            'gender': 'M',
            'lang': 'fr',
            'phone_number': '',
            'email': 'paul@example.com',
            'status': 'registered',
            'school': self.school.pk,
            'program': self.program.pk,
            'godfather': '',
            'level': self.level.pk,
            'academic_year': self.academic_year.pk,
            'mother_full_name': '',
            'mother_live_city': '',
            'mother_email': '',
            'mother_occupation': '',
            'mother_phone_number': '',
            'father_full_name': '',
            'father_live_city': '',
            'father_email': '',
            'father_occupation': '',
            'father_phone_number': '',
            'original_country': 'Cameroun',
            'original_region': '',
            'original_department': '',
            'original_district': '',
            'residence_city': '',
            'residence_quarter': '',
            'is_complete': '',
        }
        payload.update(overrides)
        return payload

    def test_etudiant_detail_displays_profile_photo(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo de profil')
        self.assertContains(response, self.student.profile_photo.url)

    def test_etudiants_list_displays_profile_photo(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo')
        self.assertContains(response, self.student.profile_photo.url)

    def test_etudiant_edit_updates_profile_photo(self):
        payload = self._edit_payload(
            profile_photo=SimpleUploadedFile(
                'photo-mise-a-jour.png',
                self._build_test_png(color='green'),
                content_type='image/png',
            ),
        )

        response = self.client.post(self.edit_url, payload)

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()

        self.assertTrue(bool(self.student.profile_photo))
        self.assertIn('photo-mise-a-jour', self.student.profile_photo.name)

    def test_etudiant_edit_can_remove_profile_photo(self):
        response = self.client.post(self.edit_url, self._edit_payload(remove_profile_photo='on'))

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()

        self.assertFalse(bool(self.student.profile_photo))
