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

    @staticmethod
    def _compute_percentage(count, total):
        return round((count / total) * 100, 1) if total else 0

    def _decorate_stats(self, stats, label_key, total, colors):
        for index, stat in enumerate(stats):
            stat['label'] = stat.get(label_key) or 'Non spécifié'
            stat['percentage'] = self._compute_percentage(stat['count'], total)
            stat['color'] = colors[index % len(colors)]
        return stats

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from schools.models import School

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'

        # Paramètres de filtrage
        selected_year = self.request.GET.get('year')
        selected_program = self.request.GET.get('program')
        selected_school = self.request.GET.get('school')
        selected_gender = self.request.GET.get('gender')
        selected_lang = self.request.GET.get('lang')
        selected_start_level = self.request.GET.get('start_level')
        selected_current_level = self.request.GET.get('current_level')
        selected_speciality = self.request.GET.get('speciality')
        selected_document_status = self.request.GET.get('document_status')
        selected_document_type = self.request.GET.get('document_type')

        # Données de référence pour les filtres
        academic_years = AcademicYear.objects.all().order_by('-start_at')
        programs = Program.objects.all().order_by('name')
        schools = School.objects.all().order_by('name')
        levels = Level.objects.all().order_by('academic_order', 'name')
        specialities = Speciality.objects.select_related('program').order_by('name')

        active_year = AcademicYear.get_active_year()
        if selected_year == 'all':
            current_year = None
            selected_year_value = 'all'
        elif selected_year:
            current_year = AcademicYear.objects.filter(id=selected_year).first() or active_year
            selected_year_value = str(current_year.id) if current_year else ''
        else:
            current_year = active_year
            selected_year_value = str(current_year.id) if current_year else ''

        colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#2e59d9', '#17a2b8', '#fd7e14']
        gender_labels = dict(Student._meta.get_field('gender').choices)
        language_choices = list(Student._meta.get_field('lang').choices)
        document_status_labels = dict(OfficialDocument._meta.get_field('status').choices)
        document_type_labels = dict(OfficialDocument.TYPE_CHOICES)
        document_status_colors = {
            'available': '#1cc88a',
            'withdrawn': '#f6c23e',
            'returned': '#36b9cc',
            'lost': '#e74a3b',
        }
        document_type_colors = {
            OfficialDocument.TYPE_STUDENT_CARD: '#4e73df',
            OfficialDocument.TYPE_TRANSCRIPT: '#36b9cc',
            OfficialDocument.TYPE_DIPLOMA: '#f6c23e',
            OfficialDocument.TYPE_CERTIFICATE: '#1cc88a',
            OfficialDocument.TYPE_REGISTRATION_CERTIFICATE: '#e74a3b',
        }
        gender_colors = {'M': '#4e73df', 'F': '#e74a3b'}

        # Jeu de données de base pour la scolarité
        base_student_levels = StudentLevel.objects.filter(
            student__status='registered'
        ).select_related(
            'student',
            'student__program',
            'student__school',
            'student__start_level',
            'level',
            'academic_year',
            'speciality',
        )

        if current_year:
            base_student_levels = base_student_levels.filter(academic_year=current_year)
        if selected_program:
            base_student_levels = base_student_levels.filter(student__program_id=selected_program)
        if selected_school:
            base_student_levels = base_student_levels.filter(student__school_id=selected_school)
        if selected_gender:
            base_student_levels = base_student_levels.filter(student__gender=selected_gender)
        if selected_lang:
            base_student_levels = base_student_levels.filter(student__lang=selected_lang)
        if selected_start_level:
            base_student_levels = base_student_levels.filter(student__start_level_id=selected_start_level)
        if selected_current_level:
            base_student_levels = base_student_levels.filter(level_id=selected_current_level)
        if selected_speciality:
            base_student_levels = base_student_levels.filter(speciality_id=selected_speciality)

        documents_query = OfficialDocument.objects.filter(student_level__in=base_student_levels)
        if selected_document_status:
            documents_query = documents_query.filter(status=selected_document_status)
        if selected_document_type:
            documents_query = documents_query.filter(type=selected_document_type)

        filtered_student_levels = base_student_levels
        if selected_document_status or selected_document_type:
            matching_level_ids = documents_query.values_list('student_level_id', flat=True)
            filtered_student_levels = base_student_levels.filter(id__in=matching_level_ids).distinct()

        students_query = Student.objects.filter(
            status='registered',
            student_levels__in=filtered_student_levels,
        ).distinct()

        documents_query = OfficialDocument.objects.filter(student_level__in=filtered_student_levels)
        if selected_document_status:
            documents_query = documents_query.filter(status=selected_document_status)
        if selected_document_type:
            documents_query = documents_query.filter(type=selected_document_type)

        # KPI principaux
        total_students = students_query.count()
        total_documents = documents_query.count()
        withdrawn_documents = documents_query.filter(status='withdrawn').count()
        available_documents = documents_query.filter(status='available').count()
        levels_count = filtered_student_levels.values('level_id').distinct().count()
        represented_schools_count = students_query.exclude(school__isnull=True).values('school_id').distinct().count()
        active_specialities_count = filtered_student_levels.exclude(speciality__isnull=True).values('speciality_id').distinct().count()
        documents_per_student = round(total_documents / total_students, 1) if total_students else 0
        document_withdrawal_rate = self._compute_percentage(withdrawn_documents, total_documents)

        if current_year:
            new_enrollments = students_query.filter(
                created_at__date__gte=current_year.start_at,
                created_at__date__lte=current_year.end_at,
            ).count()
        else:
            new_enrollments = students_query.count()

        # Répartitions
        gender_stats = list(
            students_query.values('gender').annotate(count=Count('id')).order_by('gender')
        )
        for stat in gender_stats:
            stat['label'] = gender_labels.get(stat['gender'], 'Non spécifié')
            stat['percentage'] = self._compute_percentage(stat['count'], total_students)
            stat['color'] = gender_colors.get(stat['gender'], '#858796')

        level_stats = self._decorate_stats(
            list(
                filtered_student_levels.values('level__name').annotate(
                    count=Count('student_id', distinct=True)
                ).order_by('level__academic_order', 'level__name')
            ),
            'level__name',
            total_students,
            colors,
        )

        program_stats = self._decorate_stats(
            list(
                students_query.values('program__name').annotate(
                    count=Count('id')
                ).order_by('-count', 'program__name')
            ),
            'program__name',
            total_students,
            colors,
        )

        school_stats = self._decorate_stats(
            list(
                students_query.values('school__name').annotate(
                    count=Count('id')
                ).order_by('-count', 'school__name')[:8]
            ),
            'school__name',
            total_students,
            colors,
        )

        speciality_stats = self._decorate_stats(
            list(
                filtered_student_levels.exclude(speciality__isnull=True).values('speciality__name').annotate(
                    count=Count('student_id', distinct=True)
                ).order_by('-count', 'speciality__name')[:8]
            ),
            'speciality__name',
            total_students,
            colors,
        )

        document_stats = list(
            documents_query.values('status').annotate(count=Count('id')).order_by('status')
        )
        for stat in document_stats:
            stat['label'] = document_status_labels.get(stat['status'], stat['status'])
            stat['percentage'] = self._compute_percentage(stat['count'], total_documents)
            stat['color'] = document_status_colors.get(stat['status'], '#858796')

        document_type_stats = list(
            documents_query.values('type').annotate(count=Count('id')).order_by('-count', 'type')
        )
        for stat in document_type_stats:
            stat['label'] = document_type_labels.get(stat['type'], stat['type'])
            stat['percentage'] = self._compute_percentage(stat['count'], total_documents)
            stat['color'] = document_type_colors.get(stat['type'], '#858796')

        male_percentage = 0
        female_percentage = 0
        for stat in gender_stats:
            if stat['gender'] == 'M':
                male_percentage = stat['percentage']
            elif stat['gender'] == 'F':
                female_percentage = stat['percentage']

        # Filtres appliqués affichables dans l'interface
        applied_filters = []
        if selected_year_value == 'all':
            applied_filters.append({'label': 'Année académique', 'value': 'Toutes les années'})
        elif current_year:
            applied_filters.append({'label': 'Année académique', 'value': current_year.name})

        selected_program_obj = programs.filter(pk=selected_program).first() if selected_program else None
        selected_school_obj = schools.filter(pk=selected_school).first() if selected_school else None
        selected_start_level_obj = levels.filter(pk=selected_start_level).first() if selected_start_level else None
        selected_current_level_obj = levels.filter(pk=selected_current_level).first() if selected_current_level else None
        selected_speciality_obj = specialities.filter(pk=selected_speciality).first() if selected_speciality else None

        if selected_program_obj:
            applied_filters.append({'label': 'Programme', 'value': selected_program_obj.name})
        if selected_school_obj:
            applied_filters.append({'label': 'École', 'value': selected_school_obj.name})
        if selected_gender:
            applied_filters.append({'label': 'Genre', 'value': gender_labels.get(selected_gender, selected_gender)})
        if selected_lang:
            applied_filters.append({'label': 'Langue', 'value': dict(language_choices).get(selected_lang, selected_lang)})
        if selected_start_level_obj:
            applied_filters.append({'label': 'Niveau d’entrée', 'value': selected_start_level_obj.name})
        if selected_current_level_obj:
            applied_filters.append({'label': 'Niveau actuel', 'value': selected_current_level_obj.name})
        if selected_speciality_obj:
            applied_filters.append({'label': 'Spécialité', 'value': selected_speciality_obj.name})
        if selected_document_status:
            applied_filters.append({'label': 'Statut document', 'value': document_status_labels.get(selected_document_status, selected_document_status)})
        if selected_document_type:
            applied_filters.append({'label': 'Type document', 'value': document_type_labels.get(selected_document_type, selected_document_type)})

        context.update({
            'academic_years': academic_years,
            'programs': programs,
            'schools': schools,
            'levels': levels,
            'specialities': specialities,
            'current_year': current_year,
            'current_period_label': current_year.name if current_year else 'Toutes les années',
            'selected_year': selected_year_value,
            'selected_program': selected_program or '',
            'selected_school': selected_school or '',
            'selected_gender': selected_gender or '',
            'selected_lang': selected_lang or '',
            'selected_start_level': selected_start_level or '',
            'selected_current_level': selected_current_level or '',
            'selected_speciality': selected_speciality or '',
            'selected_document_status': selected_document_status or '',
            'selected_document_type': selected_document_type or '',
            'gender_choices': Student._meta.get_field('gender').choices,
            'language_choices': language_choices,
            'document_status_choices': OfficialDocument._meta.get_field('status').choices,
            'document_type_choices': OfficialDocument.TYPE_CHOICES,
            'filters_expanded': bool(self.request.GET),
            'applied_filters': applied_filters,
            'total_students': total_students,
            'new_enrollments': new_enrollments,
            'gender_stats': gender_stats,
            'level_stats': level_stats,
            'document_stats': document_stats,
            'document_type_stats': document_type_stats,
            'total_documents': total_documents,
            'program_stats': program_stats,
            'school_stats': school_stats,
            'speciality_stats': speciality_stats,
            'withdrawn_documents': withdrawn_documents,
            'available_documents': available_documents,
            'levels_count': levels_count,
            'represented_schools_count': represented_schools_count,
            'active_specialities_count': active_specialities_count,
            'documents_per_student': documents_per_student,
            'document_withdrawal_rate': document_withdrawal_rate,
            'male_percentage': male_percentage,
            'female_percentage': female_percentage,
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


