from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from students.models import Student, StudentMetaData


class StudentDashboardProfilePhotoTests(TestCase):
    def setUp(self):
        self.temporary_media = TemporaryDirectory()
        self.addCleanup(self.temporary_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temporary_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        metadata = StudentMetaData.objects.create(original_country='Cameroun')
        self.student = Student.objects.create(
            matricule='PORTAL001',
            firstname='Julie',
            lastname='Nguemo',
            gender='F',
            lang='fr',
            email='julie@example.com',
            status='pending',
            metadata=metadata,
            profile_photo=SimpleUploadedFile(
                'photo-portail.png',
                self._build_test_png(),
                content_type='image/png',
            ),
        )

        session = self.client.session
        session['student_authenticated'] = True
        session['student_matricule'] = self.student.matricule
        session['student_name'] = f'{self.student.firstname} {self.student.lastname}'
        session.save()

    def _build_test_png(self):
        buffer = BytesIO()
        Image.new('RGB', (120, 120), color='purple').save(buffer, format='PNG')
        return buffer.getvalue()

    def test_dashboard_displays_profile_photo(self):
        response = self.client.get(reverse('student_portal:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo de profil')
        self.assertContains(response, self.student.profile_photo.url)
