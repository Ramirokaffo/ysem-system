from django.contrib.auth.decorators import login_required
from django.shortcuts import render
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
