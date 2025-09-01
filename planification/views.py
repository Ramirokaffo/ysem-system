from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from datetime import datetime, timedelta

from .models import Classroom, TimeSlot, CourseSession, Schedule, LecturerAvailability, ScheduleSession, Equipment
from .forms import (
    ClassroomForm, ClassroomSearchForm, LecturerForm, LecturerSearchForm,
    ScheduleForm, LecturerAvailabilityForm, ScheduleGenerationForm,
    TimeSlotForm, TimeSlotSearchForm, CourseSessionForm
)
from .services import ScheduleGenerationService
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear
from student_portal.decorators import planning_admin_required


@method_decorator(planning_admin_required, name='dispatch')
class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard planification"""
    template_name = 'planification/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard Planification'

        # Année académique active
        current_year = AcademicYear.objects.filter(is_active=True).first()
        context['current_year'] = current_year

        # Statistiques générales
        context['stats'] = {
            'total_classrooms': Classroom.objects.filter(is_active=True).count(),
            'total_lecturers': Lecturer.objects.count(),
            'total_courses': Course.objects.count(),
            'total_time_slots': TimeSlot.objects.filter(is_active=True).count(),
            'total_schedules': Schedule.objects.count(),
            'active_schedules': Schedule.objects.filter(status='active').count(),
            'draft_schedules': Schedule.objects.filter(status='draft').count(),
        }

        if current_year:
            # Statistiques des séances pour l'année en cours
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            sessions_this_week = CourseSession.objects.filter(
                academic_year=current_year,
                date__range=[week_start, week_end]
            )

            context['session_stats'] = {
                'this_week': sessions_this_week.count(),
                'scheduled': sessions_this_week.filter(status='scheduled').count(),
                'completed': sessions_this_week.filter(status='completed').count(),
                'cancelled': sessions_this_week.filter(status='cancelled').count(),
            }

            # Prochaines séances
            context['upcoming_sessions'] = CourseSession.objects.filter(
                academic_year=current_year,
                date__gte=today,
                status='scheduled'
            ).order_by('date', 'time_slot__start_time')[:5]

            # Salles les plus utilisées
            context['popular_classrooms'] = Classroom.objects.annotate(
                session_count=Count('sessions', filter=Q(sessions__academic_year=current_year))
            ).order_by('-session_count')[:5]

        return context


@method_decorator(planning_admin_required, name='dispatch')
class ClassroomsView(LoginRequiredMixin, ListView):
    """Vue pour la gestion des salles de classe"""
    model = Classroom
    template_name = 'planification/classrooms.html'
    context_object_name = 'classrooms'
    paginate_by = 20

    def get_queryset(self):
        queryset = Classroom.objects.all().order_by('code')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(building__icontains=search)
            )

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Salles'
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context


@method_decorator(planning_admin_required, name='dispatch')
class LecturersView(LoginRequiredMixin, ListView):
    """Vue pour la visualisation des enseignants"""
    model = Lecturer
    template_name = 'planification/lecturers.html'
    context_object_name = 'lecturers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Lecturer.objects.all().order_by('lastname', 'firstname')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(matricule__icontains=search) |
                Q(firstname__icontains=search) |
                Q(lastname__icontains=search) |
                Q(email__icontains=search)
            )

        grade = self.request.GET.get('grade')
        if grade:
            queryset = queryset.filter(grade__icontains=grade)

        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)

        lang = self.request.GET.get('lang')
        if lang:
            queryset = queryset.filter(lang=lang)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Enseignants'
        context['search'] = self.request.GET.get('search', '')
        context['grade'] = self.request.GET.get('grade', '')
        context['gender'] = self.request.GET.get('gender', '')
        context['lang'] = self.request.GET.get('lang', '')

        # Liste des grades pour le filtre
        context['grades'] = Lecturer.objects.values_list('grade', flat=True).distinct().order_by('grade')

        # Formulaire de recherche
        context['search_form'] = LecturerSearchForm(self.request.GET)

        return context


@method_decorator(planning_admin_required, name='dispatch')
class TimeSlotsView(LoginRequiredMixin, ListView):
    """Vue pour la gestion des créneaux horaires"""
    model = TimeSlot
    template_name = 'planification/time_slots.html'
    context_object_name = 'time_slots'
    paginate_by = 20

    def get_queryset(self):
        queryset = TimeSlot.objects.all().order_by('day_of_week', 'start_time')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        day_of_week = self.request.GET.get('day_of_week')
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        time_period = self.request.GET.get('time_period')
        if time_period == 'morning':
            queryset = queryset.filter(start_time__gte='06:00', start_time__lt='12:00')
        elif time_period == 'afternoon':
            queryset = queryset.filter(start_time__gte='12:00', start_time__lt='18:00')
        elif time_period == 'evening':
            queryset = queryset.filter(start_time__gte='18:00', start_time__lt='22:00')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Créneaux Horaires'

        # Formulaire de recherche
        context['search_form'] = TimeSlotSearchForm(self.request.GET)

        # Conserver les filtres dans le contexte
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'day_of_week': self.request.GET.get('day_of_week', ''),
            'status': self.request.GET.get('status', ''),
            'time_period': self.request.GET.get('time_period', ''),
        }

        return context


@method_decorator(planning_admin_required, name='dispatch')
class TimeSlotDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'un créneau horaire"""
    model = TimeSlot
    template_name = 'planification/time_slot_detail.html'
    context_object_name = 'time_slot'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Détails - {self.object.name}'

        # Statistiques d'utilisation du créneau
        current_year = AcademicYear.objects.filter(is_active=True).first()
        if current_year:
            sessions = CourseSession.objects.filter(
                time_slot=self.object,
                academic_year=current_year
            )
            context['usage_stats'] = {
                'total_sessions': sessions.count(),
                'scheduled_sessions': sessions.filter(status='scheduled').count(),
                'completed_sessions': sessions.filter(status='completed').count(),
                'cancelled_sessions': sessions.filter(status='cancelled').count(),
            }

            # Prochaines séances dans ce créneau
            context['upcoming_sessions'] = sessions.filter(
                date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('date')[:5]

            # Disponibilités des enseignants pour ce créneau
            context['lecturer_availabilities'] = LecturerAvailability.objects.filter(
                time_slot=self.object,
                academic_year=current_year
            ).select_related('lecturer').order_by('lecturer__lastname')

        return context


@method_decorator(planning_admin_required, name='dispatch')
class TimeSlotCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau créneau horaire"""
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'planification/time_slot_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter un créneau horaire'
        context['form_title'] = 'Nouveau créneau horaire'
        context['submit_text'] = 'Créer le créneau'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Le créneau "{form.instance.name}" a été créé avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:time_slot_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class TimeSlotUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un créneau horaire"""
    model = TimeSlot
    form_class = TimeSlotForm
    template_name = 'planification/time_slot_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier - {self.object.name}'
        context['form_title'] = f'Modifier le créneau {self.object.name}'
        context['submit_text'] = 'Enregistrer les modifications'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Le créneau "{form.instance.name}" a été modifié avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:time_slot_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class TimeSlotDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un créneau horaire"""
    model = TimeSlot
    template_name = 'planification/time_slot_confirm_delete.html'
    success_url = reverse_lazy('planification:time_slots')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Supprimer - {self.object.name}'

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(time_slot=self.object).count()
        context['sessions_count'] = sessions_count
        context['has_sessions'] = sessions_count > 0

        # Vérifier s'il y a des disponibilités associées
        availabilities_count = LecturerAvailability.objects.filter(time_slot=self.object).count()
        context['availabilities_count'] = availabilities_count
        context['has_availabilities'] = availabilities_count > 0

        return context

    def delete(self, request, *args, **kwargs):
        time_slot = self.get_object()

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(time_slot=time_slot).count()
        availabilities_count = LecturerAvailability.objects.filter(time_slot=time_slot).count()

        if sessions_count > 0 or availabilities_count > 0:
            messages.error(
                request,
                f'Impossible de supprimer le créneau "{time_slot.name}". '
                f'Il est utilisé dans {sessions_count} séance(s) de cours '
                f'et {availabilities_count} disponibilité(s) d\'enseignant. '
                f'Veuillez d\'abord supprimer ou modifier ces éléments.'
            )
            return redirect('planification:time_slot_detail', pk=time_slot.pk)

        messages.success(
            request,
            f'Le créneau "{time_slot.name}" a été supprimé avec succès.'
        )
        return super().delete(request, *args, **kwargs)


@method_decorator(planning_admin_required, name='dispatch')
class SessionsView(LoginRequiredMixin, ListView):
    """Vue pour la gestion des séances de cours"""
    model = CourseSession
    template_name = 'planification/sessions.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        queryset = CourseSession.objects.select_related(
            'course', 'lecturer', 'classroom', 'time_slot', 'level', 'academic_year'
        ).order_by('-date', 'time_slot__start_time')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(course__label__icontains=search) |
                Q(lecturer__firstname__icontains=search) |
                Q(lecturer__lastname__icontains=search) |
                Q(classroom__name__icontains=search) |
                Q(topic__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level_id=level)

        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        else:
            # Par défaut, afficher l'année académique active
            current_year = AcademicYear.objects.filter(is_active=True).first()
            if current_year:
                queryset = queryset.filter(academic_year=current_year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Séances de Cours'
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['level'] = self.request.GET.get('level', '')
        context['academic_year'] = self.request.GET.get('academic_year', '')

        # Données pour les filtres
        context['levels'] = Level.objects.all().order_by('name')
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')
        context['session_statuses'] = CourseSession.SESSION_STATUS

        return context


# ==================== CRUD VIEWS FOR COURSE SESSIONS ====================

@method_decorator(planning_admin_required, name='dispatch')
class CourseSessionDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une séance de cours"""
    model = CourseSession
    template_name = 'planification/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Séance - {self.object.course.label}'
        return context


@method_decorator(planning_admin_required, name='dispatch')
class CourseSessionCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle séance de cours"""
    model = CourseSession
    form_class = CourseSessionForm
    template_name = 'planification/session_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Programmer une séance'
        context['form_title'] = 'Nouvelle séance de cours'
        context['submit_text'] = 'Programmer la séance'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'La séance "{form.instance.course.label}" a été programmée avec succès '
            f'pour le {form.instance.date.strftime("%d/%m/%Y")}.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:session_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class CourseSessionUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une séance de cours"""
    model = CourseSession
    form_class = CourseSessionForm
    template_name = 'planification/session_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier - {self.object.course.label}'
        context['form_title'] = f'Modifier la séance du {self.object.date.strftime("%d/%m/%Y")}'
        context['submit_text'] = 'Enregistrer les modifications'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'La séance "{form.instance.course.label}" a été modifiée avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:session_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class CourseSessionDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une séance de cours"""
    model = CourseSession
    template_name = 'planification/session_confirm_delete.html'
    success_url = reverse_lazy('planification:sessions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Supprimer - {self.object.course.label}'

        # Vérifier s'il y a des liens avec des emplois du temps
        schedule_sessions = ScheduleSession.objects.filter(course_session=self.object)
        context['schedule_sessions'] = schedule_sessions
        context['has_schedule_links'] = schedule_sessions.exists()

        return context

    def delete(self, request, *args, **kwargs):
        session = self.get_object()

        # Vérifier s'il y a des liens avec des emplois du temps
        schedule_sessions = ScheduleSession.objects.filter(course_session=session)

        if schedule_sessions.exists():
            messages.error(
                request,
                f'Impossible de supprimer la séance "{session.course.label}" du {session.date.strftime("%d/%m/%Y")}. '
                f'Elle est liée à {schedule_sessions.count()} emploi(s) du temps. '
                f'Veuillez d\'abord supprimer ces liens.'
            )
            return redirect('planification:session_detail', pk=session.pk)

        messages.success(
            request,
            f'La séance "{session.course.label}" du {session.date.strftime("%d/%m/%Y")} a été supprimée avec succès.'
        )
        return super().delete(request, *args, **kwargs)


# ==================== CRUD VIEWS FOR CLASSROOMS ====================

@method_decorator(planning_admin_required, name='dispatch')
class ClassroomDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'une salle de classe"""
    model = Classroom
    template_name = 'planification/classroom_detail.html'
    context_object_name = 'classroom'
    pk_url_kwarg = 'code'

    def get_object(self):
        return get_object_or_404(Classroom, code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Détails - {self.object.name}'

        # Statistiques d'utilisation de la salle
        current_year = AcademicYear.objects.filter(is_active=True).first()
        if current_year:
            sessions = CourseSession.objects.filter(
                classroom=self.object,
                academic_year=current_year
            )
            context['usage_stats'] = {
                'total_sessions': sessions.count(),
                'scheduled_sessions': sessions.filter(status='scheduled').count(),
                'completed_sessions': sessions.filter(status='completed').count(),
                'cancelled_sessions': sessions.filter(status='cancelled').count(),
            }

            # Prochaines séances dans cette salle
            context['upcoming_sessions'] = sessions.filter(
                date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('date', 'time_slot__start_time')[:5]

        return context


@method_decorator(planning_admin_required, name='dispatch')
class ClassroomCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle salle de classe"""
    model = Classroom
    form_class = ClassroomForm
    template_name = 'planification/classroom_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter une salle'
        context['form_title'] = 'Nouvelle salle de classe'
        context['submit_text'] = 'Créer la salle'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'La salle "{form.instance.name}" a été créée avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:classroom_detail', kwargs={'code': self.object.code})


@method_decorator(planning_admin_required, name='dispatch')
class ClassroomUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une salle de classe"""
    model = Classroom
    form_class = ClassroomForm
    template_name = 'planification/classroom_form.html'
    pk_url_kwarg = 'code'

    def get_object(self):
        return get_object_or_404(Classroom, code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier - {self.object.name}'
        context['form_title'] = f'Modifier la salle {self.object.code}'
        context['submit_text'] = 'Enregistrer les modifications'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'La salle "{form.instance.name}" a été modifiée avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:classroom_detail', kwargs={'code': self.object.code})


@method_decorator(planning_admin_required, name='dispatch')
class ClassroomDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une salle de classe"""
    model = Classroom
    template_name = 'planification/classroom_confirm_delete.html'
    success_url = reverse_lazy('planification:classrooms')
    pk_url_kwarg = 'code'

    def get_object(self):
        return get_object_or_404(Classroom, code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Supprimer - {self.object.name}'

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(classroom=self.object).count()
        context['sessions_count'] = sessions_count
        context['has_sessions'] = sessions_count > 0

        return context

    def delete(self, request, *args, **kwargs):
        classroom = self.get_object()

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(classroom=classroom).count()
        if sessions_count > 0:
            messages.error(
                request,
                f'Impossible de supprimer la salle "{classroom.name}". '
                f'Elle est utilisée dans {sessions_count} séance(s) de cours. '
                f'Veuillez d\'abord supprimer ou modifier ces séances.'
            )
            return redirect('planification:classroom_detail', code=classroom.code)

        messages.success(
            request,
            f'La salle "{classroom.name}" a été supprimée avec succès.'
        )
        return super().delete(request, *args, **kwargs)


# ==================== CRUD VIEWS FOR LECTURERS ====================

@method_decorator(planning_admin_required, name='dispatch')
class LecturerDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'un enseignant"""
    model = Lecturer
    template_name = 'planification/lecturer_detail.html'
    context_object_name = 'lecturer'
    pk_url_kwarg = 'matricule'

    def get_object(self):
        return get_object_or_404(Lecturer, matricule=self.kwargs['matricule'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Détails - {self.object.firstname} {self.object.lastname}'

        # Statistiques d'enseignement
        current_year = AcademicYear.objects.filter(is_active=True).first()
        if current_year:
            sessions = CourseSession.objects.filter(
                lecturer=self.object,
                academic_year=current_year
            )
            context['teaching_stats'] = {
                'total_sessions': sessions.count(),
                'scheduled_sessions': sessions.filter(status='scheduled').count(),
                'completed_sessions': sessions.filter(status='completed').count(),
                'cancelled_sessions': sessions.filter(status='cancelled').count(),
            }

            # Prochaines séances de cet enseignant
            context['upcoming_sessions'] = sessions.filter(
                date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('date', 'time_slot__start_time')[:5]

            # Cours enseignés (distincts)
            context['courses_taught'] = sessions.values(
                'course__course_code', 'course__label', 'level__name'
            ).distinct().order_by('course__label')

        return context


@method_decorator(planning_admin_required, name='dispatch')
class LecturerCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel enseignant"""
    model = Lecturer
    form_class = LecturerForm
    template_name = 'planification/lecturer_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter un enseignant'
        context['form_title'] = 'Nouvel enseignant'
        context['submit_text'] = 'Créer l\'enseignant'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'L\'enseignant "{form.instance.firstname} {form.instance.lastname}" a été créé avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:lecturer_detail', kwargs={'matricule': self.object.matricule})


@method_decorator(planning_admin_required, name='dispatch')
class LecturerUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un enseignant"""
    model = Lecturer
    form_class = LecturerForm
    template_name = 'planification/lecturer_form.html'
    pk_url_kwarg = 'matricule'

    def get_object(self):
        return get_object_or_404(Lecturer, matricule=self.kwargs['matricule'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier - {self.object.firstname} {self.object.lastname}'
        context['form_title'] = f'Modifier l\'enseignant {self.object.matricule}'
        context['submit_text'] = 'Enregistrer les modifications'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'L\'enseignant "{form.instance.firstname} {form.instance.lastname}" a été modifié avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:lecturer_detail', kwargs={'matricule': self.object.matricule})


@method_decorator(planning_admin_required, name='dispatch')
class LecturerDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un enseignant"""
    model = Lecturer
    template_name = 'planification/lecturer_confirm_delete.html'
    success_url = reverse_lazy('planification:lecturers')
    pk_url_kwarg = 'matricule'

    def get_object(self):
        return get_object_or_404(Lecturer, matricule=self.kwargs['matricule'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Supprimer - {self.object.firstname} {self.object.lastname}'

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(lecturer=self.object).count()
        context['sessions_count'] = sessions_count
        context['has_sessions'] = sessions_count > 0

        # Récupérer quelques séances pour affichage
        if sessions_count > 0:
            context['recent_sessions'] = CourseSession.objects.filter(
                lecturer=self.object
            ).order_by('-date')[:3]

        return context

    def delete(self, request, *args, **kwargs):
        lecturer = self.get_object()

        # Vérifier s'il y a des séances associées
        sessions_count = CourseSession.objects.filter(lecturer=lecturer).count()
        if sessions_count > 0:
            messages.error(
                request,
                f'Impossible de supprimer l\'enseignant "{lecturer.firstname} {lecturer.lastname}". '
                f'Il/Elle est assigné(e) à {sessions_count} séance(s) de cours. '
                f'Veuillez d\'abord supprimer ou réassigner ces séances.'
            )
            return redirect('planification:lecturer_detail', matricule=lecturer.matricule)

        messages.success(
            request,
            f'L\'enseignant "{lecturer.firstname} {lecturer.lastname}" a été supprimé avec succès.'
        )
        return super().delete(request, *args, **kwargs)


# ==================== SCHEDULE VIEWS ====================

@method_decorator(planning_admin_required, name='dispatch')
class SchedulesView(LoginRequiredMixin, ListView):
    """Vue pour la liste des emplois du temps"""
    model = Schedule
    template_name = 'planification/schedules.html'
    context_object_name = 'schedules'
    paginate_by = 20

    def get_queryset(self):
        queryset = Schedule.objects.select_related(
            'academic_year', 'level'
        ).order_by('-created_at')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(level__name__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level_id=level)

        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Emplois du temps'

        # Données pour les filtres
        context['levels'] = Level.objects.all().order_by('name')
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')
        context['status_choices'] = Schedule.STATUS_CHOICES

        # Conserver les filtres dans le contexte
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'level': self.request.GET.get('level', ''),
            'academic_year': self.request.GET.get('academic_year', ''),
        }

        return context


@method_decorator(planning_admin_required, name='dispatch')
class ScheduleDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'un emploi du temps"""
    model = Schedule
    template_name = 'planification/schedule_detail.html'
    context_object_name = 'schedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Emploi du temps - {self.object.name}'

        # Statistiques de l'emploi du temps
        schedule_sessions = ScheduleSession.objects.filter(schedule=self.object)
        context['stats'] = {
            'total_sessions': schedule_sessions.count(),
            'total_weeks': self.object.get_duration_days() // 7,
            'courses_count': schedule_sessions.values('course_session__course').distinct().count(),
            'lecturers_count': schedule_sessions.values('course_session__lecturer').distinct().count(),
        }

        # Sessions par semaine
        sessions_by_week = {}
        for session in schedule_sessions.select_related(
            'course_session__course', 'course_session__lecturer',
            'course_session__classroom', 'course_session__time_slot'
        ).order_by('week_number', 'course_session__time_slot__day_of_week', 'course_session__time_slot__start_time'):
            week = session.week_number
            if week not in sessions_by_week:
                sessions_by_week[week] = []
            sessions_by_week[week].append(session)

        context['sessions_by_week'] = sessions_by_week

        return context


@method_decorator(planning_admin_required, name='dispatch')
class ScheduleCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouvel emploi du temps"""
    model = Schedule
    form_class = ScheduleForm
    template_name = 'planification/schedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Créer un emploi du temps'
        context['form_title'] = 'Nouvel emploi du temps'
        context['submit_text'] = 'Créer l\'emploi du temps'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'L\'emploi du temps "{form.instance.name}" a été créé avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:schedule_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un emploi du temps"""
    model = Schedule
    form_class = ScheduleForm
    template_name = 'planification/schedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier - {self.object.name}'
        context['form_title'] = f'Modifier l\'emploi du temps'
        context['submit_text'] = 'Enregistrer les modifications'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'L\'emploi du temps "{form.instance.name}" a été modifié avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:schedule_detail', kwargs={'pk': self.object.pk})


@method_decorator(planning_admin_required, name='dispatch')
class ScheduleGenerateView(LoginRequiredMixin, FormView):
    """Vue pour la génération automatique d'emploi du temps"""
    form_class = ScheduleGenerationForm
    template_name = 'planification/schedule_generate.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        level_id = self.request.GET.get('level')
        if level_id:
            try:
                kwargs['level'] = Level.objects.get(id=level_id)
            except Level.DoesNotExist:
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Générer un emploi du temps'
        context['form_title'] = 'Génération automatique d\'emploi du temps'
        context['submit_text'] = 'Générer l\'emploi du temps'
        return context

    def form_valid(self, form):
        schedule = form.cleaned_data['schedule']
        courses = form.cleaned_data['courses']
        sessions_per_week = form.cleaned_data['sessions_per_week']
        prefer_morning = form.cleaned_data['prefer_morning']
        avoid_consecutive_sessions = form.cleaned_data['avoid_consecutive_sessions']
        max_daily_sessions = form.cleaned_data['max_daily_sessions']

        # Créer le service de génération
        generator = ScheduleGenerationService(
            schedule=schedule,
            courses=courses,
            sessions_per_week=sessions_per_week,
            prefer_morning=prefer_morning,
            avoid_consecutive_sessions=avoid_consecutive_sessions,
            max_daily_sessions=max_daily_sessions
        )

        # Générer l'emploi du temps
        result = generator.generate_schedule()

        if result['success']:
            messages.success(self.request, result['message'])
            return redirect('planification:schedule_detail', pk=schedule.pk)
        else:
            messages.error(self.request, result['message'])
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('planification:schedules')


# ==================== LECTURER AVAILABILITY VIEWS ====================

@method_decorator(planning_admin_required, name='dispatch')
class LecturerAvailabilitiesView(LoginRequiredMixin, ListView):
    """Vue pour la liste des disponibilités des enseignants"""
    model = LecturerAvailability
    template_name = 'planification/lecturer_availabilities.html'
    context_object_name = 'availabilities'
    paginate_by = 20

    def get_queryset(self):
        queryset = LecturerAvailability.objects.select_related(
            'lecturer', 'time_slot', 'academic_year'
        ).order_by('lecturer__lastname', 'time_slot__day_of_week', 'time_slot__start_time')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(lecturer__firstname__icontains=search) |
                Q(lecturer__lastname__icontains=search) |
                Q(lecturer__matricule__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        lecturer = self.request.GET.get('lecturer')
        if lecturer:
            queryset = queryset.filter(lecturer_id=lecturer)

        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Disponibilités des enseignants'

        # Données pour les filtres
        context['lecturers'] = Lecturer.objects.all().order_by('lastname', 'firstname')
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')
        context['status_choices'] = LecturerAvailability.AVAILABILITY_STATUS

        # Conserver les filtres dans le contexte
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'lecturer': self.request.GET.get('lecturer', ''),
            'academic_year': self.request.GET.get('academic_year', ''),
        }

        return context


@method_decorator(planning_admin_required, name='dispatch')
class LecturerAvailabilityCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle disponibilité d'enseignant"""
    model = LecturerAvailability
    form_class = LecturerAvailabilityForm
    template_name = 'planification/lecturer_availability_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter une disponibilité'
        context['form_title'] = 'Nouvelle disponibilité d\'enseignant'
        context['submit_text'] = 'Enregistrer la disponibilité'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'La disponibilité pour {form.instance.lecturer} a été enregistrée avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('planification:lecturer_availabilities')
