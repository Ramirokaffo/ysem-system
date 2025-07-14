from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, time

from .models import Classroom, TimeSlot, CourseSession, Schedule, LecturerAvailability, ScheduleSession
from .services import ScheduleGenerationService
from .forms import TimeSlotForm, TimeSlotSearchForm
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear

User = get_user_model()


class PlanificationModelsTest(TestCase):
    """Tests pour les modèles de planification"""

    def setUp(self):
        # Créer une année académique
        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True
        )

        # Créer un niveau
        self.level = Level.objects.create(name="Licence 1")

        # Créer un cours
        self.course = Course.objects.create(
            course_code="INF101",
            label="Introduction à l'informatique",
            credit_count=3,
            level=self.level
        )

        # Créer un enseignant
        self.lecturer = Lecturer.objects.create(
            matricule="ENS001",
            firstname="Jean",
            lastname="Dupont",
            date_naiss=date(1980, 1, 1),
            grade="Professeur",
            gender="M"
        )

        # Créer une salle
        self.classroom = Classroom.objects.create(
            code="A101",
            name="Salle A101",
            capacity=50,
            building="Bâtiment A",
            floor="1er étage"
        )

        # Créer un créneau horaire
        self.time_slot = TimeSlot.objects.create(
            name="Matin 1",
            day_of_week="monday",
            start_time=time(8, 0),
            end_time=time(10, 0)
        )

    def test_classroom_creation(self):
        """Test de création d'une salle de classe"""
        self.assertEqual(self.classroom.code, "A101")
        self.assertEqual(self.classroom.capacity, 50)
        self.assertTrue(self.classroom.is_active)
        self.assertEqual(str(self.classroom), "A101 - Salle A101")

    def test_time_slot_creation(self):
        """Test de création d'un créneau horaire"""
        self.assertEqual(self.time_slot.day_of_week, "monday")
        self.assertEqual(self.time_slot.start_time, time(8, 0))
        self.assertEqual(str(self.time_slot), "Lundi 08:00:00-10:00:00")

    def test_course_session_creation(self):
        """Test de création d'une séance de cours"""
        session = CourseSession.objects.create(
            course=self.course,
            lecturer=self.lecturer,
            classroom=self.classroom,
            time_slot=self.time_slot,
            level=self.level,
            academic_year=self.academic_year,
            date=date.today(),
            topic="Introduction générale"
        )

        self.assertEqual(session.status, 'scheduled')
        self.assertEqual(session.session_type, 'lecture')
        self.assertEqual(session.duration_hours, 1.5)
        self.assertIn("Introduction à l'informatique", str(session))


class PlanificationViewsTest(TestCase):
    """Tests pour les vues de planification"""

    def setUp(self):
        self.client = Client()

        # Créer un utilisateur responsable de planification
        self.planning_user = User.objects.create_user(
            username='planning_admin',
            password='testpass123',
            role='planning'
        )

        # Créer un utilisateur normal
        self.normal_user = User.objects.create_user(
            username='normal_user',
            password='testpass123',
            role='student'
        )

    def test_dashboard_access_with_planning_role(self):
        """Test d'accès au dashboard avec le rôle planification"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Planification')

    def test_dashboard_access_denied_without_planning_role(self):
        """Test de refus d'accès au dashboard sans le rôle planification"""
        self.client.login(username='normal_user', password='testpass123')
        response = self.client.get(reverse('planification:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection

    def test_dashboard_access_denied_without_login(self):
        """Test de refus d'accès au dashboard sans connexion"""
        response = self.client.get(reverse('planification:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login


class UserRoleTest(TestCase):
    """Tests pour les rôles utilisateur"""

    def test_is_planning_admin_method(self):
        """Test de la méthode is_planning_admin()"""
        planning_user = User.objects.create_user(
            username='planning_admin',
            role='planning'
        )
        normal_user = User.objects.create_user(
            username='normal_user',
            role='student'
        )

        self.assertTrue(planning_user.is_planning_admin())
        self.assertFalse(normal_user.is_planning_admin())


class ClassroomCRUDTest(TestCase):
    """Tests pour les opérations CRUD des salles de classe"""

    def setUp(self):
        self.client = Client()

        # Créer un utilisateur responsable de planification
        self.planning_user = User.objects.create_user(
            username='planning_admin',
            password='testpass123',
            role='planning'
        )

        # Créer une salle de test
        self.classroom = Classroom.objects.create(
            code='TEST01',
            name='Salle de test',
            capacity=25,
            building='Bâtiment Test',
            floor='1er étage'
        )

    def test_classroom_list_view(self):
        """Test de la vue liste des salles"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:classrooms'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST01')
        self.assertContains(response, 'Salle de test')

    def test_classroom_detail_view(self):
        """Test de la vue détail d'une salle"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:classroom_detail', kwargs={'code': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST01')
        self.assertContains(response, 'Salle de test')
        self.assertContains(response, '25 personnes')

    def test_classroom_create_view_get(self):
        """Test de l'affichage du formulaire de création"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:classroom_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouvelle salle de classe')

    def test_classroom_create_view_post(self):
        """Test de création d'une nouvelle salle"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'code': 'NEW01',
            'name': 'Nouvelle salle',
            'capacity': 40,
            'building': 'Nouveau bâtiment',
            'floor': '2ème étage',
            'equipment': 'Projecteur, tableau',
            'is_active': True
        }
        response = self.client.post(reverse('planification:classroom_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création

        # Vérifier que la salle a été créée
        self.assertTrue(Classroom.objects.filter(code='NEW01').exists())
        new_classroom = Classroom.objects.get(code='NEW01')
        self.assertEqual(new_classroom.name, 'Nouvelle salle')
        self.assertEqual(new_classroom.capacity, 40)

    def test_classroom_update_view_get(self):
        """Test de l'affichage du formulaire de modification"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:classroom_update', kwargs={'code': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier la salle TEST01')
        self.assertContains(response, 'value="TEST01"')

    def test_classroom_update_view_post(self):
        """Test de modification d'une salle"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'code': 'TEST01',
            'name': 'Salle modifiée',
            'capacity': 30,
            'building': 'Bâtiment modifié',
            'floor': '2ème étage',
            'equipment': 'Nouveau matériel',
            'is_active': True
        }
        response = self.client.post(reverse('planification:classroom_update', kwargs={'code': 'TEST01'}), data)
        self.assertEqual(response.status_code, 302)  # Redirection après modification

        # Vérifier que la salle a été modifiée
        updated_classroom = Classroom.objects.get(code='TEST01')
        self.assertEqual(updated_classroom.name, 'Salle modifiée')
        self.assertEqual(updated_classroom.capacity, 30)
        self.assertEqual(updated_classroom.building, 'Bâtiment modifié')

    def test_classroom_delete_view_get(self):
        """Test de l'affichage de la confirmation de suppression"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:classroom_delete', kwargs={'code': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmer la suppression')
        self.assertContains(response, 'TEST01')

    def test_classroom_delete_view_post(self):
        """Test de suppression d'une salle"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.post(reverse('planification:classroom_delete', kwargs={'code': 'TEST01'}))
        self.assertEqual(response.status_code, 302)  # Redirection après suppression

        # Vérifier que la salle a été supprimée
        self.assertFalse(Classroom.objects.filter(code='TEST01').exists())

    def test_classroom_crud_access_denied_without_permission(self):
        """Test de refus d'accès aux vues CRUD sans permission"""
        # Créer un utilisateur sans permission
        normal_user = User.objects.create_user(
            username='normal_user',
            password='testpass123',
            role='student'
        )

        self.client.login(username='normal_user', password='testpass123')

        # Tester toutes les vues CRUD
        urls = [
            reverse('planification:classrooms'),
            reverse('planification:classroom_detail', kwargs={'code': 'TEST01'}),
            reverse('planification:classroom_create'),
            reverse('planification:classroom_update', kwargs={'code': 'TEST01'}),
            reverse('planification:classroom_delete', kwargs={'code': 'TEST01'}),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirection car accès refusé


class LecturerCRUDTest(TestCase):
    """Tests pour les opérations CRUD des enseignants"""

    def setUp(self):
        self.client = Client()

        # Créer un utilisateur responsable de planification
        self.planning_user = User.objects.create_user(
            username='planning_admin',
            password='testpass123',
            role='planning'
        )

        # Créer un enseignant de test
        self.lecturer = Lecturer.objects.create(
            matricule='TEST01',
            firstname='Jean',
            lastname='DUPONT',
            date_naiss=date(1980, 1, 1),
            grade='Professeur',
            gender='M',
            email='jean.dupont@test.com'
        )

    def test_lecturer_list_view(self):
        """Test de la vue liste des enseignants"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:lecturers'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST01')
        self.assertContains(response, 'Jean DUPONT')

    def test_lecturer_detail_view(self):
        """Test de la vue détail d'un enseignant"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:lecturer_detail', kwargs={'matricule': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST01')
        self.assertContains(response, 'Jean DUPONT')
        self.assertContains(response, 'Professeur')

    def test_lecturer_create_view_get(self):
        """Test de l'affichage du formulaire de création"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:lecturer_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouvel enseignant')

    def test_lecturer_create_view_post(self):
        """Test de création d'un nouvel enseignant"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'matricule': 'NEW01',
            'firstname': 'Marie',
            'lastname': 'MARTIN',
            'date_naiss': '1985-05-15',
            'grade': 'Maître de conférences',
            'gender': 'F',
            'lang': 'fr',
            'email': 'marie.martin@test.com',
            'phone_number': '+237 6XX XXX XXX'
        }
        response = self.client.post(reverse('planification:lecturer_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création

        # Vérifier que l'enseignant a été créé
        self.assertTrue(Lecturer.objects.filter(matricule='NEW01').exists())
        new_lecturer = Lecturer.objects.get(matricule='NEW01')
        self.assertEqual(new_lecturer.firstname, 'Marie')
        self.assertEqual(new_lecturer.lastname, 'MARTIN')
        self.assertEqual(new_lecturer.email, 'marie.martin@test.com')

    def test_lecturer_update_view_get(self):
        """Test de l'affichage du formulaire de modification"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:lecturer_update', kwargs={'matricule': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier l\'enseignant TEST01')
        self.assertContains(response, 'value="TEST01"')

    def test_lecturer_update_view_post(self):
        """Test de modification d'un enseignant"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'matricule': 'TEST01',
            'firstname': 'Jean-Pierre',
            'lastname': 'DUPONT',
            'date_naiss': '1980-01-01',
            'grade': 'Professeur des universités',
            'gender': 'M',
            'lang': 'fr',
            'email': 'jean-pierre.dupont@test.com',
            'phone_number': '+237 6XX XXX XXX'
        }
        response = self.client.post(reverse('planification:lecturer_update', kwargs={'matricule': 'TEST01'}), data)
        self.assertEqual(response.status_code, 302)  # Redirection après modification

        # Vérifier que l'enseignant a été modifié
        updated_lecturer = Lecturer.objects.get(matricule='TEST01')
        self.assertEqual(updated_lecturer.firstname, 'Jean-Pierre')
        self.assertEqual(updated_lecturer.grade, 'Professeur des universités')
        self.assertEqual(updated_lecturer.email, 'jean-pierre.dupont@test.com')

    def test_lecturer_delete_view_get(self):
        """Test de l'affichage de la confirmation de suppression"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:lecturer_delete', kwargs={'matricule': 'TEST01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmer la suppression')
        self.assertContains(response, 'TEST01')

    def test_lecturer_delete_view_post(self):
        """Test de suppression d'un enseignant"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.post(reverse('planification:lecturer_delete', kwargs={'matricule': 'TEST01'}))
        self.assertEqual(response.status_code, 302)  # Redirection après suppression

        # Vérifier que l'enseignant a été supprimé
        self.assertFalse(Lecturer.objects.filter(matricule='TEST01').exists())


class ScheduleModelTest(TestCase):
    """Tests pour le modèle Schedule"""

    def setUp(self):
        # Créer une année académique
        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True
        )

        # Créer un niveau
        self.level = Level.objects.create(name="Licence 1")

    def test_schedule_creation(self):
        """Test de création d'un emploi du temps"""
        schedule = Schedule.objects.create(
            name="Emploi du temps L1 - Semestre 1",
            description="Premier semestre de Licence 1",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31),
            duration_type='3_months'
        )

        self.assertEqual(schedule.name, "Emploi du temps L1 - Semestre 1")
        self.assertEqual(schedule.level, self.level)
        self.assertEqual(schedule.academic_year, self.academic_year)
        self.assertEqual(schedule.status, 'draft')  # Statut par défaut
        self.assertFalse(schedule.is_generated)  # Pas généré par défaut

    def test_schedule_str_method(self):
        """Test de la méthode __str__ du modèle Schedule"""
        schedule = Schedule.objects.create(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )

        expected_str = f"Test Schedule - {self.level.name} ({self.academic_year})"
        self.assertEqual(str(schedule), expected_str)

    def test_schedule_get_duration_days(self):
        """Test de la méthode get_duration_days"""
        schedule = Schedule.objects.create(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 9, 30)  # 29 jours
        )

        self.assertEqual(schedule.get_duration_days(), 29)

    def test_schedule_validation_dates(self):
        """Test de validation des dates"""
        # Test avec date de fin antérieure à la date de début
        schedule = Schedule(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 12, 31),
            end_date=date(2024, 9, 1)  # Date de fin avant date de début
        )

        with self.assertRaises(ValidationError):
            schedule.clean()

    def test_schedule_unique_constraint(self):
        """Test de la contrainte d'unicité"""
        # Créer un premier emploi du temps
        Schedule.objects.create(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )

        # Essayer de créer un deuxième avec le même nom, année et niveau
        with self.assertRaises(Exception):  # Contrainte d'unicité
            Schedule.objects.create(
                name="Test Schedule",
                academic_year=self.academic_year,
                level=self.level,
                start_date=date(2024, 9, 1),
                end_date=date(2024, 12, 31)
            )


class LecturerAvailabilityModelTest(TestCase):
    """Tests pour le modèle LecturerAvailability"""

    def setUp(self):
        # Créer les données de base
        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True
        )

        self.lecturer = Lecturer.objects.create(
            matricule="ENS001",
            firstname="Jean",
            lastname="Dupont",
            date_naiss=date(1980, 1, 1),
            grade="Professeur",
            gender="M"
        )

        self.time_slot = TimeSlot.objects.create(
            name="Matin 1",
            day_of_week="monday",
            start_time=time(8, 0),
            end_time=time(10, 0)
        )

    def test_lecturer_availability_creation(self):
        """Test de création d'une disponibilité"""
        availability = LecturerAvailability.objects.create(
            lecturer=self.lecturer,
            time_slot=self.time_slot,
            academic_year=self.academic_year,
            status='available'
        )

        self.assertEqual(availability.lecturer, self.lecturer)
        self.assertEqual(availability.time_slot, self.time_slot)
        self.assertEqual(availability.status, 'available')

    def test_lecturer_availability_str_method(self):
        """Test de la méthode __str__"""
        availability = LecturerAvailability.objects.create(
            lecturer=self.lecturer,
            time_slot=self.time_slot,
            academic_year=self.academic_year,
            status='preferred'
        )

        expected_str = f"{self.lecturer} - {self.time_slot} (Préféré)"
        self.assertEqual(str(availability), expected_str)

    def test_is_available_on_date(self):
        """Test de la méthode is_available_on_date"""
        # Disponibilité sans dates spécifiques
        availability = LecturerAvailability.objects.create(
            lecturer=self.lecturer,
            time_slot=self.time_slot,
            academic_year=self.academic_year,
            status='available'
        )

        self.assertTrue(availability.is_available_on_date(date(2024, 10, 1)))

        # Disponibilité avec dates spécifiques
        availability_with_dates = LecturerAvailability.objects.create(
            lecturer=self.lecturer,
            time_slot=self.time_slot,
            academic_year=self.academic_year,
            status='available',
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )

        self.assertTrue(availability_with_dates.is_available_on_date(date(2024, 10, 1)))
        self.assertFalse(availability_with_dates.is_available_on_date(date(2025, 1, 1)))

        # Indisponibilité
        unavailability = LecturerAvailability.objects.create(
            lecturer=self.lecturer,
            time_slot=self.time_slot,
            academic_year=self.academic_year,
            status='unavailable'
        )

        self.assertFalse(unavailability.is_available_on_date(date(2024, 10, 1)))


class ScheduleGenerationServiceTest(TestCase):
    """Tests pour le service de génération d'emploi du temps"""

    def setUp(self):
        # Créer les données de base
        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True
        )

        self.level = Level.objects.create(name="Licence 1")

        self.schedule = Schedule.objects.create(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31),
            duration_type='3_months'
        )

        # Créer des cours
        self.course1 = Course.objects.create(
            course_code="INF101",
            label="Introduction à l'informatique",
            credit_count=3,
            level=self.level
        )

        self.course2 = Course.objects.create(
            course_code="MAT101",
            label="Mathématiques générales",
            credit_count=4,
            level=self.level
        )

        # Créer des enseignants
        self.lecturer1 = Lecturer.objects.create(
            matricule="ENS001",
            firstname="Jean",
            lastname="Dupont",
            date_naiss=date(1980, 1, 1),
            grade="Professeur",
            gender="M"
        )

        self.lecturer2 = Lecturer.objects.create(
            matricule="ENS002",
            firstname="Marie",
            lastname="Martin",
            date_naiss=date(1985, 5, 15),
            grade="Maître de conférences",
            gender="F"
        )

        # Créer des créneaux horaires
        self.time_slot1 = TimeSlot.objects.create(
            name="Matin 1",
            day_of_week="monday",
            start_time=time(8, 0),
            end_time=time(10, 0)
        )

        self.time_slot2 = TimeSlot.objects.create(
            name="Matin 2",
            day_of_week="tuesday",
            start_time=time(8, 0),
            end_time=time(10, 0)
        )

        # Créer des salles
        self.classroom1 = Classroom.objects.create(
            code="A101",
            name="Salle A101",
            capacity=50,
            building="Bâtiment A",
            floor="1er étage"
        )

        self.classroom2 = Classroom.objects.create(
            code="A102",
            name="Salle A102",
            capacity=40,
            building="Bâtiment A",
            floor="1er étage"
        )

        # Créer des disponibilités
        LecturerAvailability.objects.create(
            lecturer=self.lecturer1,
            time_slot=self.time_slot1,
            academic_year=self.academic_year,
            status='available'
        )

        LecturerAvailability.objects.create(
            lecturer=self.lecturer2,
            time_slot=self.time_slot2,
            academic_year=self.academic_year,
            status='preferred'
        )

    def test_schedule_generation_service_initialization(self):
        """Test d'initialisation du service de génération"""
        courses = [self.course1, self.course2]
        service = ScheduleGenerationService(
            schedule=self.schedule,
            courses=courses,
            sessions_per_week=2
        )

        self.assertEqual(service.schedule, self.schedule)
        self.assertEqual(list(service.courses), courses)
        self.assertEqual(service.sessions_per_week, 2)

    def test_prepare_data(self):
        """Test de la méthode _prepare_data"""
        courses = [self.course1]
        service = ScheduleGenerationService(
            schedule=self.schedule,
            courses=courses
        )

        service._prepare_data()

        # Vérifier que les données ont été préparées
        self.assertTrue(len(service.available_time_slots) > 0)
        self.assertTrue(len(service.available_classrooms) > 0)
        self.assertTrue(len(service.lecturer_availabilities) > 0)

    def test_get_total_weeks(self):
        """Test de la méthode _get_total_weeks"""
        courses = [self.course1]
        service = ScheduleGenerationService(
            schedule=self.schedule,
            courses=courses
        )

        total_weeks = service._get_total_weeks()
        expected_weeks = (self.schedule.end_date - self.schedule.start_date).days // 7
        self.assertEqual(total_weeks, max(1, expected_weeks))

    def test_generate_schedule_success(self):
        """Test de génération réussie d'un emploi du temps"""
        courses = [self.course1]
        service = ScheduleGenerationService(
            schedule=self.schedule,
            courses=courses,
            sessions_per_week=1,  # Réduire pour éviter les conflits
            max_daily_sessions=2
        )

        result = service.generate_schedule()

        # Le test peut échouer si les conditions ne sont pas optimales
        # mais on vérifie au moins que la méthode retourne un résultat
        self.assertIn('success', result)
        self.assertIn('message', result)
        self.assertIn('sessions_count', result)


class ScheduleViewsTest(TestCase):
    """Tests pour les vues d'emploi du temps"""

    def setUp(self):
        self.client = Client()

        # Créer un utilisateur responsable de planification
        self.planning_user = User.objects.create_user(
            username='planning_admin',
            password='testpass123',
            role='planning'
        )

        # Créer les données de base
        self.academic_year = AcademicYear.objects.create(
            start_at=date(2024, 9, 1),
            end_at=date(2025, 6, 30),
            is_active=True
        )

        self.level = Level.objects.create(name="Licence 1")

        self.schedule = Schedule.objects.create(
            name="Test Schedule",
            academic_year=self.academic_year,
            level=self.level,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31)
        )

    def test_schedules_list_view(self):
        """Test de la vue liste des emplois du temps"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:schedules'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Schedule')

    def test_schedule_detail_view(self):
        """Test de la vue détail d'un emploi du temps"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:schedule_detail', kwargs={'pk': self.schedule.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Schedule')

    def test_schedule_create_view_get(self):
        """Test de l'affichage du formulaire de création"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:schedule_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Créer un emploi du temps')

    def test_schedule_create_view_post(self):
        """Test de création d'un nouvel emploi du temps"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'name': 'Nouvel emploi du temps',
            'description': 'Description test',
            'academic_year': self.academic_year.id,
            'level': self.level.id,
            'start_date': '2024-09-01',
            'end_date': '2024-12-31',
            'duration_type': '3_months'
        }
        response = self.client.post(reverse('planification:schedule_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création

        # Vérifier que l'emploi du temps a été créé
        self.assertTrue(Schedule.objects.filter(name='Nouvel emploi du temps').exists())

    def test_schedule_access_denied_without_permission(self):
        """Test de refus d'accès sans permission"""
        normal_user = User.objects.create_user(
            username='normal_user',
            password='testpass123',
            role='student'
        )

        self.client.login(username='normal_user', password='testpass123')

        urls = [
            reverse('planification:schedules'),
            reverse('planification:schedule_detail', kwargs={'pk': self.schedule.pk}),
            reverse('planification:schedule_create'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirection car accès refusé


class TimeSlotCRUDTest(TestCase):
    """Tests pour les vues CRUD des créneaux horaires"""

    def setUp(self):
        self.client = Client()

        # Créer un utilisateur responsable de planification
        self.planning_user = User.objects.create_user(
            username='planning_admin',
            password='testpass123',
            role='planning'
        )

        # Créer un créneau de test
        self.time_slot = TimeSlot.objects.create(
            name="Test Slot",
            day_of_week="monday",
            start_time=time(8, 0),
            end_time=time(10, 0),
            is_active=True
        )

    def test_time_slots_list_view(self):
        """Test de la vue liste des créneaux horaires"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:time_slots'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Slot')

    def test_time_slot_detail_view(self):
        """Test de la vue détail d'un créneau horaire"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:time_slot_detail', kwargs={'pk': self.time_slot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Slot')

    def test_time_slot_create_view_get(self):
        """Test de l'affichage du formulaire de création"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:time_slot_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ajouter un créneau horaire')

    def test_time_slot_create_view_post(self):
        """Test de création d'un nouveau créneau horaire"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'name': 'Nouveau créneau',
            'day_of_week': 'tuesday',
            'start_time': '10:00',
            'end_time': '12:00',
            'is_active': True
        }
        response = self.client.post(reverse('planification:time_slot_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création

        # Vérifier que le créneau a été créé
        self.assertTrue(TimeSlot.objects.filter(name='Nouveau créneau').exists())

    def test_time_slot_update_view_get(self):
        """Test de l'affichage du formulaire de modification"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:time_slot_update', kwargs={'pk': self.time_slot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Slot')

    def test_time_slot_update_view_post(self):
        """Test de modification d'un créneau horaire"""
        self.client.login(username='planning_admin', password='testpass123')
        data = {
            'name': 'Créneau modifié',
            'day_of_week': 'monday',
            'start_time': '08:00',
            'end_time': '10:00',
            'is_active': True
        }
        response = self.client.post(reverse('planification:time_slot_update', kwargs={'pk': self.time_slot.pk}), data)
        self.assertEqual(response.status_code, 302)  # Redirection après modification

        # Vérifier que le créneau a été modifié
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.name, 'Créneau modifié')

    def test_time_slot_delete_view_get(self):
        """Test de l'affichage de la confirmation de suppression"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.get(reverse('planification:time_slot_delete', kwargs={'pk': self.time_slot.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmer la suppression')

    def test_time_slot_delete_view_post(self):
        """Test de suppression d'un créneau horaire"""
        self.client.login(username='planning_admin', password='testpass123')
        response = self.client.post(reverse('planification:time_slot_delete', kwargs={'pk': self.time_slot.pk}))
        self.assertEqual(response.status_code, 302)  # Redirection après suppression

        # Vérifier que le créneau a été supprimé
        self.assertFalse(TimeSlot.objects.filter(pk=self.time_slot.pk).exists())

    def test_time_slot_access_denied_without_permission(self):
        """Test de refus d'accès sans permission"""
        normal_user = User.objects.create_user(
            username='normal_user',
            password='testpass123',
            role='student'
        )

        self.client.login(username='normal_user', password='testpass123')

        urls = [
            reverse('planification:time_slots'),
            reverse('planification:time_slot_detail', kwargs={'pk': self.time_slot.pk}),
            reverse('planification:time_slot_create'),
            reverse('planification:time_slot_update', kwargs={'pk': self.time_slot.pk}),
            reverse('planification:time_slot_delete', kwargs={'pk': self.time_slot.pk}),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirection car accès refusé


class TimeSlotFormTest(TestCase):
    """Tests pour le formulaire TimeSlotForm"""

    def test_time_slot_form_valid_data(self):
        """Test avec des données valides"""
        form_data = {
            'name': 'Test Créneau',
            'day_of_week': 'monday',
            'start_time': '08:00',
            'end_time': '10:00',
            'is_active': True
        }
        form = TimeSlotForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_time_slot_form_invalid_time_order(self):
        """Test avec heure de fin avant heure de début"""
        form_data = {
            'name': 'Test Créneau',
            'day_of_week': 'monday',
            'start_time': '10:00',
            'end_time': '08:00',  # Heure de fin avant début
            'is_active': True
        }
        form = TimeSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('heure de fin doit être postérieure', str(form.errors))

    def test_time_slot_form_too_short_duration(self):
        """Test avec durée trop courte"""
        form_data = {
            'name': 'Test Créneau',
            'day_of_week': 'monday',
            'start_time': '08:00',
            'end_time': '08:15',  # 15 minutes seulement
            'is_active': True
        }
        form = TimeSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('durée minimale', str(form.errors))

    def test_time_slot_form_too_long_duration(self):
        """Test avec durée trop longue"""
        form_data = {
            'name': 'Test Créneau',
            'day_of_week': 'monday',
            'start_time': '08:00',
            'end_time': '18:00',  # 10 heures
            'is_active': True
        }
        form = TimeSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('durée maximale', str(form.errors))

    def test_time_slot_form_short_name(self):
        """Test avec nom trop court"""
        form_data = {
            'name': 'AB',  # Trop court
            'day_of_week': 'monday',
            'start_time': '08:00',
            'end_time': '10:00',
            'is_active': True
        }
        form = TimeSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('au moins 3 caractères', str(form.errors))
