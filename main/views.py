from collections import defaultdict
from decimal import Decimal

from django.shortcuts import redirect
from django.db import models

from main.utils import *
from students.models import OfficialDocument, Student, StudentLevel
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone

from academic.models import AcademicYear, Level, Program, Speciality
from audit.utils import log_audit_event
from .program_documents import (
    build_program_document_payload,
)
import logging
from django.core.paginator import Paginator
from student_portal.decorators import scholar_admin_required
from payments.models import Payment, PaymentInstallment

from django.contrib import messages
from .models import SystemSettings
from .forms import (
    GeneralSettingsForm, AcademicSettingsForm, ProgramLevelSettingsForm,
    UserSettingsForm, DocumentSettingsForm, NotificationSettingsForm,
    DataManagementSettingsForm
)

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """Vue d'accueil publique"""
    template_name = 'main/home.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard"""
    template_name = 'main/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from datetime import datetime, timedelta
        from academic.models import Program

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'

        # Année académique active
        current_year = AcademicYear.objects.filter(is_active=True).first()
        context['current_year'] = current_year

        # Statistiques générales
        total_students = Student.objects.filter(status='registered').count()
        pending_students = Student.objects.filter(status='pending').count()
        total_programs = Program.objects.count()

        # Documents en attente (disponibles non retirés)
        pending_documents = OfficialDocument.objects.filter(status='available').count()

        # Nouvelles inscriptions (derniers 30 jours)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_enrollments = Student.objects.filter(
            created_at__gte=thirty_days_ago,
            status='registered'
        ).count()

        # Activités récentes (derniers étudiants inscrits)
        recent_students = Student.objects.filter(
            status='registered'
        ).order_by('-last_registration_date')[:5]

        # Documents récemment créés
        recent_documents = OfficialDocument.objects.select_related(
            'student_level__student',
            'student_level__level'
        ).order_by('-created_at')[:5]

        # Étudiants en attente d'approbation
        students_pending_approval = Student.objects.filter(
            status='pending'
        ).order_by('-created_at')[:3]

        # Statistiques par niveau
        level_stats = StudentLevel.objects.filter(
            is_active=True,
            student__status='registered'
        ).values('level__name').annotate(count=Count('student')).order_by('-count')[:5]

        # Statistiques de prospection
        prospection_stats = {}
        try:
            from prospection.models import Agent, Campagne, Equipe, Prospect
            prospection_stats = {
                'total_agents': Agent.objects.filter(statut='actif').count(),
                'campagnes_actives': Campagne.objects.filter(statut='en_cours').count(),
                'total_equipes': Equipe.objects.count(),
                'prospects_ce_mois': Prospect.objects.filter(
                    date_collecte__gte=datetime.now().replace(day=1)
                ).count(),
            }
        except ImportError:
            # Module prospection pas encore migré
            pass

        context.update({
            'total_students': total_students,
            'pending_students': pending_students,
            'new_enrollments': new_enrollments,
            'pending_documents': pending_documents,
            'total_programs': total_programs,
            'recent_students': recent_students,
            'recent_documents': recent_documents,
            'students_pending_approval': students_pending_approval,
            'level_stats': level_stats,
            'prospection_stats': prospection_stats,
        })

        return context


class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques"""
    template_name = 'main/statistiques.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from academic.models import Program

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'

        # Récupération des paramètres de filtrage
        selected_year = self.request.GET.get('year')
        selected_program = self.request.GET.get('program')

        # Années académiques disponibles
        academic_years = AcademicYear.objects.all().order_by('-start_at')
        context['academic_years'] = academic_years

        # Programmes disponibles
        programs = Program.objects.all()
        context['programs'] = programs

        # Année académique active ou sélectionnée
        if selected_year:
            try:
                current_year = AcademicYear.objects.get(id=selected_year)
            except AcademicYear.DoesNotExist:
                current_year = AcademicYear.objects.filter(is_active=True).first()
        else:
            current_year = AcademicYear.objects.filter(is_active=True).first()

        context['current_year'] = current_year
        context['selected_year'] = selected_year
        context['selected_program'] = selected_program

        # Filtrage des étudiants
        students_query = Student.objects.filter(status='registered')
        if selected_program:
            students_query = students_query.filter(program_id=selected_program)

        # Statistiques générales
        total_students = students_query.count()

        # Nouvelles inscriptions (étudiants créés cette année)
        if current_year:
            new_enrollments = students_query.filter(
                created_at__gte=current_year.start_at,
                created_at__lte=current_year.end_at
            ).count()
        else:
            new_enrollments = 0

        # Étudiants par genre
        gender_stats = students_query.values('gender').annotate(count=Count('gender'))

        # Étudiants par niveau (basé sur StudentLevel actif)
        level_stats = StudentLevel.objects.filter(
            is_active=True,
            student__status='registered'
        ).values('level__name').annotate(count=Count('student')).order_by('level__name')

        if selected_program:
            level_stats = level_stats.filter(student__program_id=selected_program)

        # Statistiques des documents
        document_stats = OfficialDocument.objects.values('status').annotate(count=Count('status'))
        total_documents = sum([stat['count'] for stat in document_stats])

        # Répartition par programme
        program_stats = students_query.values('program__name').annotate(count=Count('program')).order_by('-count')

        # Calcul des pourcentages pour les programmes
        colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#2e59d9', '#17a2b8', '#fd7e14']
        for i, stat in enumerate(program_stats):
            if total_students > 0:
                stat['percentage'] = round((stat['count'] / total_students) * 100, 1)
            else:
                stat['percentage'] = 0
            stat['color'] = colors[i % len(colors)]

        context.update({
            'total_students': total_students,
            'new_enrollments': new_enrollments,
            'gender_stats': gender_stats,
            'level_stats': level_stats,
            'document_stats': document_stats,
            'total_documents': total_documents,
            'program_stats': program_stats,
        })

        return context


class ParametresView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres"""
    template_name = 'main/parametres.html'

    def get_context_data(self, **kwargs):
        from .models import SystemSettings
        from .forms import (
            GeneralSettingsForm, AcademicSettingsForm, ProgramLevelSettingsForm,
            UserSettingsForm, DocumentSettingsForm, NotificationSettingsForm,
            DataManagementSettingsForm
        )

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paramètres'

        # Récupérer les paramètres système
        settings = SystemSettings.get_settings()

        # Créer les formulaires avec les données actuelles
        context['general_form'] = GeneralSettingsForm(instance=settings)
        context['academic_form'] = AcademicSettingsForm(instance=settings)
        context['program_level_form'] = ProgramLevelSettingsForm(instance=settings)
        context['user_form'] = UserSettingsForm(instance=settings)
        context['document_form'] = DocumentSettingsForm(instance=settings)
        context['notification_form'] = NotificationSettingsForm(instance=settings)
        context['data_management_form'] = DataManagementSettingsForm(instance=settings)

        # Ajouter la configuration de prospection
        try:
            from prospection.models import ProspectionConfig
            context['prospection_config'] = ProspectionConfig.get_or_create_config()
        except:
            # Module prospection pas encore migré
            context['prospection_config'] = None

        # Ajouter les données pour les sélecteurs dynamiques
        context['programs'] = Program.objects.all().order_by('name')
        context['levels'] = Level.objects.all().order_by('name')

        # Ajouter les années académiques pour la sélection
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')

        return context

    def post(self, request, *args, **kwargs):


        # Récupérer les paramètres système
        settings = SystemSettings.get_settings()

        # Déterminer quel formulaire a été soumis
        form_type = request.POST.get('form_type')

        if form_type == 'general':
            form = GeneralSettingsForm(request.POST, request.FILES, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres généraux mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres généraux.')

        elif form_type == 'academic':
            form = AcademicSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres académiques mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres académiques.')

        elif form_type == 'program_level':
            form = ProgramLevelSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres des programmes et niveaux mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres des programmes et niveaux.')

        elif form_type == 'user':
            form = UserSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres utilisateurs mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres utilisateurs.')

        elif form_type == 'document':
            form = DocumentSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres des documents mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres des documents.')

        elif form_type == 'notification':
            form = NotificationSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres de notification mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres de notification.')

        elif form_type == 'data_management':
            form = DataManagementSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres de gestion des données mis à jour avec succès.')
                return redirect('main:parametres')
            else:
                messages.error(request, 'Erreur lors de la mise à jour des paramètres de gestion des données.')

        elif form_type == 'academic_year':
            # Gestion du changement d'année académique active
            academic_year_id = request.POST.get('active_academic_year')
            if academic_year_id:
                try:
                    academic_year = AcademicYear.objects.get(id=academic_year_id)
                    previous_academic_year_id = request.session.get('active_academic_year_id')
                    request.session['active_academic_year_id'] = academic_year.id
                    log_audit_event(
                        category='business',
                        action='update',
                        actor=request.user,
                        instance=academic_year,
                        changes={
                            'active_academic_year_id': {
                                'from': previous_academic_year_id,
                                'to': academic_year.id,
                            }
                        },
                        context={
                            'operation': 'switch_active_academic_year',
                            'selected_academic_year': str(academic_year),
                        },
                        message="Changement de l'année académique active de la session.",
                    )
                    messages.success(request, f'Année académique active changée vers {academic_year}.')
                    return redirect('main:parametres')
                except AcademicYear.DoesNotExist:
                    messages.error(request, 'Année académique invalide.')
            else:
                messages.error(request, 'Aucune année académique sélectionnée.')

        elif form_type == 'prospection':
            # Gestion de la configuration de prospection
            try:
                from prospection.models import ProspectionConfig
                config = ProspectionConfig.get_or_create_config()
                is_active = request.POST.get('prospection_active') == 'on'
                config.is_active = is_active
                config.save()

                status = "activée" if is_active else "désactivée"
                messages.success(request, f'Prospection {status} avec succès.')
                return redirect('main:parametres')
            except Exception as e:
                messages.error(request, f'Erreur lors de la mise à jour de la prospection: {str(e)}')

        # Si aucun form_type valide n'est trouvé, rediriger avec erreur
        messages.error(request, 'Type de formulaire non reconnu.')
        return redirect('main:parametres')


def test_404_view(request):
    """Vue de test pour la page 404"""
    from django.http import Http404
    raise Http404("Page de test 404")


def test_500_view(request):
    """Vue de test pour la page 500"""
    raise Exception("Erreur de test 500")


def test_403_view(request):
    """Vue de test pour la page 403"""
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied("Accès interdit de test")


@login_required
@scholar_admin_required
def toggle_prospection(request):
    """Vue pour activer/désactiver la prospection"""
    if request.method == 'POST':
        try:
            from prospection.models import ProspectionConfig
            config = ProspectionConfig.get_or_create_config()
            config.is_active = not config.is_active
            config.modified_by = request.user.username
            config.save()

            status = "activée" if config.is_active else "désactivée"
            messages.success(request, f'Prospection {status} avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification: {e}')

    return redirect('main:parametres')


class ProfilView(LoginRequiredMixin, TemplateView):
    """Vue pour le profil utilisateur"""
    template_name = 'main/profil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Mon Profil'
        return context


class UserProfileView(LoginRequiredMixin, TemplateView):
    """Vue pour le profil utilisateur"""
    template_name = 'main/profil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Mon Profil'

        # Informations sur l'utilisateur connecté
        user = self.request.user
        context['user'] = user

        # Statistiques personnelles si l'utilisateur est un administrateur
        if hasattr(user, 'role'):
            # Nombre d'étudiants gérés récemment
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)

            recent_approvals = Student.objects.filter(
                status='registered',
                last_updated__gte=thirty_days_ago
            ).count()

            context['recent_approvals'] = recent_approvals

            # Dernière connexion
            context['last_login'] = user.last_login

            # Date de création du compte
            context['date_joined'] = user.date_joined

        return context


def get_specialities_by_program(request):
    """
    Vue AJAX pour récupérer les spécialités d'un programme donné
    """
    program_id = request.GET.get('program_id')
    documents_mode = request.GET.get('documents_mode')

    try:
        program = get_program_from_value(program_id)
        # Récupérer les spécialités du programme
        specialities = Speciality.objects.filter(program_id=program_id).values('id', 'name') if program_id else []
        specialities_list = list(specialities)
        document_payload_kwargs = {}

        if documents_mode == 'admin_only_optional':
            document_payload_kwargs = {
                'fallback_visible_fields': None,
                'force_optional': True,
            }

        return JsonResponse({
            'success': True,
            'specialities': specialities_list,
            'documents': build_program_document_payload(program=program, **document_payload_kwargs),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


