from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from academic.models import Course
from lecturers.emails import (
    send_recruitment_accepted_email,
    send_recruitment_refused_email,
)
from lecturers.forms import LecturerCreateForm, TeacherRecruitmentSettingsForm
from lecturers.models import Lecturer
from main.models import SystemSettings
from main.pdf_exports import build_lecturer_dossier_pdf
from recruitment.forms import (
    DiplomaStep2Form,
    LecturerSubjectFormSet,
    ProfileStep1Form,
)
from recruitment.models import LecturerCourse, LecturerRefusalReason, LecturerSubject



@never_cache
@login_required
def admin_dashboard(request):
    """Tableau de bord du recrutement des enseignants (côté administration).

    L'accès au module est contrôlé en amont par le middleware basé sur les
    modules accessibles. Ce tableau de bord sera étoffé ultérieurement.
    """
    submitted = Lecturer.objects.filter(recruitment_submitted=True)
    settings_obj = SystemSettings.get_settings()
    context = {
        'submitted_count': submitted.count(),
        'pending_courses_count': LecturerCourse.objects.filter(is_validated=False).count(),
        'recent_candidates': submitted.order_by('-recruitment_submitted_at')[:10],
        'teacher_recruitment_open': settings_obj.teacher_recruitment_open,
    }
    return render(request, 'lecturers/admin/admin_dashboard.html', context)


@never_cache
@login_required
def lecturer_settings(request):
    """Configuration des paramètres de recrutement des enseignants."""
    settings_obj = SystemSettings.get_settings()

    if request.method == 'POST':
        form = TeacherRecruitmentSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Les paramètres ont été enregistrés avec succès.")
            return redirect('lecturers:settings')
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = TeacherRecruitmentSettingsForm(instance=settings_obj)

    return render(request, 'lecturers/admin/settings.html', {'form': form})


def _filter_lecturer_dossiers(params):
    """Construit le queryset des dossiers enseignants à partir des filtres GET."""
    lecturers = Lecturer.objects.all()

    status = params.get('status')
    gender = params.get('gender')
    diploma = params.get('diploma')
    is_permanent = params.get('is_permanent')
    search = (params.get('search') or '').strip()

    if status:
        lecturers = lecturers.filter(status=status)
    if gender:
        lecturers = lecturers.filter(gender=gender)
    if diploma:
        lecturers = lecturers.filter(highest_diploma_obtained=diploma)
    if is_permanent in ('True', 'False'):
        lecturers = lecturers.filter(is_permanent=(is_permanent == 'True'))
    if search:
        lecturers = lecturers.filter(
            Q(matricule__icontains=search)
            | Q(firstname__icontains=search)
            | Q(lastname__icontains=search)
            | Q(email__icontains=search)
        )

    return lecturers.order_by('lastname', 'firstname')


@never_cache
@login_required
def lecturer_dossiers(request):
    """Liste les dossiers des enseignants avec filtres et pagination."""
    lecturers = _filter_lecturer_dossiers(request.GET)
    filtered_count = lecturers.count()

    per_page_choices = [5, 10, 25, 50, 100]
    try:
        per_page = int(request.GET.get('per_page', 10))
    except (TypeError, ValueError):
        per_page = 10
    if per_page not in per_page_choices:
        per_page = 10

    paginator = Paginator(lecturers, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    has_filter = any(
        value for key, value in request.GET.items()
        if key not in ('page', 'per_page')
    )

    context = {
        'lecturers': page_obj.object_list,
        'filtered_count': filtered_count,
        'page_obj': page_obj,
        'has_filter': has_filter,
        'per_page': per_page,
        'per_page_choices': per_page_choices,
        'status_choices': Lecturer.LECTURERS_STATUS_CHOICES,
        'diploma_choices': Lecturer.DIPLOMAS_CHOICES,
    }
    return render(request, 'lecturers/admin/dossiers.html', context)


@never_cache
@login_required
def lecturer_dossier_create(request):
    """Crée un enseignant directement depuis l'administration, puis redirige
    vers l'édition complète de son dossier (utile pour les enseignants déjà
    recrutés avant la mise en place du système)."""
    if request.method == 'POST':
        form = LecturerCreateForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            messages.success(
                request,
                f"L'enseignant {lecturer.full_name()} a été créé. "
                "Vous pouvez maintenant compléter son dossier.",
            )
            return redirect('lecturers:dossier_edit', matricule=lecturer.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = LecturerCreateForm()

    return render(request, 'lecturers/admin/dossier_create.html', {'form': form})


@never_cache
@login_required
def lecturer_dossier_detail(request, matricule):
    """Affiche le dossier détaillé d'un enseignant."""
    lecturer = get_object_or_404(
        Lecturer.objects.prefetch_related(
            'lecturer_subjects__subject',
            'lecturer_courses__course__level',
        ),
        pk=matricule,
    )

    context = {
        'lecturer': lecturer,
        'lecturer_subjects': lecturer.lecturer_subjects.all(),
        'lecturer_courses': lecturer.lecturer_courses.all(),
    }
    return render(request, 'lecturers/admin/dossier_detail.html', context)


def _sync_lecturer_courses(lecturer, selected_course_codes):
    """Synchronise les cours d'un enseignant et garantit l'invariant métier :
    la matière de chaque cours sélectionné fait toujours partie des matières
    de l'enseignant (créée automatiquement si nécessaire)."""
    selected_courses = list(
        Course.objects.filter(pk__in=selected_course_codes).select_related('subject')
    )

    existing_subject_ids = set(
        lecturer.lecturer_subjects.values_list('subject_id', flat=True)
    )
    for course in selected_courses:
        if course.subject_id and course.subject_id not in existing_subject_ids:
            LecturerSubject.objects.get_or_create(
                lecturer=lecturer, subject_id=course.subject_id
            )
            existing_subject_ids.add(course.subject_id)

    existing = {lc.course_id: lc for lc in lecturer.lecturer_courses.all()}
    selected_ids = {course.pk for course in selected_courses}
    for course_id, lc in existing.items():
        if course_id not in selected_ids:
            lc.delete()
    for course in selected_courses:
        if course.pk not in existing:
            LecturerCourse.objects.create(lecturer=lecturer, course=course)


@never_cache
@login_required
def lecturer_dossier_edit(request, matricule):
    """Permet de modifier le dossier complet d'un enseignant : informations
    personnelles, diplôme, matières et cours proposés."""
    lecturer = get_object_or_404(
        Lecturer.objects.prefetch_related(
            'lecturer_subjects__subject',
            'lecturer_courses__course',
        ),
        pk=matricule,
    )

    if request.method == 'POST':
        profile_form = ProfileStep1Form(
            request.POST, request.FILES, instance=lecturer, partial=True,
        )
        diploma_form = DiplomaStep2Form(
            request.POST, request.FILES, instance=lecturer, partial=True,
        )
        subject_formset = LecturerSubjectFormSet(
            request.POST, request.FILES, instance=lecturer,
        )
        selected_course_codes = set(request.POST.getlist('courses'))

        forms_valid = all([
            profile_form.is_valid(),
            diploma_form.is_valid(),
            subject_formset.is_valid(),
        ])
        if forms_valid:
            with transaction.atomic():
                profile_form.save()
                diploma_form.save()
                subject_formset.save()
                _sync_lecturer_courses(lecturer, selected_course_codes)
            messages.success(
                request,
                f"Le dossier de {lecturer.full_name()} a été mis à jour avec succès.",
            )
            if 'save_and_continue' in request.POST:
                return redirect('lecturers:dossier_edit', matricule=lecturer.pk)
            return redirect('lecturers:dossier_detail', matricule=lecturer.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        profile_form = ProfileStep1Form(instance=lecturer, partial=True)
        diploma_form = DiplomaStep2Form(instance=lecturer, partial=True)
        subject_formset = LecturerSubjectFormSet(instance=lecturer)
        selected_course_codes = set(
            lecturer.lecturer_courses.values_list('course_id', flat=True)
        )

    all_courses = (
        Course.objects.select_related('subject', 'level')
        .order_by('subject__name', 'level__academic_order', 'label')
    )

    context = {
        'lecturer': lecturer,
        'profile_form': profile_form,
        'diploma_form': diploma_form,
        'subject_formset': subject_formset,
        'all_courses': all_courses,
        'selected_course_codes': selected_course_codes,
    }
    return render(request, 'lecturers/admin/dossier_edit.html', context)


@never_cache
@login_required
def lecturer_dossier_pdf(request, matricule):
    """Génère le dossier complet d'un enseignant au format PDF."""
    lecturer = get_object_or_404(
        Lecturer.objects.prefetch_related(
            'lecturer_subjects__subject',
            'lecturer_courses__course__level',
            'refusal_reasons__created_by',
        ),
        pk=matricule,
    )

    pdf_content = build_lecturer_dossier_pdf(lecturer, request=request)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="dossier_{lecturer.matricule}.pdf"'
    return response


@never_cache
@login_required
def lecturer_dossier_process(request, matricule):
    """Traite le dossier d'un enseignant : validation ou refus de la candidature."""
    lecturer = get_object_or_404(
        Lecturer.objects.prefetch_related(
            'lecturer_subjects__subject',
            'lecturer_courses__course__level',
            'refusal_reasons',
        ),
        pk=matricule,
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            return _process_accept(request, lecturer)
        if action == 'refuse':
            return _process_refuse(request, lecturer)
        if action == 'save_progress':
            return _process_save_progress(request, lecturer)

        messages.error(request, "Action inconnue.")
        return redirect('lecturers:dossier_process', matricule=matricule)

    context = {
        'lecturer': lecturer,
        'lecturer_subjects': lecturer.lecturer_subjects.all(),
        'lecturer_courses': lecturer.lecturer_courses.all(),
        'refusal_reasons': lecturer.refusal_reasons.all(),
    }
    return render(request, 'lecturers/admin/dossier_process.html', context)


def _apply_validation_selection(request, lecturer):
    """Met à jour l'état de validation des matières/cours selon les cases cochées."""
    validated_subject_ids = set(request.POST.getlist('validated_subjects'))
    validated_course_ids = set(request.POST.getlist('validated_courses'))
    now = timezone.now()

    for ls in lecturer.lecturer_subjects.all():
        should_validate = str(ls.pk) in validated_subject_ids
        ls.is_validated = should_validate
        ls.validated_by = request.user if should_validate else None
        ls.validated_at = now if should_validate else None
        ls.save(update_fields=['is_validated', 'validated_by', 'validated_at'])

    for lc in lecturer.lecturer_courses.all():
        should_validate = str(lc.pk) in validated_course_ids
        lc.is_validated = should_validate
        lc.validated_by = request.user if should_validate else None
        lc.validated_at = now if should_validate else None
        lc.save(update_fields=['is_validated', 'validated_by', 'validated_at'])


def _process_save_progress(request, lecturer):
    """Enregistre l'avancement de la validation sans accepter ni refuser le dossier.

    Permet à l'administration de reprendre le traitement du dossier plus tard.
    """
    with transaction.atomic():
        _apply_validation_selection(request, lecturer)

    messages.success(
        request,
        "L'avancement du traitement a été enregistré. Vous pourrez reprendre le "
        "traitement de ce dossier plus tard.",
    )
    return redirect('lecturers:dossier_process', matricule=lecturer.pk)


def _process_accept(request, lecturer):
    """Valide les matières/cours sélectionnés et marque le dossier comme recruté."""
    with transaction.atomic():
        _apply_validation_selection(request, lecturer)

        lecturer.status = 'hired'
        lecturer.can_be_resubmitted = False
        lecturer.save(update_fields=['status', 'can_be_resubmitted'])

    send_recruitment_accepted_email(lecturer, request=request)
    messages.success(
        request,
        f"Le dossier de {lecturer.full_name()} a été accepté. Un email de "
        "confirmation a été envoyé à l'enseignant.",
    )
    return redirect('lecturers:dossier_detail', matricule=lecturer.pk)


def _process_refuse(request, lecturer):
    """Enregistre un motif de refus et notifie l'enseignant."""
    reason = (request.POST.get('reason') or '').strip()
    can_be_resubmitted = request.POST.get('can_be_resubmitted') == 'on'

    if not reason:
        messages.error(request, "Veuillez préciser le motif du refus.")
        return redirect('lecturers:dossier_process', matricule=lecturer.pk)

    with transaction.atomic():
        LecturerRefusalReason.objects.create(
            lecturer=lecturer,
            reason=reason,
            can_be_resubmitted=can_be_resubmitted,
            created_by=request.user,
        )
        lecturer.status = 'refused'
        lecturer.can_be_resubmitted = can_be_resubmitted
        lecturer.save(update_fields=['status', 'can_be_resubmitted'])

    send_recruitment_refused_email(
        lecturer, reason, can_be_resubmitted=can_be_resubmitted, request=request,
    )
    messages.success(
        request,
        f"Le dossier de {lecturer.full_name()} a été refusé. Un email a été "
        "envoyé à l'enseignant.",
    )
    return redirect('lecturers:dossier_detail', matricule=lecturer.pk)
