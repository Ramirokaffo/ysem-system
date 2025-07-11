from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from students.models import Student, OfficialDocument
from django.core.paginator import Paginator


@never_cache
@csrf_protect
def student_login(request):
    """
    Vue de connexion pour les étudiants (accès externe)
    """
    # Si l'étudiant est déjà connecté, rediriger vers le dashboard
    if request.session.get('student_authenticated'):
        return redirect('student_portal:dashboard')

    if request.method == 'POST':
        matricule = request.POST.get('matricule')
        password = request.POST.get('password')

        if matricule and password:
            try:
                student = Student.objects.get(matricule=matricule)

                # Vérifier si l'étudiant a un mot de passe externe configuré
                if not student.has_external_password():
                    messages.error(request, 'Accès non configuré. Veuillez contacter la scolarité.')
                    return render(request, 'student_portal/login.html')

                # Vérifier le mot de passe
                if student.check_external_password(password):
                    # Authentification réussie - créer une session spéciale
                    request.session['student_authenticated'] = True
                    request.session['student_matricule'] = student.matricule
                    request.session['student_name'] = f"{student.firstname} {student.lastname}"

                    # Rediriger vers le dashboard étudiant
                    return redirect('student_portal:dashboard')
                else:
                    messages.error(request, 'Matricule ou mot de passe incorrect.')
            except Student.DoesNotExist:
                messages.error(request, 'Matricule ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    return render(request, 'student_portal/login.html')


def student_logout(request):
    """
    Vue de déconnexion pour les étudiants
    """
    # Supprimer les données de session de l'étudiant
    if 'student_authenticated' in request.session:
        del request.session['student_authenticated']
    if 'student_matricule' in request.session:
        del request.session['student_matricule']
    if 'student_name' in request.session:
        del request.session['student_name']

    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('student_portal:login')


def student_required(view_func):
    """
    Décorateur pour vérifier que l'étudiant est authentifié
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('student_authenticated'):
            messages.error(request, 'Vous devez vous connecter pour accéder à cette page.')
            return redirect('student_portal:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def student_dashboard(request):
    """
    Dashboard principal pour les étudiants connectés
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)

    # Récupération des niveaux de l'étudiant avec leurs documents
    student_levels = student.student_levels.all().order_by('-academic_year__start_at', 'level__name')

    # Statistiques des documents
    total_documents = 0
    available_documents = 0
    withdrawn_documents = 0
    lost_documents = 0

    for level in student_levels:
        docs = level.official_documents.all()
        total_documents += docs.count()
        available_documents += docs.filter(status='available').count()
        withdrawn_documents += docs.filter(status='withdrawn').count()
        lost_documents += docs.filter(status='lost').count()

    context = {
        'student': student,
        'student_levels': student_levels,
        'document_stats': {
            'total': total_documents,
            'available': available_documents,
            'withdrawn': withdrawn_documents,
            'lost': lost_documents
        }
    }

    return render(request, 'student_portal/dashboard.html', context)


@student_required
def student_documents(request):
    """
    Vue pour afficher tous les documents de l'étudiant avec pagination et filtres
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)

    # Récupération des documents avec filtres
    documents = OfficialDocument.objects.filter(
        student_level__student=student
    ).select_related(
        'student_level__level',
        'student_level__academic_year'
    ).order_by('-student_level__academic_year__start_at', 'type')

    # Filtres
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    year_filter = request.GET.get('year')

    if status_filter:
        documents = documents.filter(status=status_filter)
    if type_filter:
        documents = documents.filter(type=type_filter)
    if year_filter:
        documents = documents.filter(student_level__academic_year_id=year_filter)

    # Pagination
    per_page = request.GET.get('per_page', 10)
    page = request.GET.get('page', 1)

    paginator = Paginator(documents, per_page)
    page_obj = paginator.get_page(page)

    # Données pour les filtres
    from academic.models import AcademicYear
    academic_years = AcademicYear.objects.filter(
        student_levels__student=student
    ).distinct().order_by('-start_at')

    document_types = OfficialDocument.objects.filter(
        student_level__student=student
    ).values_list('type', flat=True).distinct()

    context = {
        'student': student,
        'documents': page_obj.object_list,
        'page_obj': page_obj,
        'academic_years': academic_years,
        'document_types': document_types,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'year_filter': year_filter,
        'per_page': int(per_page),
        'per_page_choices': [5, 10, 25, 50]
    }

    return render(request, 'student_portal/documents.html', context)


def permission_denied_view(request, exception=None):
    """
    Vue personnalisée pour les erreurs 403 dans le portail étudiant
    """
    return render(request, 'student_portal/403.html', status=403)
