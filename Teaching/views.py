from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from students.models import Student
from accounts.models import BaseUser, Godfather
import json
from Teaching.models import TeachingMonitoring


from Teaching.models import Evaluation, Lecturer
from .forms import EnseignantForm
from .forms import EvaluationForm
from .forms import Suivi_CoursForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard"""
    template_name = 'Teaching/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Avg, F
        from django.utils import timezone
        from datetime import timedelta
        from academic.models import AcademicYear, Program, Course
        from planification.models import CourseSession

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'

        # Année académique active
        current_year = AcademicYear.objects.filter(is_active=True).first()
        context['current_year'] = current_year

        if current_year:
            today = timezone.now().date()

            # 1. KPIs principaux
            # Nombre total d'enseignants
            total_lecturers = Lecturer.objects.count()

            # Nombre total de cours pour l'année académique
            total_courses = Course.objects.filter(
                teaching_monitorings__academic_year=current_year
            ).distinct().count()

            # Nombre de programmes actifs
            active_programs = Program.objects.filter(
                courses__teaching_monitorings__academic_year=current_year
            ).distinct().count()

            # Suivi des enseignements pour l'année
            teaching_monitorings = TeachingMonitoring.objects.filter(
                academic_year=current_year
            )

            # Calcul du taux de couverture global
            if teaching_monitorings.exists():
                avg_coverage_chapters = teaching_monitorings.aggregate(
                    avg_coverage=Avg(F('chapitre_fait') * 100.0 / F('totalChapterCount'))
                )['avg_coverage'] or 0

                avg_coverage_sessions = teaching_monitorings.aggregate(
                    avg_coverage=Avg(F('contenu_effectif_seance') * 100.0 / F('contenu_seance_prevu'))
                )['avg_coverage'] or 0

                global_coverage = round((avg_coverage_chapters + avg_coverage_sessions) / 2, 1)
            else:
                global_coverage = 0

            context['kpis'] = {
                'total_lecturers': total_lecturers,
                'total_courses': total_courses,
                'active_programs': active_programs,
                'global_coverage': global_coverage,
            }

            # 2. Activités récentes (dernières entrées de suivi)
            recent_monitorings = TeachingMonitoring.objects.filter(
                academic_year=current_year
            ).order_by('-date')[:3]

            context['recent_monitorings'] = recent_monitorings

            # 3. Prochaines séances de cours
            upcoming_sessions = CourseSession.objects.filter(
                academic_year=current_year,
                date__gte=today,
                status='scheduled'
            ).order_by('date', 'time_slot__start_time')[:3]

            context['upcoming_sessions'] = upcoming_sessions

            # 4. Séances du jour
            today_sessions = CourseSession.objects.filter(
                academic_year=current_year,
                date=today
            ).order_by('time_slot__start_time')

            context['today_sessions'] = today_sessions

            # 5. Alertes (cours en retard)
            delayed_monitorings = TeachingMonitoring.objects.filter(
                academic_year=current_year,
                contenu_effectif_seance__lt=F('contenu_seance_prevu')
            ).order_by('date')[:3]

            context['delayed_monitorings'] = delayed_monitorings

            # 6. Calendrier académique
            context['academic_year_start'] = current_year.start_at
            context['academic_year_end'] = current_year.end_at

            # Calculer les périodes importantes (approximation)
            year_duration = (current_year.end_at - current_year.start_at).days

            # Période d'examens (approximation: dernier mois de l'année académique)
            exam_start = current_year.end_at - timedelta(days=30)
            context['exam_period'] = {
                'start': exam_start,
                'end': current_year.end_at - timedelta(days=10)
            }

            # Période de cours (approximation: du début à 1 mois avant la fin)
            context['course_period'] = {
                'start': current_year.start_at + timedelta(days=15),
                'end': exam_start - timedelta(days=10)
            }

        return context


class EnseignantsView(LoginRequiredMixin, TemplateView):
    """Vue pour la visualisationdes enseignants"""
    template_name = 'Teaching/enseignants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération de tous les enseignants
        context['enseignants'] = Lecturer.objects.all()
        context['page_title'] = 'Visualisation des enseignants'
        return context

class ajouter_enseignantView(LoginRequiredMixin, TemplateView):
    """Vue pour l'ajout d'enseignants"""
    model = Lecturer
    form_class = EnseignantForm
    template_name = 'Teaching/ajouter_enseignant.html'
    success_url = '/enseignants/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = EnseignantForm()
        return context

    def post(self, request, *args, **kwargs):
        form = EnseignantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teaching:enseignants')
        else:
            context = self.get_context_data(**kwargs)
            context ['form'] = form
            return self.render_to_response(context)


class DetailEnseignantView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher les détails d'un enseignant"""
    template_name = 'Teaching/detail_enseignant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matricule = kwargs.get('matricule')
        try:
            context['enseignant'] = Lecturer.objects.get(matricule=matricule)
            context['page_title'] = 'Détails de l\'enseignant'
        except Lecturer.DoesNotExist:
            context['enseignant'] = None
            context['error'] = 'Enseignant non trouvé'
        return context


class ModifierEnseignantView(LoginRequiredMixin, TemplateView):
    """Vue pour modifier un enseignant"""
    template_name = 'Teaching/modifier_enseignant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matricule = kwargs.get('matricule')
        try:
            enseignant = Lecturer.objects.get(matricule=matricule)
            context['enseignant'] = enseignant
            context['form'] = EnseignantForm(instance=enseignant)
            context['page_title'] = 'Modifier l\'enseignant'
        except Lecturer.DoesNotExist:
            context['enseignant'] = None
            context['error'] = 'Enseignant non trouvé'
        return context

    def post(self, request, *args, **kwargs):
        matricule = kwargs.get('matricule')
        try:
            enseignant = Lecturer.objects.get(matricule=matricule)
            form = EnseignantForm(request.POST, instance=enseignant)
            if form.is_valid():
                form.save()
                return redirect('teaching:enseignants')
            else:
                context = self.get_context_data(**kwargs)
                context['form'] = form
                return self.render_to_response(context)
        except Lecturer.DoesNotExist:
            return redirect('teaching:enseignants')


class SupprimerEnseignantView(LoginRequiredMixin, TemplateView):
    """Vue pour supprimer un enseignant"""
    template_name = 'Teaching/supprimer_enseignant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matricule = kwargs.get('matricule')
        try:
            context['enseignant'] = Lecturer.objects.get(matricule=matricule)
            context['page_title'] = 'Supprimer l\'enseignant'
        except Lecturer.DoesNotExist:
            context['enseignant'] = None
            context['error'] = 'Enseignant non trouvé'
        return context

    def post(self, request, *args, **kwargs):
        matricule = kwargs.get('matricule')
        try:
            enseignant = Lecturer.objects.get(matricule=matricule)
            enseignant.delete()
            return redirect('teaching:enseignants')
        except Lecturer.DoesNotExist:
            return redirect('teaching:enseignants')


class EvaluationsView(LoginRequiredMixin, TemplateView):
    """Vue pour l'évaluation des enseignants"""
    template_name = 'Teaching/evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération de tous les enseignants
        context['evaluations'] = Evaluation.objects.all()
        context['page_title'] = 'Evaluation des enseignants'
        return context

class ajouter_evaluationView(LoginRequiredMixin, TemplateView):
    """Vue pour l'ajout d'evaluation"""
    model = Evaluation
    form_class = EvaluationForm
    template_name = 'Teaching/ajouter_evaluation.html'
    success_url = '/evaluations/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = EvaluationForm()
        return context

    def post(self, request, *args, **kwargs):
        form = EvaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teaching:evaluations')
        else:
            context = self.get_context_data(**kwargs)
            context ['form'] = form
            return self.render_to_response(context)


class DetailEvaluationView(LoginRequiredMixin, TemplateView):
    """Vue pour afficher les détails d'une évaluation"""
    template_name = 'Teaching/detail_evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluation_id = kwargs.get('pk')
        try:
            context['evaluation'] = Evaluation.objects.get(id=evaluation_id)
            context['page_title'] = 'Détails de l\'évaluation'
        except Evaluation.DoesNotExist:
            context['evaluation'] = None
            context['error'] = 'Évaluation non trouvée'
        return context


class ModifierEvaluationView(LoginRequiredMixin, TemplateView):
    """Vue pour modifier une évaluation"""
    template_name = 'Teaching/modifier_evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluation_id = kwargs.get('pk')
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
            context['evaluation'] = evaluation
            context['form'] = EvaluationForm(instance=evaluation)
            context['page_title'] = 'Modifier l\'évaluation'
        except Evaluation.DoesNotExist:
            context['evaluation'] = None
            context['error'] = 'Évaluation non trouvée'
        return context

    def post(self, request, *args, **kwargs):
        evaluation_id = kwargs.get('pk')
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
            form = EvaluationForm(request.POST, instance=evaluation)
            if form.is_valid():
                form.save()
                return redirect('teaching:evaluations')
            else:
                context = self.get_context_data(**kwargs)
                context['form'] = form
                return self.render_to_response(context)
        except Evaluation.DoesNotExist:
            return redirect('teaching:evaluations')


class SupprimerEvaluationView(LoginRequiredMixin, TemplateView):
    """Vue pour supprimer une évaluation"""
    template_name = 'Teaching/supprimer_evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluation_id = kwargs.get('pk')
        try:
            context['evaluation'] = Evaluation.objects.get(id=evaluation_id)
            context['page_title'] = 'Supprimer l\'évaluation'
        except Evaluation.DoesNotExist:
            context['evaluation'] = None
            context['error'] = 'Évaluation non trouvée'
        return context

    def post(self, request, *args, **kwargs):
        evaluation_id = kwargs.get('pk')
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
            evaluation.delete()
            return redirect('teaching:evaluations')
        except Evaluation.DoesNotExist:
            return redirect('teaching:evaluations')


class Suivi_CoursView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion du suivi des cours"""
    template_name = 'Teaching/suivi_cours.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupération de tous les suivis avec les relations
        suivi_cours = TeachingMonitoring.objects.select_related(
            'lecturer', 'course', 'level', 'academic_year'
        ).all()

        # Filtrage par année académique active si disponible
        from academic.models import AcademicYear, Course, Level
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if active_year:
            suivi_cours = suivi_cours.filter(academic_year=active_year)

        context['suivi_cours'] = suivi_cours
        context['avancements'] = suivi_cours
        context['page_title'] = 'Suivi des Enseignements'

        # Ajout des données pour les filtres
        context['lecturers'] = Lecturer.objects.all()
        context['courses'] = Course.objects.all()
        context['levels'] = Level.objects.all()
        context['academic_years'] = AcademicYear.objects.all()
        context['active_year'] = active_year

        return context
    
class ajouter_suiviView(LoginRequiredMixin, TemplateView):
    """Vue pour l'ajout de suivi"""
    model = TeachingMonitoring
    form_class = Suivi_CoursForm
    template_name = 'Teaching/ajouter_suivi.html'
    success_url = '/suivi_cours/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = Suivi_CoursForm()
        return context

    def post(self, request, *args, **kwargs):
        form = Suivi_CoursForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teaching:suivi_cours') 
        else:
            context = self.get_context_data(**kwargs)
            context ['form'] = form
            return self.render_to_response(context)





class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques"""
    template_name = 'Teaching/statistiques.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count, Avg, Q, F
        from academic.models import AcademicYear, Program, Course, Level
        from planification.models import CourseSession

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'

        # Récupérer les paramètres de filtre
        selected_year_id = self.request.GET.get('academic_year')
        selected_program_id = self.request.GET.get('program')

        # Année académique active par défaut
        if selected_year_id:
            try:
                current_year = AcademicYear.objects.get(id=selected_year_id)
            except AcademicYear.DoesNotExist:
                current_year = AcademicYear.objects.filter(is_active=True).first()
        else:
            current_year = AcademicYear.objects.filter(is_active=True).first()

        # Programme sélectionné
        selected_program = None
        if selected_program_id:
            try:
                selected_program = Program.objects.get(id=selected_program_id)
            except Program.DoesNotExist:
                pass

        # Données pour les filtres
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')
        context['programs'] = Program.objects.all().order_by('name')
        context['current_year'] = current_year
        context['selected_program'] = selected_program

        if current_year:
            # Filtres de base
            base_filters = {'academic_year': current_year}
            if selected_program:
                base_filters['course__program'] = selected_program

            # 1. KPIs principaux
            total_lecturers = Lecturer.objects.count()
            total_courses = Course.objects.filter(**{k: v for k, v in base_filters.items() if k != 'academic_year'}).count()

            # Suivi des enseignements pour l'année
            teaching_monitorings = TeachingMonitoring.objects.filter(**base_filters)
            total_monitoring_entries = teaching_monitorings.count()

            # Calcul du taux de couverture global
            if total_monitoring_entries > 0:
                avg_coverage_chapters = teaching_monitorings.aggregate(
                    avg_coverage=Avg(F('chapitre_fait') * 100.0 / F('totalChapterCount'))
                )['avg_coverage'] or 0

                avg_coverage_sessions = teaching_monitorings.aggregate(
                    avg_coverage=Avg(F('contenu_effectif_seance') * 100.0 / F('contenu_seance_prevu'))
                )['avg_coverage'] or 0

                global_coverage = (avg_coverage_chapters + avg_coverage_sessions) / 2
            else:
                global_coverage = 0

            # Séances programmées
            session_filters = base_filters.copy()
            if 'course__program' in session_filters:
                session_filters['course__program'] = session_filters.pop('course__program')
            total_sessions = CourseSession.objects.filter(**session_filters).count()

            context['kpis'] = {
                'total_lecturers': total_lecturers,
                'total_courses': total_courses,
                'global_coverage': round(global_coverage, 1),
                'total_sessions': total_sessions,
            }

            # 2. Statistiques de suivi pédagogique
            # Répartition par statut d'avancement
            status_stats = {
                'retard': 0,
                'en_cours': 0,
                'termine': 0
            }

            for monitoring in teaching_monitorings:
                status = monitoring.statut_avancement()
                if status in status_stats:
                    status_stats[status] += 1

            # Activités pédagogiques
            if total_monitoring_entries > 0:
                pedagogical_activities = teaching_monitorings.aggregate(
                    travaux_prep=Count('id', filter=Q(travaux_preparatoires=True)),
                    group_work=Count('id', filter=Q(groupWork=True)),
                    class_work=Count('id', filter=Q(classWork=True)),
                    home_work=Count('id', filter=Q(homeWork=True)),
                    pedagogic_activities=Count('id', filter=Q(pedagogicActivities=True)),
                    td_tp=Count('id', filter=Q(TDandTP=True)),
                )

                # Convertir en pourcentages
                for key, value in pedagogical_activities.items():
                    pedagogical_activities[key] = round((value / total_monitoring_entries) * 100, 1)
            else:
                pedagogical_activities = {
                    'travaux_prep': 0, 'group_work': 0, 'class_work': 0,
                    'home_work': 0, 'pedagogic_activities': 0, 'td_tp': 0
                }

            context['monitoring_stats'] = {
                'status_distribution': status_stats,
                'pedagogical_activities': pedagogical_activities,
                'total_entries': total_monitoring_entries,
            }

            # 3. Statistiques d'évaluation
            evaluation_filters = base_filters.copy()
            evaluations = Evaluation.objects.filter(**evaluation_filters)
            total_evaluations = evaluations.count()

            if total_evaluations > 0:
                evaluation_stats = evaluations.aggregate(
                    support_accessible=Count('id', filter=Q(support_cours_acessible=True)),
                    bonne_explication=Count('id', filter=Q(bonne_explication_cours=True)),
                    bonne_reponse=Count('id', filter=Q(bonne_reponse_questions=True)),
                    donne_td=Count('id', filter=Q(donne_TD=True)),
                    donne_projet=Count('id', filter=Q(donne_projet=True)),
                    difficultes=Count('id', filter=Q(difficulte_rencontree=True)),
                )

                # Convertir en pourcentages
                for key, value in evaluation_stats.items():
                    evaluation_stats[key] = round((value / total_evaluations) * 100, 1)

                # Score de satisfaction global
                satisfaction_score = (
                    evaluation_stats['support_accessible'] +
                    evaluation_stats['bonne_explication'] +
                    evaluation_stats['bonne_reponse']
                ) / 3
            else:
                evaluation_stats = {
                    'support_accessible': 0, 'bonne_explication': 0, 'bonne_reponse': 0,
                    'donne_td': 0, 'donne_projet': 0, 'difficultes': 0
                }
                satisfaction_score = 0

            context['evaluation_stats'] = {
                'stats': evaluation_stats,
                'satisfaction_score': round(satisfaction_score, 1),
                'total_evaluations': total_evaluations,
            }

            # 4. Statistiques par niveau et programme
            # Récupérer tous les programmes
            programs = Program.objects.all().order_by('name')
            levels_by_program = {}

            for program in programs:
                # Filtrer les suivis par programme
                program_filters = base_filters.copy()
                program_filters['course__program'] = program

                # Récupérer les niveaux pour ce programme
                levels = Level.objects.filter(
                    courses__program=program
                ).distinct().order_by('name')

                level_stats = []
                for level in levels:
                    # Filtrer les suivis par niveau
                    level_filters = program_filters.copy()
                    level_filters['level'] = level

                    # Compter les cours pour ce niveau et programme
                    course_count = Course.objects.filter(
                        program=program,
                        level=level
                    ).count()

                    # Calculer le taux de couverture pour ce niveau
                    level_monitorings = TeachingMonitoring.objects.filter(**level_filters)
                    level_monitoring_count = level_monitorings.count()

                    if level_monitoring_count > 0:
                        level_coverage = level_monitorings.aggregate(
                            avg_coverage=Avg(F('chapitre_fait') * 100.0 / F('totalChapterCount'))
                        )['avg_coverage'] or 0

                        # Calculer la moyenne des notes (si disponible)
                        level_evaluations = Evaluation.objects.filter(
                            academic_year=current_year,
                            level=level,
                            course__program=program
                        )

                        # Ici, on pourrait calculer une moyenne si on avait un champ de note
                        # Pour l'instant, on utilise un score fictif basé sur les évaluations positives
                        if level_evaluations.count() > 0:
                            positive_eval_count = level_evaluations.filter(
                                bonne_explication_cours=True,
                                support_cours_acessible=True
                            ).count()
                            avg_score = (positive_eval_count / level_evaluations.count()) * 20
                        else:
                            avg_score = 0
                    else:
                        level_coverage = 0
                        avg_score = 0

                    level_stats.append({
                        'level': level,
                        'course_count': course_count,
                        'coverage': round(level_coverage, 1),
                        'avg_score': round(avg_score, 1)
                    })

                if level_stats:  # Ne pas ajouter de programmes sans niveaux
                    levels_by_program[program] = level_stats

            context['levels_by_program'] = levels_by_program

        return context


class ParametresView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres"""
    template_name = 'Teaching/parametres.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paramètres'
        return context






