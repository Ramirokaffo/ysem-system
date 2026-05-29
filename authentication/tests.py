from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import AccessModule


User = get_user_model()


class ModuleAccessLoginTests(TestCase):
    def setUp(self):
        self.scholar = AccessModule.objects.get_or_create(
            code='scholar', defaults={'name': 'Scolarité'}
        )[0]
        self.planning = AccessModule.objects.get_or_create(
            code='planning', defaults={'name': 'Planification'}
        )[0]
        self.teaching = AccessModule.objects.get_or_create(
            code='teaching', defaults={'name': 'Suivi des enseignements'}
        )[0]

    def test_login_redirects_to_only_available_module(self):
        user = User.objects.create_user(username='planner', password='secret123')
        user.accessible_modules.add(self.planning)

        response = self.client.post(reverse('authentication:login'), {
            'username': 'planner',
            'password': 'secret123',
        })

        self.assertRedirects(response, reverse('planification:dashboard'), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertEqual(user.last_accessed_module, 'planning')

    def test_login_redirects_to_module_choice_when_multiple_modules(self):
        user = User.objects.create_user(username='multi', password='secret123')
        user.accessible_modules.add(self.scholar, self.planning)

        response = self.client.post(reverse('authentication:login'), {
            'username': 'multi',
            'password': 'secret123',
        })

        self.assertRedirects(response, reverse('authentication:select_module'), fetch_redirect_response=False)

    def test_module_choice_saves_last_accessed_module(self):
        user = User.objects.create_user(username='multi', password='secret123')
        user.accessible_modules.add(self.scholar, self.teaching)
        self.client.force_login(user)

        response = self.client.post(reverse('authentication:select_module'), {'module': 'teaching'})

        self.assertRedirects(response, reverse('teaching:Teaching'), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertEqual(user.last_accessed_module, 'teaching')

    def test_module_middleware_blocks_unassigned_module(self):
        user = User.objects.create_user(username='scholar', password='secret123')
        user.accessible_modules.add(self.scholar)
        self.client.force_login(user)

        response = self.client.get(reverse('planification:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('main:dashboard'))
