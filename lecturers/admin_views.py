from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from lecturers.models import Lecturer
from recruitment.models import LecturerCourse



@never_cache
@login_required
def admin_dashboard(request):
    """Tableau de bord du recrutement des enseignants (côté administration).

    L'accès au module est contrôlé en amont par le middleware basé sur les
    modules accessibles. Ce tableau de bord sera étoffé ultérieurement.
    """
    submitted = Lecturer.objects.filter(recruitment_submitted=True)
    context = {
        'submitted_count': submitted.count(),
        'pending_courses_count': LecturerCourse.objects.filter(is_validated=False).count(),
        'recent_candidates': submitted.order_by('-recruitment_submitted_at')[:10],
    }
    return render(request, 'lecturers/admin/admin_dashboard.html', context)


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
