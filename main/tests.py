import os
from io import BytesIO
from tempfile import TemporaryDirectory
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django import forms
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from rest_framework.test import APIClient

from academic.document_requirements import PROGRAM_DOCUMENT_FIELD_NAMES
from academic.models import AcademicYear, Level, Program, ProgramDocumentRequirement, Speciality
from accounts.models import BaseUser, Godfather
from audit.models import AuditLog
from main.forms import InscriptionCompleteForm, SecondaryDiplomaForm, UniversityLevelForm
from main.models import SystemSettings
from payments.models import Payment, PaymentInstallment
from prospection.models import Agent
from schools.models import School, SecondaryDiploma, UniversityLevel
from students.models import OfficialDocument, Student, StudentLevel, StudentMetaData


def set_program_required_documents(program, required_fields):
    configuration = ProgramDocumentRequirement.get_for_program(program)
    for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
        setattr(configuration, field_name, field_name in required_fields)
    configuration.save(update_fields=list(PROGRAM_DOCUMENT_FIELD_NAMES))
    return configuration


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NouvelleInscriptionViewTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

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
        self.program = Program.objects.create(name='Informatique')
        self.speciality_1 = Speciality.objects.create(name='Génie logiciel', program=self.program)
        self.speciality_2 = Speciality.objects.create(name='Réseaux', program=self.program)
        self.speciality_3 = Speciality.objects.create(name='Data', program=self.program)
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
        self.existing_university = School.objects.create(
            name='Université de Yaoundé I',
            phone_number='+237688888881',
            level='higher',
        )
        self.url = reverse('main:nouvelle_inscription')

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

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
            'secondary_diplomas-TOTAL_FORMS': '0',
            'secondary_diplomas-INITIAL_FORMS': '0',
            'secondary_diplomas-MIN_NUM_FORMS': '0',
            'secondary_diplomas-MAX_NUM_FORMS': '1000',
            'university_levels-TOTAL_FORMS': '0',
            'university_levels-INITIAL_FORMS': '0',
            'university_levels-MIN_NUM_FORMS': '0',
            'university_levels-MAX_NUM_FORMS': '1000',
        }

    def test_get_displays_existing_godfather_selector(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo de profil')
        self.assertContains(response, 'Parrain/tuteur existant')
        self.assertContains(response, 'Parrain Existant')
        self.assertContains(response, 'Diplômes du secondaire')
        self.assertContains(response, 'Cursus universitaire')
        self.assertContains(response, 'Lycée Général Leclerc')
        self.assertContains(response, 'secondary_diplomas-TOTAL_FORMS')
        self.assertContains(response, 'Dossier complet')
        self.assertNotContains(response, 'secondary_diplomas-0-name')
        self.assertNotContains(response, 'university_levels-0-level_name')
        self.assertFalse(response.context['form'].fields['is_complete'].initial)
        self.assertEqual(response.context['secondary_diploma_formset'].total_form_count(), 0)
        self.assertEqual(response.context['university_level_formset'].total_form_count(), 0)
        self.assertTrue(all(not entry['should_display'] for entry in response.context['form'].program_document_entries))

    def test_form_fields_use_expected_dropdown_choices(self):
        form = InscriptionCompleteForm()
        secondary_form = SecondaryDiplomaForm()
        university_form = UniversityLevelForm()

        self.assertIsInstance(form.fields['lien_parente_urgence'].widget, forms.Select)
        self.assertIn(('oncle', 'Oncle'), list(form.fields['lien_parente_urgence'].choices))
        self.assertIn(('tante', 'Tante'), list(form.fields['lien_parente_urgence'].choices))

        self.assertIsInstance(secondary_form.fields['name'].widget, forms.Select)
        self.assertIn(('BEPC', 'BEPC'), list(secondary_form.fields['name'].choices))
        self.assertIn(('Baccalauréat', 'Baccalauréat'), list(secondary_form.fields['name'].choices))

        self.assertIsInstance(secondary_form.fields['mention'].widget, forms.Select)
        self.assertIn(('Passable', 'Passable'), list(secondary_form.fields['mention'].choices))
        self.assertIn(('Très bien', 'Très bien'), list(secondary_form.fields['mention'].choices))

        self.assertIsInstance(university_form.fields['level_name'].widget, forms.Select)
        self.assertIn(('Niveau 1', 'Niveau 1'), list(university_form.fields['level_name'].choices))
        self.assertIn(('Niveau 3', 'Niveau 3'), list(university_form.fields['level_name'].choices))

        self.assertIsInstance(university_form.fields['diploma_name'].widget, forms.Select)
        self.assertIn(('Licence', 'Licence'), list(university_form.fields['diploma_name'].choices))
        self.assertIn(('Doctorat', 'Doctorat'), list(university_form.fields['diploma_name'].choices))

    def test_post_with_profile_photo_persists_file(self):
        payload = self._valid_payload()
        payload['profile_photo'] = SimpleUploadedFile(
            'photo-preinscription.png',
            self._build_test_png(color='orange'),
            content_type='image/png',
        )

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        self.assertTrue(bool(student.profile_photo))
        self.assertIn('photo-preinscription', student.profile_photo.name)

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

    def test_post_persists_three_specialities_and_associates_existing_bac_school(self):
        set_program_required_documents(self.program, [])
        payload = self._valid_payload()
        payload.update({
            'programme': self.program.pk,
            'specialite_souhaitee_1': self.speciality_1.pk,
            'specialite_souhaitee_2': self.speciality_2.pk,
            'specialite_souhaitee_3': self.speciality_3.pk,
            'secondary_diplomas-TOTAL_FORMS': '1',
            'secondary_diplomas-0-name': 'Baccalauréat',
            'secondary_diplomas-0-serie': 'C',
            'secondary_diplomas-0-obtained_year': '2023',
            'secondary_diplomas-0-mention': 'Bien',
            'secondary_diplomas-0-school_existant': self.existing_school.pk,
            'secondary_diplomas-0-school_name': '',
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        diploma = SecondaryDiploma.objects.get(student=student)
        self.assertEqual(student.program, self.program)
        self.assertEqual(student.school, self.existing_school)
        self.assertEqual(diploma.school, self.existing_school)
        self.assertEqual(diploma.name, 'Baccalauréat')
        self.assertEqual(student.specialite_souhaitee_1, 'Génie logiciel')
        self.assertEqual(student.specialite_souhaitee_2, 'Réseaux')
        self.assertEqual(student.specialite_souhaitee_3, 'Data')

    def test_post_creates_university_level_with_existing_university(self):
        payload = self._valid_payload()
        payload.update({
            'university_levels-TOTAL_FORMS': '1',
            'university_levels-0-level_name': 'Niveau 1',
            'university_levels-0-diploma_name': 'Licence',
            'university_levels-0-speciality': 'Informatique',
            'university_levels-0-academic_year': '2023/2024',
            'university_levels-0-university_existant': self.existing_university.pk,
            'university_levels-0-university_name': '',
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        university_level = UniversityLevel.objects.get(student=student)
        self.assertEqual(university_level.university, self.existing_university)
        self.assertEqual(university_level.level_name, 'Niveau 1')
        self.assertEqual(university_level.diploma_name, 'Licence')
        self.assertEqual(university_level.speciality, 'Informatique')

    def test_post_sets_student_school_from_highest_university_level(self):
        payload = self._valid_payload()
        payload.update({
            'secondary_diplomas-TOTAL_FORMS': '1',
            'secondary_diplomas-0-name': 'Baccalauréat',
            'secondary_diplomas-0-serie': 'C',
            'secondary_diplomas-0-obtained_year': '2023',
            'secondary_diplomas-0-mention': 'Bien',
            'secondary_diplomas-0-school_existant': self.existing_school.pk,
            'secondary_diplomas-0-school_name': '',
            'university_levels-TOTAL_FORMS': '2',
            'university_levels-0-level_name': 'Niveau 1',
            'university_levels-0-diploma_name': 'BTS',
            'university_levels-0-speciality': 'Gestion',
            'university_levels-0-academic_year': '2022/2023',
            'university_levels-0-university_existant': self.existing_university.pk,
            'university_levels-0-university_name': '',
        })

        higher_university = School.objects.create(name='Université de Douala', level='higher')
        payload.update({
            'university_levels-1-level_name': 'Niveau 5',
            'university_levels-1-diploma_name': 'Master',
            'university_levels-1-speciality': 'Informatique',
            'university_levels-1-academic_year': '2024/2025',
            'university_levels-1-university_existant': higher_university.pk,
            'university_levels-1-university_name': '',
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        self.assertEqual(student.school, higher_university)

    def test_post_creates_and_associates_manual_bac_school(self):
        payload = self._valid_payload()
        payload.update({
            'secondary_diplomas-TOTAL_FORMS': '1',
            'secondary_diplomas-0-name': 'Baccalauréat',
            'secondary_diplomas-0-serie': 'D',
            'secondary_diplomas-0-obtained_year': '2022',
            'secondary_diplomas-0-mention': 'Assez bien',
            'secondary_diplomas-0-school_existant': '',
            'secondary_diplomas-0-school_name': 'Collège Adventiste de Test',
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        diploma = SecondaryDiploma.objects.get(student=student)
        self.assertEqual(student.school.name, 'Collège Adventiste de Test')
        self.assertEqual(student.school.level, 'secondary')
        self.assertEqual(diploma.school, student.school)
        self.assertTrue(School.objects.filter(name='Collège Adventiste de Test', level='secondary').exists())

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

    def test_post_sends_pre_inscription_email_to_student(self):
        payload = self._valid_payload()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['jane.doe@example.com'])
        self.assertIn('pré-inscription', mail.outbox[0].subject.lower())
        self.assertIn(student.matricule, mail.outbox[0].body)
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertIn(student.matricule, mail.outbox[0].alternatives[0][0])

    def test_get_specialities_by_program_returns_internal_document_configuration(self):
        set_program_required_documents(
            self.program,
            ['acte_naissance', 'decharge_equivalence', 'releve_notes_master1'],
        )

        response = self.client.get(
            reverse('main:get_specialities_by_program'),
            {
                'program_id': self.program.pk,
                'documents_mode': 'admin_only_optional',
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(len(payload['specialities']), 3)
        self.assertEqual(len(payload['documents']), len(PROGRAM_DOCUMENT_FIELD_NAMES))

        documents_by_field = {
            document['field_name']: document
            for document in payload['documents']
        }
        self.assertTrue(documents_by_field['acte_naissance']['should_display'])
        self.assertTrue(documents_by_field['decharge_equivalence']['should_display'])
        self.assertTrue(documents_by_field['releve_notes_master1']['should_display'])
        self.assertFalse(documents_by_field['acte_naissance']['is_required'])
        self.assertFalse(documents_by_field['decharge_equivalence']['is_required'])
        self.assertFalse(documents_by_field['releve_notes_master1']['is_required'])
        self.assertFalse(documents_by_field['preuve_baccalaureat']['should_display'])
        self.assertFalse(documents_by_field['photocopie_bts_hnd']['should_display'])
        self.assertFalse(documents_by_field['preuve_baccalaureat']['is_required'])
        self.assertFalse(documents_by_field['photocopie_bts_hnd']['is_required'])

    def test_form_allows_missing_program_documents_on_internal_preinscription(self):
        set_program_required_documents(self.program, ['decharge_equivalence'])
        payload = self._valid_payload()
        payload['programme'] = self.program.pk

        form = InscriptionCompleteForm(data=payload)

        self.assertTrue(form.is_valid())
        entries_by_field = {
            entry['field_name']: entry
            for entry in form.program_document_entries
        }
        self.assertTrue(entries_by_field['decharge_equivalence']['should_display'])
        self.assertFalse(entries_by_field['decharge_equivalence']['is_required'])
        self.assertFalse(entries_by_field['preuve_baccalaureat']['should_display'])

    def test_post_persists_additional_program_documents(self):
        payload = self._valid_payload()
        payload.update({
            'decharge_equivalence': SimpleUploadedFile(
                'decharge-equivalence.pdf',
                self._build_test_png(color='blue'),
                content_type='application/pdf',
            ),
            'releve_notes_master1': SimpleUploadedFile(
                'releve-master1.pdf',
                self._build_test_png(color='green'),
                content_type='application/pdf',
            ),
            'photocopie_bts_hnd': SimpleUploadedFile(
                'bts-hnd.pdf',
                self._build_test_png(color='red'),
                content_type='application/pdf',
            ),
        })

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get()
        self.assertTrue(bool(student.metadata.decharge_equivalence))
        self.assertTrue(bool(student.metadata.releve_notes_master1))
        self.assertTrue(bool(student.metadata.photocopie_bts_hnd))
        self.assertIn('decharge-equivalence', student.metadata.decharge_equivalence.name)
        self.assertIn('releve-master1', student.metadata.releve_notes_master1.name)
        self.assertIn('bts-hnd', student.metadata.photocopie_bts_hnd.name)


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
        self.speciality_1 = Speciality.objects.create(name='Génie logiciel', program=self.program)
        self.speciality_2 = Speciality.objects.create(name='Maintenance', program=self.program)
        self.speciality_3 = Speciality.objects.create(name='Data', program=self.program)
        self.next_speciality_1 = Speciality.objects.create(name='Télécoms', program=self.next_program)
        self.next_speciality_2 = Speciality.objects.create(name='Cybersécurité', program=self.next_program)
        self.next_speciality_3 = Speciality.objects.create(name='Cloud', program=self.next_program)
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
        self.assertContains(response, 'Ou saisir un autre établissement')
        self.assertContains(response, 'Spécialité souhaitée 1')

    def test_post_inscription_edit_updates_student_metadata_and_level(self):
        set_program_required_documents(self.next_program, [])
        payload = {
            'firstname': 'Alicia',
            'lastname': 'Mballa',
            'date_naiss': '2001-02-03',
            'gender': 'M',
            'lang': 'en',
            'phone_number': '+237611111111',
            'email': 'alicia@example.com',
            'status': 'rejected',
            'bac_etablissement_existant': self.next_school.pk,
            'program': self.next_program.pk,
            'specialite_souhaitee_1': self.next_speciality_1.pk,
            'specialite_souhaitee_2': self.next_speciality_2.pk,
            'specialite_souhaitee_3': self.next_speciality_3.pk,
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

        if response.status_code != 302:
            self.fail(
                f"student={response.context['student_form'].errors.as_json()} "
                f"metadata={response.context['metadata_form'].errors.as_json()} "
                f"level={response.context['student_level_form'].errors.as_json()} "
                f"secondary={response.context['secondary_diploma_formset'].management_form.errors.as_json()} "
                f"university={response.context['university_level_formset'].management_form.errors.as_json()}"
            )

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
        self.assertEqual(self.student.specialite_souhaitee_1, self.next_speciality_1.name)
        self.assertEqual(self.student.specialite_souhaitee_2, self.next_speciality_2.name)
        self.assertEqual(self.student.specialite_souhaitee_3, self.next_speciality_3.name)
        self.assertEqual(self.student.godfather, self.next_godfather)
        self.assertTrue(self.student.metadata.is_complete)
        self.assertEqual(self.student.metadata.original_country, 'Gabon')
        self.assertEqual(self.student.metadata.residence_city, 'Bafoussam')
        self.assertEqual(self.student_level.level, self.next_level)
        self.assertEqual(self.student_level.academic_year, self.next_academic_year)
        self.assertTrue(self.student_level.is_active)
        self.assertEqual(self.student.student_levels.count(), 1)

    def test_post_inscription_edit_creates_manual_bac_school_and_associates_it(self):
        set_program_required_documents(self.program, [])
        payload = {
            'firstname': self.student.firstname,
            'lastname': self.student.lastname,
            'date_naiss': '2001-02-03',
            'gender': self.student.gender,
            'lang': self.student.lang,
            'phone_number': self.student.phone_number,
            'email': self.student.email,
            'status': self.student.status,
            'bac_etablissement': 'Lycée Technique de Test',
            'program': self.program.pk,
            'specialite_souhaitee_1': self.speciality_1.pk,
            'specialite_souhaitee_2': self.speciality_2.pk,
            'specialite_souhaitee_3': self.speciality_3.pk,
            'godfather': self.godfather.pk,
            'level': self.level.pk,
            'academic_year': self.academic_year.pk,
            'original_country': 'Cameroun',
        }

        response = self.client.post(self.edit_url, payload)

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()

        self.assertEqual(self.student.school.name, 'Lycée Technique de Test')
        self.assertEqual(self.student.school.level, 'secondary')
        self.assertTrue(School.objects.filter(name='Lycée Technique de Test', level='secondary').exists())
        self.assertEqual(self.student.specialite_souhaitee_1, self.speciality_1.name)
        self.assertEqual(self.student.specialite_souhaitee_2, self.speciality_2.name)
        self.assertEqual(self.student.specialite_souhaitee_3, self.speciality_3.name)

    def test_post_inscription_edit_allows_missing_documents_for_selected_program(self):
        set_program_required_documents(self.next_program, ['decharge_equivalence'])
        payload = {
            'firstname': self.student.firstname,
            'lastname': self.student.lastname,
            'date_naiss': '2001-02-03',
            'gender': self.student.gender,
            'lang': self.student.lang,
            'phone_number': self.student.phone_number,
            'email': self.student.email,
            'status': self.student.status,
            'bac_etablissement_existant': self.next_school.pk,
            'program': self.next_program.pk,
            'specialite_souhaitee_1': self.next_speciality_1.pk,
            'specialite_souhaitee_2': self.next_speciality_2.pk,
            'specialite_souhaitee_3': self.next_speciality_3.pk,
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
            'original_country': 'Cameroun',
            'original_region': 'Centre',
            'original_department': 'Mfoundi',
            'original_district': 'Yaoundé 1',
            'residence_city': 'Yaoundé',
            'residence_quarter': 'Bastos',
            'is_complete': 'on',
        }

        response = self.client.post(self.edit_url, payload)

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()
        self.assertEqual(self.student.program, self.next_program)


class InscriptionEditDocumentFilesTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='scholar_editor_docs',
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
        self.speciality_1 = Speciality.objects.create(name='Génie logiciel', program=self.program)
        self.speciality_2 = Speciality.objects.create(name='Maintenance', program=self.program)
        self.speciality_3 = Speciality.objects.create(name='Data', program=self.program)
        self.school = School.objects.create(name='Collège Documents', level='secondary')
        self.godfather = Godfather.objects.create(full_name='Parrain Documents')

        self.metadata = StudentMetaData.objects.create(
            original_country='Cameroun',
            acte_naissance=SimpleUploadedFile(
                'acte-inscription.pdf',
                self._build_test_pdf('Acte de naissance'),
                content_type='application/pdf',
            ),
            preuve_baccalaureat=SimpleUploadedFile(
                'baccalaureat-inscription.pdf',
                self._build_test_pdf('Preuve baccalauréat'),
                content_type='application/pdf',
            ),
            certificat_nationalite=SimpleUploadedFile(
                'certificat-nationalite.pdf',
                self._build_test_pdf('Certificat nationalité'),
                content_type='application/pdf',
            ),
            releve_notes_last_class=SimpleUploadedFile(
                'releve-notes.pdf',
                self._build_test_pdf('Relevé de notes'),
                content_type='application/pdf',
            ),
            justificatif_dernier_diplome=SimpleUploadedFile(
                'dernier-diplome.pdf',
                self._build_test_pdf('Justificatif diplôme'),
                content_type='application/pdf',
            ),
            bulletins_terminale=SimpleUploadedFile(
                'bulletins-terminale.pdf',
                self._build_test_pdf('Bulletins terminale'),
                content_type='application/pdf',
            ),
            decharge_equivalence=SimpleUploadedFile(
                'decharge-equivalence.pdf',
                self._build_test_pdf('Décharge équivalence'),
                content_type='application/pdf',
            ),
            releve_notes_master1=SimpleUploadedFile(
                'releve-master1.pdf',
                self._build_test_pdf('Relevé Master 1'),
                content_type='application/pdf',
            ),
            photocopie_bts_hnd=SimpleUploadedFile(
                'bts-hnd.pdf',
                self._build_test_pdf('BTS HND'),
                content_type='application/pdf',
            ),
        )
        self.student = Student.objects.create(
            matricule='INT_EDIT_DOC_001',
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
            profile_photo=SimpleUploadedFile(
                'logo-etudiant.png',
                self._build_test_png(color='purple'),
                content_type='image/png',
            ),
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.edit_url = reverse('main:inscription_edit', kwargs={'pk': self.student.matricule})

    def _build_test_pdf(self, title):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(72, 800, title)
        pdf.save()
        return buffer.getvalue()

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

    def _edit_payload(self, **overrides):
        payload = {
            'firstname': self.student.firstname,
            'lastname': self.student.lastname,
            'date_naiss': '',
            'gender': self.student.gender,
            'lang': self.student.lang,
            'phone_number': self.student.phone_number,
            'email': self.student.email,
            'status': self.student.status,
            'bac_etablissement_existant': self.school.pk,
            'bac_etablissement': '',
            'program': self.program.pk,
            'specialite_souhaitee_1': self.speciality_1.pk,
            'specialite_souhaitee_2': self.speciality_2.pk,
            'specialite_souhaitee_3': self.speciality_3.pk,
            'godfather': self.godfather.pk,
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

    def test_get_inscription_edit_displays_existing_filenames_and_remove_options(self):
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'logo-etudiant.png')
        self.assertContains(response, 'acte-inscription.pdf')
        self.assertContains(response, 'baccalaureat-inscription.pdf')
        self.assertContains(response, 'certificat-nationalite.pdf')
        self.assertContains(response, 'releve-notes.pdf')
        self.assertContains(response, 'dernier-diplome.pdf')
        self.assertContains(response, 'bulletins-terminale.pdf')
        self.assertContains(response, 'decharge-equivalence.pdf')
        self.assertContains(response, 'releve-master1.pdf')
        self.assertContains(response, 'bts-hnd.pdf')
        self.assertContains(response, 'Supprimer la photo actuelle')
        self.assertContains(response, 'Supprimer le document actuel', count=9)

    def test_inscription_detail_displays_additional_program_documents(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'decharge-equivalence.pdf')
        self.assertContains(response, 'releve-master1.pdf')
        self.assertContains(response, 'bts-hnd.pdf')

    def test_post_inscription_edit_can_remove_existing_files(self):
        set_program_required_documents(self.program, [])
        old_photo_path = self.student.profile_photo.path
        old_acte_path = self.student.metadata.acte_naissance.path
        old_bac_path = self.student.metadata.preuve_baccalaureat.path
        old_certificat_path = self.student.metadata.certificat_nationalite.path

        response = self.client.post(
            self.edit_url,
            self._edit_payload(
                remove_profile_photo='on',
                remove_acte_naissance='on',
                remove_preuve_baccalaureat='on',
                remove_certificat_nationalite='on',
            ),
        )

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()
        self.metadata.refresh_from_db()

        self.assertFalse(bool(self.student.profile_photo))
        self.assertFalse(bool(self.metadata.acte_naissance))
        self.assertFalse(bool(self.metadata.preuve_baccalaureat))
        self.assertFalse(bool(self.metadata.certificat_nationalite))
        self.assertTrue(bool(self.metadata.releve_notes_last_class))
        self.assertTrue(bool(self.metadata.justificatif_dernier_diplome))
        self.assertTrue(bool(self.metadata.bulletins_terminale))

        self.assertFalse(os.path.exists(old_photo_path))
        self.assertFalse(os.path.exists(old_acte_path))
        self.assertFalse(os.path.exists(old_bac_path))
        self.assertFalse(os.path.exists(old_certificat_path))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PreInscriptionApprovalNotificationTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_approve',
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
        self.speciality = Speciality.objects.create(name='Génie logiciel', program=self.program)
        self.other_program = Program.objects.create(name='Gestion')
        self.other_speciality = Speciality.objects.create(name='Finance', program=self.other_program)
        self.student = Student.objects.create(
            matricule='INT_PENDING_001',
            firstname='Merveille',
            lastname='Biloa',
            gender='F',
            lang='fr',
            email='merveille@example.com',
            status='pending',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )
        self.student_level = StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )
        self.approve_url = reverse('main:inscription_approve', kwargs={'pk': self.student.matricule})
        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})

    def test_inscription_detail_displays_speciality_selector_in_approval_modal(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="speciality"')
        self.assertContains(response, 'Sélectionner la spécialité')
        self.assertContains(response, self.speciality.name)

    def test_approving_pre_inscription_requires_program_speciality(self):
        response = self.client.post(self.approve_url)

        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.student_level.refresh_from_db()
        self.assertEqual(self.student.status, 'pending')
        self.assertIsNone(self.student_level.speciality)
        self.assertEqual(len(mail.outbox), 0)

    def test_approving_pre_inscription_rejects_speciality_from_another_program(self):
        response = self.client.post(self.approve_url, {'speciality': self.other_speciality.pk})

        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.student_level.refresh_from_db()
        self.assertEqual(self.student.status, 'pending')
        self.assertIsNone(self.student_level.speciality)
        self.assertEqual(len(mail.outbox), 0)

    def test_approving_pre_inscription_saves_speciality_and_sends_validation_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.approve_url, {'speciality': self.speciality.pk})

        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.student_level.refresh_from_db()
        self.assertEqual(self.student.status, 'approved')
        self.assertEqual(self.student_level.speciality, self.speciality)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['merveille@example.com'])
        self.assertIn('validation', mail.outbox[0].subject.lower())
        self.assertIn('a été validée', mail.outbox[0].body)
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertIn(self.student.matricule, mail.outbox[0].alternatives[0][0])


class PreInscriptionCompletionTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_complete',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)
        self.program = Program.objects.create(name='Droit')
        self.metadata = StudentMetaData.objects.create(original_country='Cameroun', is_complete=False)
        self.student = Student.objects.create(
            matricule='INT_COMPLETE_001',
            firstname='Brice',
            lastname='Essama',
            gender='M',
            lang='fr',
            email='brice@example.com',
            status='pending',
            metadata=self.metadata,
            program=self.program,
        )
        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.mark_complete_url = reverse('main:inscription_mark_complete', kwargs={'pk': self.student.matricule})

    def test_inscription_detail_displays_mark_complete_button_when_metadata_is_incomplete(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marquer ce dossier complet')
        self.assertContains(response, self.mark_complete_url)

    def test_mark_complete_updates_metadata_and_hides_button(self):
        response = self.client.post(self.mark_complete_url, follow=True)

        self.assertRedirects(response, self.detail_url)
        self.metadata.refresh_from_db()
        self.assertTrue(self.metadata.is_complete)
        self.assertContains(response, 'a été marqué comme complet')
        self.assertNotContains(response, 'Marquer ce dossier complet')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PreInscriptionRegistrationTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_register',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2025, 9, 1),
            end_at=date(2026, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 3')
        self.program = Program.objects.create(name='Licence gestion')

        Student.objects.create(
            matricule='EXISTING_REGISTERED',
            dossier_number='L0164',
            firstname='Déjà',
            lastname='Inscrit',
            gender='M',
            lang='fr',
            status='registered',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )

        self.student = Student.objects.create(
            matricule='INT_APPROVED_001',
            firstname='Cécilia Audrey Raphaelle',
            lastname='Mapubi',
            gender='F',
            lang='fr',
            phone_number='+237699999999',
            email='cecilia@example.com',
            status='approved',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )
        self.first_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche 1',
            order_number=1,
            amount=50000,
            due_date=date(2025, 10, 15),
        )
        self.second_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche 2',
            order_number=2,
            amount=70000,
            due_date=date(2025, 12, 15),
        )
        Payment.objects.create(
            student=self.student,
            installment=self.first_installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=50000,
            payment_date=timezone.make_aware(datetime.combine(date(2025, 9, 10), datetime.min.time())),
            receipt_number='REC-REG-001',
            transaction_id='TX-REG-001',
            source='cash',
        )

        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.register_url = reverse('main:inscription_register', kwargs={'pk': self.student.matricule})
        self.expected_matricule = '251301659'

    def test_inscription_detail_displays_register_button_when_approved(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inscrire l'étudiant")
        self.assertContains(response, self.register_url)

    def test_registering_approved_pre_inscription_generates_final_matricule(self):
        response = self.client.post(self.register_url)

        self.assertRedirects(
            response,
            reverse('main:etudiant_detail', kwargs={'pk': self.expected_matricule}),
            fetch_redirect_response=False,
        )
        self.assertFalse(Student.objects.filter(matricule='INT_APPROVED_001').exists())

        registered_student = Student.objects.get(matricule=self.expected_matricule)
        self.assertEqual(registered_student.status, 'registered')
        self.assertEqual(registered_student.dossier_number, 'L0165')
        self.assertEqual(registered_student.metadata.original_country, 'Cameroun')

        student_level = StudentLevel.objects.get(level=self.level, academic_year=self.academic_year)
        self.assertEqual(student_level.student.matricule, self.expected_matricule)

    def test_registering_approved_pre_inscription_sends_registration_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.register_url)

        self.assertEqual(response.status_code, 302)
        registered_student = Student.objects.get(matricule=self.expected_matricule)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['cecilia@example.com'])
        self.assertIn('confirmation de votre inscription', mail.outbox[0].subject.lower())
        self.assertIn(registered_student.matricule, mail.outbox[0].body)
        self.assertIn(registered_student.dossier_number, mail.outbox[0].body)
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertIn(registered_student.matricule, mail.outbox[0].alternatives[0][0])

    def test_registering_approved_pre_inscription_creates_registration_certificate(self):
        response = self.client.post(self.register_url)

        self.assertEqual(response.status_code, 302)

        registered_student = Student.objects.get(matricule=self.expected_matricule)
        student_level = StudentLevel.objects.get(
            student=registered_student,
            level=self.level,
            academic_year=self.academic_year,
        )
        document = OfficialDocument.objects.get(
            student_level=student_level,
            type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
        )

        self.assertEqual(document.reference, 'CI-2025-251301659')
        self.assertEqual(document.status, 'available')

    def test_registering_approved_pre_inscription_redirects_to_payment_when_first_installment_is_not_sold(self):
        Payment.objects.all().delete()

        response = self.client.post(self.register_url)

        self.assertEqual(response.status_code, 302)
        parsed_url = urlparse(response.url)
        self.assertEqual(parsed_url.path, reverse('main:payments:payment_create'))

        query = parse_qs(parsed_url.query)
        self.assertEqual(query['student'], [self.student.pk])
        self.assertEqual(query['academic_year'], [str(self.academic_year.pk)])
        self.assertEqual(query['category'], ['frais_scolarite'])
        self.assertEqual(query['installment'], [str(self.first_installment.pk)])
        self.assertEqual(query['registration_flow'], ['1'])
        self.assertEqual(query['registration_student_id'], [self.student.pk])

    def test_registration_flow_completes_after_first_installment_payment(self):
        Payment.objects.all().delete()

        first_response = self.client.post(self.register_url)
        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(urlparse(first_response.url).path, reverse('main:payments:payment_create'))

        payment_response = self.client.post(reverse('main:payments:payment_create'), {
            'student_search': f'{self.student.matricule} - {self.student.firstname} {self.student.lastname} - {self.program.name}',
            'student': self.student.pk,
            'installment': self.first_installment.pk,
            'academic_year': self.academic_year.pk,
            'payment_date': '2025-09-12',
            'category': 'frais_scolarite',
            'amount_paid': '50000',
            'source': 'cash',
            'receipt_number': 'REC-REG-002',
            'registration_flow': '1',
            'registration_student_id': self.student.pk,
            'registration_academic_year_id': self.academic_year.pk,
            'registration_installment_id': self.first_installment.pk,
            'return_url': self.detail_url,
        })

        self.assertRedirects(
            payment_response,
            reverse('main:etudiant_detail', kwargs={'pk': self.expected_matricule}),
            fetch_redirect_response=False,
        )
        self.assertTrue(Student.objects.filter(matricule=self.expected_matricule).exists())


class AuditLogIntegrationTests(TestCase):
    def setUp(self):
        AuditLog.objects.all().delete()
        self.user = BaseUser.objects.create_user(
            username='audit_user',
            password='testpass123',
            role='scholar'
        )
        self.login_url = reverse('authentication:login')
        self.logout_url = reverse('authentication:logout')
        self.settings_url = reverse('main:parametres')

    def test_web_login_and_logout_create_audit_entries(self):
        response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': 'testpass123',
        })

        self.assertEqual(response.status_code, 302)
        login_entry = AuditLog.objects.filter(category='auth', action='login').latest('id')
        self.assertEqual(login_entry.actor_user, self.user)
        self.assertEqual(login_entry.context['channel'], 'web')

        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, 302)
        logout_entry = AuditLog.objects.filter(category='auth', action='logout').latest('id')
        self.assertEqual(logout_entry.actor_user, self.user)
        self.assertEqual(logout_entry.context['channel'], 'web')

    def test_settings_update_creates_model_audit_entry(self):
        self.client.force_login(self.user)
        settings = SystemSettings.get_settings()

        response = self.client.post(self.settings_url, {
            'form_type': 'data_management',
            'backup_frequency': settings.backup_frequency,
            'data_retention': 9,
            'audit_log': 'on',
            'data_encryption': 'on',
        })

        self.assertEqual(response.status_code, 302)
        entry = AuditLog.objects.filter(
            category='model',
            action='update',
            target_app_label='main',
            target_model='SystemSettings',
        ).latest('id')
        self.assertEqual(entry.actor_user, self.user)
        self.assertEqual(entry.changes['data_retention']['to'], 9)

    def test_academic_year_switch_creates_business_audit_entry(self):
        self.client.force_login(self.user)
        academic_year = AcademicYear.objects.create(
            start_at=date(2026, 9, 1),
            end_at=date(2027, 6, 30),
            is_active=True,
        )

        response = self.client.post(self.settings_url, {
            'form_type': 'academic_year',
            'active_academic_year': academic_year.pk,
        })

        self.assertEqual(response.status_code, 302)
        entry = AuditLog.objects.filter(category='business', action='update').latest('id')
        self.assertEqual(entry.actor_user, self.user)
        self.assertEqual(entry.changes['active_academic_year_id']['to'], academic_year.id)
        self.assertEqual(entry.context['operation'], 'switch_active_academic_year')

    def test_api_agent_login_creates_auth_audit_entry(self):
        agent = Agent.objects.create(
            matricule='AG20260001',
            nom='Agent',
            prenom='Test',
            telephone='+237600000000',
            email='agent.audit@example.com',
            type_agent='interne',
            statut='actif',
            date_embauche=date(2026, 1, 10),
            is_active=True,
        )
        agent.set_password('secret123')
        agent.save()

        api_client = APIClient()
        response = api_client.post('/api/v1/auth/login/', {
            'email': agent.email,
            'password': 'secret123',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        entry = AuditLog.objects.filter(category='auth', action='login', actor_agent_id=agent.id).latest('id')
        self.assertEqual(entry.context['channel'], 'api')
        self.assertEqual(entry.actor_identifier, agent.email)


class SystemSettingsLogoUploadTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='settings_logo_user',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)
        self.settings_url = reverse('main:parametres')

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

    def test_general_settings_form_accepts_logo_upload(self):
        settings = SystemSettings.get_settings()

        response = self.client.post(self.settings_url, {
            'form_type': 'general',
            'institution_name': settings.institution_name,
            'institution_code': settings.institution_code,
            'address': settings.address,
            'phone': settings.phone,
            'email': settings.email,
            'website': settings.website,
            'timezone': settings.timezone,
            'language': settings.language,
            'logo': SimpleUploadedFile(
                'institution-logo.png',
                self._build_test_png(color='teal'),
                content_type='image/png',
            ),
        })

        self.assertEqual(response.status_code, 302)
        settings.refresh_from_db()
        self.assertTrue(bool(settings.logo))
        self.assertIn('institution-logo', settings.logo.name)
        self.assertTrue(os.path.exists(settings.logo.path))


class PreInscriptionRegistrationAuditTests(TestCase):
    def setUp(self):
        AuditLog.objects.all().delete()
        self.user = BaseUser.objects.create_user(
            username='scholar_register_audit',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2025, 9, 1),
            end_at=date(2026, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Master 1')
        self.program = Program.objects.create(name='Audit program')
        Student.objects.create(
            matricule='EXISTING_REGISTERED_AUDIT',
            dossier_number='M0099',
            firstname='Déjà',
            lastname='Inscrit',
            gender='M',
            lang='fr',
            status='registered',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )
        self.student = Student.objects.create(
            matricule='INT_APPROVED_AUDIT',
            firstname='Nadia',
            lastname='Ngono',
            gender='F',
            lang='fr',
            status='approved',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )
        self.first_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche 1',
            order_number=1,
            amount=50000,
            due_date=date(2025, 10, 15),
        )
        Payment.objects.create(
            student=self.student,
            installment=self.first_installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=50000,
            payment_date=timezone.make_aware(datetime.combine(date(2025, 9, 10), datetime.min.time())),
            receipt_number='REC-REG-AUDIT-001',
            transaction_id='TX-REG-AUDIT-001',
            source='cash',
        )
        self.register_url = reverse('main:inscription_register', kwargs={'pk': self.student.matricule})

    def test_registration_flow_creates_business_audit_entry(self):
        response = self.client.post(self.register_url)

        self.assertEqual(response.status_code, 302)
        entry = AuditLog.objects.filter(category='business', action='bulk_update').latest('id')
        self.assertEqual(entry.actor_user, self.user)
        self.assertEqual(entry.context['operation'], 'student_registration_rebinding')
        self.assertEqual(entry.changes['status']['to'], 'registered')


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
        self.secondary_school = School.objects.create(name='Lycée de Yaoundé', level='secondary')
        self.university = School.objects.create(name='Université de Yaoundé I', level='higher')

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

    def _set_created_at(self, student, value):
        aware_datetime = timezone.make_aware(datetime.combine(value, datetime.min.time()))
        Student.objects.filter(pk=student.pk).update(created_at=aware_datetime)
        student.refresh_from_db()

    def test_inscription_detail_displays_pdf_print_link(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.print_url)
        self.assertContains(response, 'Imprimer le dossier PDF complet')

    def test_pdf_export_returns_combined_pdf_with_annexes(self):
        SecondaryDiploma.objects.create(
            student=self.student,
            name='Baccalauréat',
            serie='C',
            obtained_year=2021,
            mention='Bien',
            school=self.secondary_school,
        )
        UniversityLevel.objects.create(
            student=self.student,
            level_name='Licence 1',
            diploma_name='Baccalauréat',
            speciality='Informatique',
            academic_year='2024/2025',
            university=self.university,
        )

        response = self.client.get(self.print_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('preinscription_PDF001.pdf', response['Content-Disposition'])

        reader = PdfReader(BytesIO(response.content))
        self.assertGreaterEqual(len(reader.pages), 5)

        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        normalized_text = ' '.join(full_text.split())
        self.assertIn('Jean Dupont', normalized_text)
        self.assertIn('PDF001', normalized_text)
        self.assertIn('Acte de naissance', normalized_text)
        self.assertIn('Preuve d\'obtention du baccalauréat', normalized_text)
        self.assertIn('Cursus scolaire et universitaire', normalized_text)
        self.assertIn('Baccalauréat', normalized_text)
        self.assertIn('Université de Yaoundé I', normalized_text)

    def test_pdf_export_displays_profile_photo_on_first_page_without_annex(self):
        self.student.profile_photo = SimpleUploadedFile(
            'photo-identite.png',
            self._build_test_png(),
            content_type='image/png',
        )
        self.student.save(update_fields=['profile_photo'])

        response = self.client.get(self.print_url)

        self.assertEqual(response.status_code, 200)

        reader = PdfReader(BytesIO(response.content))
        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        first_page_resources = reader.pages[0]['/Resources'].get_object()
        x_objects = first_page_resources.get('/XObject')
        if x_objects is not None:
            x_objects = x_objects.get_object()

        self.assertNotIn('Photo de profil', full_text)
        self.assertIsNotNone(x_objects)
        self.assertGreater(len(x_objects), 0)

    def test_inscriptions_list_displays_filtered_batch_pdf_export_action(self):
        response = self.client.get(self.list_url, {'program': self.program.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.batch_print_url)
        self.assertContains(response, 'Exporter les dossiers filtrés en PDF')
        self.assertContains(response, 'filteredPdfExportModal')
        self.assertContains(response, '2 pré-inscription(s) trouvée(s)')
        self.assertContains(response, f'name="program" value="{self.program.pk}"')
        self.assertContains(response, 'Vous allez générer un seul PDF combiné')

    def test_inscriptions_list_can_filter_by_date_interval(self):
        self._set_created_at(self.student, date(2024, 1, 10))
        self._set_created_at(self.second_student, date(2024, 1, 20))
        self._set_created_at(self.excluded_student, date(2024, 2, 5))

        response = self.client.get(self.list_url, {
            'date_from': '2024-01-15',
            'date_to': '2024-01-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="date_from" value="2024-01-15"')
        self.assertContains(response, 'name="date_to" value="2024-01-31"')
        self.assertContains(response, '1 pré-inscription(s) trouvée(s)')
        self.assertContains(response, 'Alice Ngono')
        self.assertNotContains(response, 'Jean Dupont')
        self.assertNotContains(response, 'Marc Essono')
        self.assertContains(response, 'Du : 2024-01-15')
        self.assertContains(response, 'Au : 2024-01-31')

    def test_batch_pdf_export_can_filter_by_date_interval(self):
        self._set_created_at(self.student, date(2024, 1, 10))
        self._set_created_at(self.second_student, date(2024, 1, 20))
        self._set_created_at(self.excluded_student, date(2024, 2, 5))

        response = self.client.get(self.batch_print_url, {
            'date_from': '2024-01-15',
            'date_to': '2024-01-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        reader = PdfReader(BytesIO(response.content))
        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        self.assertIn('Alice Ngono', full_text)
        self.assertIn('PDF002', full_text)
        self.assertNotIn('Jean Dupont', full_text)
        self.assertNotIn('PDF001', full_text)
        self.assertNotIn('Marc Essono', full_text)
        self.assertNotIn('PDF003', full_text)

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
            'bac_etablissement_existant': self.school.pk,
            'bac_etablissement': '',
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
            'secondary_diplomas-TOTAL_FORMS': '0',
            'secondary_diplomas-INITIAL_FORMS': '0',
            'secondary_diplomas-MIN_NUM_FORMS': '0',
            'secondary_diplomas-MAX_NUM_FORMS': '1000',
            'university_levels-TOTAL_FORMS': '0',
            'university_levels-INITIAL_FORMS': '0',
            'university_levels-MIN_NUM_FORMS': '0',
            'university_levels-MAX_NUM_FORMS': '1000',
            'acte_naissance': SimpleUploadedFile('acte-naissance.pdf', b'%PDF-1.4 acte', content_type='application/pdf'),
            'preuve_baccalaureat': SimpleUploadedFile('preuve-bac.pdf', b'%PDF-1.4 bac', content_type='application/pdf'),
            'certificat_nationalite': SimpleUploadedFile('certificat-nationalite.pdf', b'%PDF-1.4 cni', content_type='application/pdf'),
            'releve_notes_last_class': SimpleUploadedFile('releve-dernier-cycle.pdf', b'%PDF-1.4 releve', content_type='application/pdf'),
            'justificatif_dernier_diplome': SimpleUploadedFile('justificatif-diplome.pdf', b'%PDF-1.4 diplome', content_type='application/pdf'),
            'bulletins_terminale': SimpleUploadedFile('bulletins-terminale.pdf', b'%PDF-1.4 bulletins', content_type='application/pdf'),
        }
        payload.update(overrides)
        return payload

    def test_etudiant_detail_displays_profile_photo(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo de profil')
        self.assertContains(response, self.student.profile_photo.url)

    def test_etudiant_detail_displays_secondary_and_university_curriculum(self):
        SecondaryDiploma.objects.create(
            student=self.student,
            name='Baccalauréat',
            serie='C',
            obtained_year=2021,
            mention='Bien',
            school=self.school,
        )
        university = School.objects.create(name='Université de Test', level='higher')
        UniversityLevel.objects.create(
            student=self.student,
            level_name='Licence 2',
            diploma_name='DEUG',
            speciality='Informatique',
            academic_year='2022/2023',
            university=university,
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cursus académique')
        self.assertContains(response, 'Baccalauréat')
        self.assertContains(response, 'Collège Photo')
        self.assertContains(response, 'Cursus universitaire')
        self.assertContains(response, 'Licence 2')
        self.assertContains(response, 'Université de Test')

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

    def test_etudiant_edit_displays_existing_curriculum_formsets(self):
        SecondaryDiploma.objects.create(
            student=self.student,
            name='Baccalauréat',
            serie='C',
            obtained_year=2021,
            mention='Bien',
            school=self.school,
        )
        university = School.objects.create(name='Université de Test', level='higher')
        UniversityLevel.objects.create(
            student=self.student,
            level_name='Niveau 3',
            diploma_name='Licence',
            speciality='Informatique',
            academic_year='2022/2023',
            university=university,
        )

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cursus scolaire et universitaire')
        self.assertContains(response, 'secondary_diplomas-0-name')
        self.assertContains(response, 'university_levels-0-level_name')
        self.assertEqual(response.context['secondary_diploma_formset'].total_form_count(), 1)
        self.assertEqual(response.context['university_level_formset'].total_form_count(), 1)

    def test_etudiant_edit_marks_documents_as_optional(self):
        set_program_required_documents(self.program, ['acte_naissance', 'decharge_equivalence'])

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['documents_mode'], 'admin_only_optional')
        self.assertTrue(all(not entry['is_required'] for entry in response.context['document_entries']))

    def test_etudiant_edit_allows_missing_documents_for_selected_program(self):
        set_program_required_documents(self.program, ['decharge_equivalence'])

        response = self.client.post(self.edit_url, self._edit_payload())

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

    def test_etudiant_edit_can_add_update_and_delete_curriculum(self):
        existing_diploma = SecondaryDiploma.objects.create(
            student=self.student,
            name='Probatoire',
            serie='D',
            obtained_year=2020,
            mention='Passable',
            school=self.school,
        )
        existing_university = School.objects.create(name='Université Ancienne', level='higher')
        existing_university_level = UniversityLevel.objects.create(
            student=self.student,
            level_name='Niveau 2',
            diploma_name='BTS',
            speciality='Gestion',
            academic_year='2021/2022',
            university=existing_university,
        )
        new_secondary_school = School.objects.create(name='Lycée Moderne', level='secondary')

        payload = self._edit_payload(
            **{
                'secondary_diplomas-TOTAL_FORMS': '2',
                'secondary_diplomas-INITIAL_FORMS': '1',
                'secondary_diplomas-MIN_NUM_FORMS': '0',
                'secondary_diplomas-MAX_NUM_FORMS': '1000',
                'secondary_diplomas-0-name': 'Baccalauréat',
                'secondary_diplomas-0-serie': 'C',
                'secondary_diplomas-0-obtained_year': '2021',
                'secondary_diplomas-0-mention': 'Bien',
                'secondary_diplomas-0-school_existant': self.school.pk,
                'secondary_diplomas-0-school_name': '',
                'secondary_diplomas-0-DELETE': '',
                'secondary_diplomas-1-name': 'BEPC',
                'secondary_diplomas-1-serie': '',
                'secondary_diplomas-1-obtained_year': '2019',
                'secondary_diplomas-1-mention': 'Assez bien',
                'secondary_diplomas-1-school_existant': new_secondary_school.pk,
                'secondary_diplomas-1-school_name': '',
                'secondary_diplomas-1-DELETE': '',
                'university_levels-TOTAL_FORMS': '1',
                'university_levels-INITIAL_FORMS': '1',
                'university_levels-MIN_NUM_FORMS': '0',
                'university_levels-MAX_NUM_FORMS': '1000',
                'university_levels-0-level_name': existing_university_level.level_name,
                'university_levels-0-diploma_name': existing_university_level.diploma_name,
                'university_levels-0-speciality': existing_university_level.speciality,
                'university_levels-0-academic_year': existing_university_level.academic_year,
                'university_levels-0-university_existant': existing_university.pk,
                'university_levels-0-university_name': '',
                'university_levels-0-DELETE': 'on',
            }
        )

        response = self.client.post(self.edit_url, payload)

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()
        diplomas = list(self.student.secondary_diplomas.order_by('obtained_year', 'name'))

        self.assertFalse(SecondaryDiploma.objects.filter(pk=existing_diploma.pk).exists())
        self.assertEqual(len(diplomas), 2)
        self.assertEqual(diplomas[0].name, 'BEPC')
        self.assertEqual(diplomas[1].name, 'Baccalauréat')
        self.assertEqual(diplomas[1].mention, 'Bien')
        self.assertEqual(self.student.school, self.school)
        self.assertFalse(UniversityLevel.objects.filter(pk=existing_university_level.pk).exists())
        self.assertEqual(self.student.university_levels.count(), 0)

    def test_etudiant_edit_can_remove_profile_photo(self):
        response = self.client.post(self.edit_url, self._edit_payload(remove_profile_photo='on'))

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )

        self.student.refresh_from_db()

        self.assertFalse(bool(self.student.profile_photo))


class RegistrationCertificateDownloadTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='scholar_certificate',
            password='testpass123',
            role='scholar'
        )
        self.client.force_login(self.user)

        self.academic_year = AcademicYear.objects.create(
            start_at=date(2025, 9, 1),
            end_at=date(2026, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 1')
        self.program = Program.objects.create(name='Informatique')
        self.student = Student.objects.create(
            matricule='CERT001',
            dossier_number='L0999',
            firstname='Claire',
            lastname='Essomba',
            gender='F',
            lang='fr',
            email='claire@example.com',
            status='registered',
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
            program=self.program,
        )
        self.student_level = StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )
        self.document = OfficialDocument.objects.create(
            student_level=self.student_level,
            type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
            reference='CI-2025-CERT001',
        )

        settings = SystemSettings.get_settings()
        settings.institution_name = 'Institut de Test YSEM'
        settings.institution_code = 'YSEM-TEST'
        settings.address = 'Damas, Yaoundé'
        settings.phone = '+237600000000'
        settings.email = 'contact@test-ysem.local'
        settings.website = 'https://test-ysem.local'
        settings.logo = SimpleUploadedFile(
            'certificate-logo.png',
            self._build_test_png(color='teal'),
            content_type='image/png',
        )
        settings.save()

        self.detail_url = reverse('main:etudiant_detail', kwargs={'pk': self.student.matricule})
        self.download_url = reverse('main:registration_certificate_download', kwargs={'pk': self.document.pk})

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

    def test_etudiant_detail_displays_registration_certificate_reference_and_download_link(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CERTIFICAT D’INSCRIPTION')
        self.assertContains(response, 'CI-2025-CERT001')
        self.assertContains(response, self.download_url)
        self.assertContains(response, 'Télécharger')

    def test_download_generates_registration_certificate_pdf_on_demand(self):
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('certificat_inscription_CI-2025-CERT001.pdf', response['Content-Disposition'])

        reader = PdfReader(BytesIO(response.content))
        full_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        normalized_text = ' '.join(full_text.split())

        self.assertIn('Institut de Test YSEM', normalized_text)
        self.assertIn('YSEM-TEST', normalized_text)
        self.assertIn('Claire Essomba', normalized_text)
        self.assertIn('CERT001', normalized_text)
        self.assertIn('CI-2025-CERT001', normalized_text)
        self.assertIn('Licence 1', normalized_text)
        self.assertIn('2025/2026', normalized_text)
        self.assertIn('Damas, Yaoundé', normalized_text)
        self.assertIn('contact@test-ysem.local', normalized_text)


class DocumentWithdrawalRulesTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_document_rules',
            password='testpass123',
            role='scholar',
        )
        self.client.force_login(self.user)

        today = timezone.localdate()
        self.academic_year = AcademicYear.objects.create(
            start_at=date(today.year, 9, 1),
            end_at=date(today.year + 1, 6, 30),
            is_active=True,
        )
        self.level = Level.objects.create(name='Licence 2', academic_order=2)
        self.program = Program.objects.create(name='Finance')
        self.student = Student.objects.create(
            matricule='DOC-RULE-001',
            firstname='Mireille',
            lastname='Abena',
            gender='F',
            status='registered',
            program=self.program,
            metadata=StudentMetaData.objects.create(original_country='Cameroun'),
        )
        self.student_level = StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
            is_registered=True,
        )
        self.document = OfficialDocument.objects.create(
            student_level=self.student_level,
            type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
            reference='CI-DOC-RULE-001',
        )
        self.installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche échue',
            order_number=1,
            amount=50000,
            due_date=today - timezone.timedelta(days=15),
        )
        self.toggle_url = reverse('main:document_toggle_status', kwargs={'pk': self.document.pk})

    def test_document_toggle_status_blocks_withdraw_when_due_installments_are_unpaid(self):
        response = self.client.post(self.toggle_url)

        self.assertRedirects(response, reverse('main:documents'), fetch_redirect_response=False)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'available')
        self.assertIsNone(self.document.withdrawn_date)

    def test_document_toggle_status_allows_withdraw_when_due_installments_are_paid(self):
        Payment.objects.create(
            student=self.student,
            installment=self.installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=50000,
            payment_date=timezone.make_aware(datetime.combine(timezone.localdate(), datetime.min.time())),
            receipt_number='REC-DOC-RULE-001',
            source='cash',
        )

        response = self.client.post(self.toggle_url)

        self.assertRedirects(response, reverse('main:documents'), fetch_redirect_response=False)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'withdrawn')
        self.assertEqual(self.document.withdrawn_date, timezone.localdate())


class PreInscriptionProfilePhotoTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = BaseUser.objects.create_user(
            username='scholar_preinscription_photo',
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
        self.metadata = StudentMetaData.objects.create(original_country='Cameroun')

        self.student = Student.objects.create(
            matricule='PREPHOTO001',
            firstname='Julie',
            lastname='Nkoa',
            gender='F',
            lang='fr',
            email='julie@example.com',
            status='pending',
            metadata=self.metadata,
            program=self.program,
            profile_photo=SimpleUploadedFile(
                'photo-preinscription-detail.png',
                self._build_test_png(color='pink'),
                content_type='image/png',
            ),
        )
        StudentLevel.objects.create(
            student=self.student,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
        )

        self.detail_url = reverse('main:inscription_detail', kwargs={'pk': self.student.matricule})
        self.list_url = reverse('main:inscriptions')

    def _build_test_png(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color=color).save(buffer, format='PNG')
        return buffer.getvalue()

    def test_preinscription_detail_displays_profile_photo(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo de profil')
        self.assertContains(response, self.student.profile_photo.url)

    def test_preinscription_detail_displays_secondary_and_university_curriculum(self):
        secondary_school = School.objects.create(name='Lycée de Test', level='secondary')
        university = School.objects.create(name='Université de Douala', level='higher')
        SecondaryDiploma.objects.create(
            student=self.student,
            name='Probatoire',
            serie='D',
            obtained_year=2022,
            mention='Assez bien',
            school=secondary_school,
        )
        UniversityLevel.objects.create(
            student=self.student,
            level_name='Licence 1',
            diploma_name='Baccalauréat',
            speciality='Mathématiques',
            academic_year='2023/2024',
            university=university,
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cursus académique')
        self.assertContains(response, 'Probatoire')
        self.assertContains(response, 'Lycée de Test')
        self.assertContains(response, 'Cursus universitaire')
        self.assertContains(response, 'Licence 1')
        self.assertContains(response, 'Université de Douala')

    def test_preinscriptions_list_displays_profile_thumbnail(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo')
        self.assertContains(response, self.student.profile_photo.url)

    def test_preinscription_delete_soft_delete(self):
        """Test que la suppression d'une pré-inscription marque deleted_at"""
        # Créer un étudiant avec statut rejected
        student = Student.objects.create(
            matricule='TEST-DELETE-001',
            firstname='Test',
            lastname='Delete',
            gender='M',
            status='rejected'
        )

        # Vérifier que deleted_at est null
        self.assertIsNone(student.deleted_at)

        # Supprimer l'étudiant
        delete_url = reverse('main:inscription_delete', kwargs={'pk': student.matricule})
        response = self.client.post(delete_url)

        # Vérifier la redirection
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('main:inscriptions'))

        # Vérifier que deleted_at est maintenant défini
        student.refresh_from_db()
        self.assertIsNotNone(student.deleted_at)

    def test_preinscription_deleted_not_in_list(self):
        """Test que les étudiants supprimés n'apparaissent pas dans la liste"""
        # Créer deux étudiants
        student1 = Student.objects.create(
            matricule='TEST-LIST-001',
            firstname='Test1',
            lastname='List1',
            gender='M',
            status='rejected'
        )
        student2 = Student.objects.create(
            matricule='TEST-LIST-002',
            firstname='Test2',
            lastname='List2',
            gender='M',
            status='rejected'
        )

        # Supprimer le premier étudiant
        from django.utils import timezone
        student1.deleted_at = timezone.now()
        student1.save()

        # Vérifier que seul student2 apparaît dans la liste
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, student2.firstname)
        self.assertNotContains(response, student1.firstname)


class PaymentStatusViewTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_payment_status',
            password='testpass123',
            role='scholar',
        )
        self.client.force_login(self.user)

        today = timezone.localdate()
        self.academic_year = AcademicYear.objects.create(
            start_at=date(today.year, 9, 1),
            end_at=date(today.year + 1, 6, 30),
            is_active=True,
        )
        self.program = Program.objects.create(name='Informatique')
        self.level = Level.objects.create(name='Licence 1', academic_order=1)

        self.student_up_to_date = Student.objects.create(
            matricule='PAY-STATUS-001',
            firstname='Jean',
            lastname='Dupont',
            gender='M',
            status='registered',
            program=self.program,
        )
        self.student_overdue = Student.objects.create(
            matricule='PAY-STATUS-002',
            firstname='Alice',
            lastname='Ngono',
            gender='F',
            status='registered',
            program=self.program,
        )

        StudentLevel.objects.create(
            student=self.student_up_to_date,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
            is_registered=True,
        )
        StudentLevel.objects.create(
            student=self.student_overdue,
            level=self.level,
            academic_year=self.academic_year,
            is_active=True,
            is_registered=True,
        )

        self.first_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche 1',
            order_number=1,
            amount=50000,
            due_date=today - timezone.timedelta(days=30),
        )
        self.second_installment = PaymentInstallment.objects.create(
            program=self.program,
            academic_year=self.academic_year,
            level=self.level,
            name='Tranche 2',
            order_number=2,
            amount=70000,
            due_date=today + timezone.timedelta(days=30),
        )

        Payment.objects.create(
            student=self.student_up_to_date,
            installment=self.first_installment,
            academic_year=self.academic_year,
            category='frais_scolarite',
            author=self.user,
            amount_paid=50000,
            payment_date=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            receipt_number='REC-STATUS-001',
            source='cash',
        )

        self.url = reverse('main:payment_status')

    def test_payment_status_view_uses_dynamic_payment_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_academic_year'], self.academic_year)
        self.assertEqual(response.context['filtered_students_count'], 2)
        self.assertContains(response, 'Suivi des frais de scolarité')
        self.assertContains(response, 'Jean Dupont')
        self.assertContains(response, 'Alice Ngono')
        self.assertContains(response, 'Ajouter un paiement')

        rows = {row['student'].pk: row for row in response.context['page_obj'].object_list}
        self.assertEqual(rows[self.student_up_to_date.pk]['total_amount_due'], Decimal('120000.00'))
        self.assertEqual(rows[self.student_up_to_date.pk]['amount_paid'], Decimal('50000.00'))
        self.assertEqual(rows[self.student_up_to_date.pk]['remaining_amount'], Decimal('70000.00'))
        self.assertEqual(rows[self.student_up_to_date.pk]['status'], 'up_to_date')
        self.assertEqual(rows[self.student_overdue.pk]['status'], 'overdue')

    def test_payment_status_view_can_filter_on_computed_status(self):
        response = self.client.get(self.url, {'status': 'overdue'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filtered_students_count'], 1)
        self.assertContains(response, 'Alice Ngono')
        self.assertNotContains(response, 'Jean Dupont')


class StatistiquesViewTests(TestCase):
    def setUp(self):
        self.user = BaseUser.objects.create_user(
            username='scholar_stats',
            password='testpass123',
            role='scholar',
        )
        self.client.force_login(self.user)

        self.old_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=False,
        )
        self.active_year = AcademicYear.objects.create(
            start_at=date(2025, 9, 1),
            end_at=date(2026, 6, 30),
            is_active=True,
        )
        self.level_1 = Level.objects.create(name='Licence 1', academic_order=1)
        self.level_2 = Level.objects.create(name='Licence 2', academic_order=2)
        self.program_1 = Program.objects.create(name='Informatique')
        self.program_2 = Program.objects.create(name='Gestion')
        self.speciality_1 = Speciality.objects.create(name='Data', program=self.program_1)
        self.speciality_2 = Speciality.objects.create(name='Finance', program=self.program_2)
        self.school_1 = School.objects.create(
            name='Lycée de Yaoundé',
            phone_number='+237600000001',
            level='secondary',
        )
        self.school_2 = School.objects.create(
            name='Université de Douala',
            phone_number='+237600000002',
            level='higher',
        )

        self.student_active = Student.objects.create(
            matricule='STAT-001',
            firstname='Alice',
            lastname='Nanga',
            gender='F',
            lang='fr',
            status='registered',
            program=self.program_1,
            school=self.school_1,
            start_level=self.level_1,
        )
        self.student_old = Student.objects.create(
            matricule='STAT-002',
            firstname='Brice',
            lastname='Essomba',
            gender='M',
            lang='en',
            status='registered',
            program=self.program_2,
            school=self.school_2,
            start_level=self.level_2,
        )

        self.student_level_active = StudentLevel.objects.create(
            student=self.student_active,
            level=self.level_1,
            academic_year=self.active_year,
            speciality=self.speciality_1,
            is_active=True,
            is_registered=True,
        )
        self.student_level_old = StudentLevel.objects.create(
            student=self.student_old,
            level=self.level_2,
            academic_year=self.old_year,
            speciality=self.speciality_2,
            is_active=True,
            is_registered=True,
        )

        OfficialDocument.objects.create(
            student_level=self.student_level_active,
            type=OfficialDocument.TYPE_TRANSCRIPT,
            status='available',
        )
        OfficialDocument.objects.create(
            student_level=self.student_level_active,
            type=OfficialDocument.TYPE_CERTIFICATE,
            status='withdrawn',
        )
        OfficialDocument.objects.create(
            student_level=self.student_level_old,
            type=OfficialDocument.TYPE_DIPLOMA,
            status='lost',
        )

        self.url = reverse('main:statistiques')

    def test_statistics_view_defaults_to_active_year_and_renders_all_filters(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_year'], self.active_year)
        self.assertEqual(response.context['selected_year'], str(self.active_year.id))
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_documents'], 2)
        self.assertContains(response, 'Filtres avancés')
        self.assertContains(response, 'École d’origine')
        self.assertContains(response, 'Statut document')
        self.assertContains(response, 'Type de document')
        self.assertContains(response, 'Toutes les années')

    def test_statistics_view_can_aggregate_all_years(self):
        response = self.client.get(self.url, {'year': 'all'})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['current_year'])
        self.assertEqual(response.context['selected_year'], 'all')
        self.assertEqual(response.context['current_period_label'], 'Toutes les années')
        self.assertEqual(response.context['total_students'], 2)
        self.assertEqual(response.context['total_documents'], 3)
        self.assertCountEqual(
            [stat['label'] for stat in response.context['level_stats']],
            [self.level_1.name, self.level_2.name],
        )

    def test_statistics_view_applies_combined_student_and_document_filters(self):
        response = self.client.get(self.url, {
            'year': 'all',
            'program': str(self.program_1.id),
            'gender': 'F',
            'document_status': 'withdrawn',
            'document_type': OfficialDocument.TYPE_CERTIFICATE,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['filters_expanded'])
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_documents'], 1)
        self.assertEqual(response.context['withdrawn_documents'], 1)
        self.assertEqual(response.context['available_documents'], 0)
        self.assertEqual(response.context['program_stats'][0]['label'], self.program_1.name)
        self.assertEqual(response.context['document_type_stats'][0]['label'], 'Certificat de scolarité')

        applied_filters = {item['label']: item['value'] for item in response.context['applied_filters']}
        self.assertEqual(applied_filters['Année académique'], 'Toutes les années')
        self.assertEqual(applied_filters['Programme'], self.program_1.name)
        self.assertEqual(applied_filters['Genre'], 'Féminin')
        self.assertEqual(applied_filters['Statut document'], 'Déchargé')
