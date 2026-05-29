from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from academic.models import Course
from lecturers.decorators import SESSION_LECTURER_ID, lecturer_required
from lecturers.models import Lecturer
from main.models import SystemSettings

from .forms import (
    CourseSelectionForm,
    DiplomaStep2Form,
    LecturerSubjectFormSet,
    ProfileStep1Form,
)
from .models import LecturerCourse


TOTAL_STEPS = 4

STEP_TITLES = {
    1: "Informations personnelles",
    2: "Diplôme et CV",
    3: "Matières que vous pouvez enseigner",
    4: "Cours proposés",
}
STEP_SUBTITLES = {
    1: "Renseignez vos informations personnelles et de contact.",
    2: "Indiquez votre plus haut diplôme et déposez votre CV.",
    3: "Choisissez vos matières et précisez votre expérience pour chacune.",
    4: "Sélectionnez parmi les cours auxquels vous êtes éligible.",
}


def _get_lecturer_or_logout(request):
    pk = request.session.get(SESSION_LECTURER_ID)
    if not pk:
        return None
    return Lecturer.objects.filter(pk=pk).first()


def _step_url(step):
    return reverse('recruitment:step', args=[step])


def _build_step_context(step, lecturer, **extra):
    context = {
        'lecturer': lecturer,
        'step': step,
        'total_steps': TOTAL_STEPS,
        'steps': [
            {
                'index': i,
                'title': STEP_TITLES[i],
                'reached': lecturer.recruitment_step >= i,
                'current': i == step,
                'accessible': i <= lecturer.recruitment_step + 1,
                'url': _step_url(i),
            }
            for i in range(1, TOTAL_STEPS + 1)
        ],
        'step_title': STEP_TITLES[step],
        'step_subtitle': STEP_SUBTITLES[step],
        'is_submitted': lecturer.recruitment_submitted,
    }
    context.update(extra)
    return context


def get_eligible_courses(lecturer):
    """Calcule les cours auxquels un enseignant peut postuler selon son diplôme
    et son expérience par matière, en se basant sur les seuils de SystemSettings."""

    diploma = lecturer.highest_diploma_obtained
    if not diploma:
        return Course.objects.none()

    settings_obj = SystemSettings.get_settings()
    lec_subjects = lecturer.lecturer_subjects.select_related('subject')
    by_subject = {ls.subject_id: (ls.practice_experience_years or 0) for ls in lec_subjects}
    if not by_subject:
        return Course.objects.none()

    threshold_lic = settings_obj.require_experience_for_licence_to_teach_licence or 0
    threshold_mas = settings_obj.require_experience_for_masters_to_teach_masters or 0
    threshold_doc = settings_obj.require_experience_for_doctors_to_teach_doctors or 0

    pairs = []  # (subject_id, cycle)
    for subj_id, years in by_subject.items():
        if diploma == 'Licence':
            if years >= threshold_lic:
                pairs.append((subj_id, 'Licence'))
        elif diploma == 'Master':
            pairs.append((subj_id, 'Licence'))
            if years >= threshold_mas:
                pairs.append((subj_id, 'Master'))
        elif diploma == 'Doctorat':
            pairs.append((subj_id, 'Licence'))
            pairs.append((subj_id, 'Master'))
            if years >= threshold_doc:
                pairs.append((subj_id, 'Doctorat'))

    if not pairs:
        return Course.objects.none()

    query = Q()
    for subj_id, cycle in pairs:
        query |= Q(subject_id=subj_id, level__cycle=cycle)
    return (
        Course.objects.filter(query)
        .select_related('subject', 'level', 'program', 'speciality')
        .order_by('subject__name', 'level__academic_order', 'label')
    )


@method_decorator([never_cache, csrf_protect, lecturer_required], name='dispatch')
class RecruitmentStepView(View):
    """Wizard de recrutement — dispatch sur ``step`` (1..4)."""

    template_name = 'recruitment/recruitment_step.html'

    def dispatch(self, request, step, *args, **kwargs):
        try:
            step = int(step)
        except (TypeError, ValueError):
            return redirect('recruitment:step', step=1)
        if step < 1 or step > TOTAL_STEPS:
            return redirect('recruitment:step', step=1)

        lecturer = _get_lecturer_or_logout(request)
        if not lecturer:
            return redirect('lecturers:logout')

        if lecturer.recruitment_submitted:
            return redirect('recruitment:recap')

        max_allowed = min(lecturer.recruitment_step + 1, TOTAL_STEPS)
        if step > max_allowed:
            messages.info(
                request,
                f"Veuillez d'abord compléter l'étape {max_allowed} avant de continuer.",
            )
            return redirect('recruitment:step', step=max_allowed)

        self.lecturer = lecturer
        return super().dispatch(request, step, *args, **kwargs)

    def get(self, request, step):
        handler = getattr(self, f'_render_step{step}')
        return handler(request)

    def post(self, request, step):
        handler = getattr(self, f'_handle_step{step}')
        return handler(request)

    def _mark_step_reached(self, step):
        if self.lecturer.recruitment_step < step:
            self.lecturer.recruitment_step = step
            self.lecturer.save(update_fields=['recruitment_step'])

    # ----------------------------------------------------------------- Step 1
    def _render_step1(self, request, form=None):
        if form is None:
            form = ProfileStep1Form(instance=self.lecturer)
        return render(request, self.template_name, _build_step_context(
            1, self.lecturer, form=form,
        ))

    def _handle_step1(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        form = ProfileStep1Form(
            request.POST, request.FILES,
            instance=self.lecturer, partial=partial,
        )
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step1(request, form=form)
        form.save()
        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('recruitment:step', step=1)
        self._mark_step_reached(1)
        return redirect('recruitment:step', step=2)

    # ----------------------------------------------------------------- Step 2
    def _render_step2(self, request, form=None):
        if form is None:
            form = DiplomaStep2Form(instance=self.lecturer)
        return render(request, self.template_name, _build_step_context(
            2, self.lecturer, form=form,
        ))

    def _handle_step2(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        form = DiplomaStep2Form(
            request.POST, request.FILES,
            instance=self.lecturer, partial=partial,
        )
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step2(request, form=form)
        form.save()
        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('recruitment:step', step=2)
        self._mark_step_reached(2)
        return redirect('recruitment:step', step=3)

    # ----------------------------------------------------------------- Step 3
    def _render_step3(self, request, formset=None):
        if formset is None:
            formset = LecturerSubjectFormSet(instance=self.lecturer)
        return render(request, self.template_name, _build_step_context(
            3, self.lecturer, formset=formset,
        ))

    def _handle_step3(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        formset = LecturerSubjectFormSet(request.POST, request.FILES, instance=self.lecturer)
        if not formset.is_valid():
            if partial and not any(formset.errors):
                # En mode brouillon on tolère l'absence de matière.
                pass
            else:
                messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
                return self._render_step3(request, formset=formset)
        with transaction.atomic():
            formset.save()
        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('recruitment:step', step=3)
        # On purge l'éventuelle sélection de cours obsolète (les matières ont pu changer).
        LecturerCourse.objects.filter(lecturer=self.lecturer).delete()
        self._mark_step_reached(3)
        return redirect('recruitment:step', step=4)

    # ----------------------------------------------------------------- Step 4
    def _render_step4(self, request, form=None, eligible=None, selected_ids=None):
        if eligible is None:
            eligible = get_eligible_courses(self.lecturer)
        if selected_ids is None:
            if form is not None and form.is_bound:
                # Course.pk est un CharField (course_code) → on garde des chaînes.
                selected_ids = set(form.data.getlist('courses'))
            else:
                selected_ids = set(
                    LecturerCourse.objects.filter(lecturer=self.lecturer)
                    .values_list('course_id', flat=True)
                )
        if form is None:
            form = CourseSelectionForm(
                initial={'courses': list(selected_ids)},
                eligible_courses=eligible,
            )
        ctx = _build_step_context(
            4, self.lecturer, form=form,
            eligible_courses=eligible,
            has_no_courses=not eligible.exists(),
            selected_course_ids=selected_ids,
        )
        return render(request, self.template_name, ctx)

    def _handle_step4(self, request):
        action = request.POST.get('save_action', 'next')
        eligible = get_eligible_courses(self.lecturer)
        form = CourseSelectionForm(request.POST, eligible_courses=eligible)
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step4(request, form=form, eligible=eligible)

        selected = form.cleaned_data['courses']
        with transaction.atomic():
            LecturerCourse.objects.filter(lecturer=self.lecturer).delete()
            LecturerCourse.objects.bulk_create([
                LecturerCourse(lecturer=self.lecturer, course=c) for c in selected
            ])
            self._mark_step_reached(4)
            if action != 'save_draft':
                self.lecturer.recruitment_submitted = True
                self.lecturer.recruitment_submitted_at = timezone.now()
                self.lecturer.status = 'pending'  # Passage en statut "En attente de validation" à la soumission
                self.lecturer.save(update_fields=[
                    'recruitment_submitted', 'recruitment_submitted_at', 'status'
                ])

        if action == 'save_draft':
            messages.success(request, "Brouillon enregistré.")
            return redirect('recruitment:step', step=4)
        messages.success(request, "Votre dossier de candidature a bien été soumis.")
        return redirect('recruitment:recap')


@method_decorator([never_cache, lecturer_required], name='dispatch')
class RecruitmentRecapView(View):
    template_name = 'recruitment/recap.html'

    def get(self, request):
        lecturer = _get_lecturer_or_logout(request)
        if not lecturer:
            return redirect('lecturers:logout')
        if not lecturer.recruitment_submitted:
            return redirect('recruitment:step', step=min(lecturer.recruitment_step + 1, TOTAL_STEPS))
        return render(request, self.template_name, {
            'lecturer': lecturer,
            'subjects': lecturer.lecturer_subjects.select_related('subject').all(),
            'courses': LecturerCourse.objects.filter(lecturer=lecturer)
                .select_related('course', 'course__subject', 'course__level').all(),
        })


