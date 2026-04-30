import re

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse, JsonResponse
from students.models import Student, OfficialDocument
from django.core.paginator import Paginator

from main.pdf_exports import build_payment_receipt_pdf, build_registration_certificate_pdf
from payments.models import Payment
from payments.utils import build_student_financial_statement
from academic.models import AcademicYear


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
                    # request.session['student_must_change_password'] = student.must_change_password
                    request.session['student_matricule'] = student.matricule
                    request.session['student_name'] = f"{student.firstname} {student.lastname}"
                    student.last_login_date = timezone.now()
                    student.save(update_fields=['last_login_date'])

                    # Si le mot de passe a été généré ou réinitialisé par la
                    # scolarité, forcer l'étudiant à le changer dès la connexion
                    if student.must_change_password:
                        messages.info(
                            request,
                            "Pour des raisons de sécurité, vous devez définir un "
                            "nouveau mot de passe avant de continuer."
                        )
                        return redirect('student_portal:change_password')

                    # Rediriger vers le dashboard étudiant
                    messages.success(request, f'Bienvenue {student.firstname} ! Vous êtes connecté avec succès.')
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
    # if 'student_must_change_password' in request.session:
    #     del request.session['student_must_change_password']

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

    active_year = AcademicYear.get_active_year()
    financial_summary = build_student_financial_statement(student, active_year) if active_year else None

    context = {
        'student': student,
        'student_levels': student_levels,
        'document_stats': {
            'total': total_documents,
            'available': available_documents,
            'withdrawn': withdrawn_documents,
            'lost': lost_documents
        },
        'financial_summary': financial_summary,
        'active_academic_year': active_year,
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

    # Annoter chaque certificat d'inscription affiché avec son autorisation de téléchargement
    download_check_cache = {}
    for document in page_obj.object_list:
        if document.type != OfficialDocument.TYPE_REGISTRATION_CERTIFICATE:
            continue
        academic_year = document.student_level.academic_year
        cache_key = academic_year.pk if academic_year else None
        if cache_key not in download_check_cache:
            download_check_cache[cache_key] = student.can_withdraw_documents(academic_year)
        can_download, reason = download_check_cache[cache_key]
        document.download_allowed = can_download
        document.download_block_reason = '' if can_download else reason

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


@student_required
def registration_certificate_download(request, pk):
    """
    Permet à l'étudiant connecté de télécharger son certificat d'inscription.
    Le téléchargement est bloqué tant que la situation financière n'est pas régularisée.
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)

    document = get_object_or_404(
        OfficialDocument.objects.select_related(
            'student_level__student__program',
            'student_level__level',
            'student_level__academic_year',
        ),
        pk=pk,
        type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
        student_level__student=student,
    )

    can_download, reason = student.can_withdraw_documents(
        document.student_level.academic_year
    )
    if not can_download:
        messages.error(
            request,
            f"Téléchargement indisponible : {reason}. "
            "Veuillez régulariser votre situation financière auprès de la scolarité."
        )
        return redirect('student_portal:documents')

    pdf_content = build_registration_certificate_pdf(document)
    filename_reference = re.sub(
        r'[^A-Za-z0-9_-]+',
        '_',
        document.reference or f'certificat_inscription_{student.matricule}',
    ).strip('_')

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_inscription_{filename_reference}.pdf"'
    return response


@student_required
def student_finances(request):
    """
    Vue de la situation financière complète de l'étudiant pour une année académique donnée.
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)

    academic_years = list(
        AcademicYear.objects.filter(
            payments__student=student,
        ).distinct().order_by('-start_at')
    )
    student_year_ids = set(
        student.student_levels.values_list('academic_year_id', flat=True)
    )
    for year in AcademicYear.objects.filter(pk__in=student_year_ids).order_by('-start_at'):
        if year not in academic_years:
            academic_years.append(year)

    selected_academic_year = None
    requested_year_id = request.GET.get('academic_year')
    if requested_year_id:
        selected_academic_year = AcademicYear.objects.filter(pk=requested_year_id).first()
    if not selected_academic_year:
        selected_academic_year = (
            AcademicYear.get_active_year()
            or (academic_years[0] if academic_years else None)
        )

    statement = (
        build_student_financial_statement(student, selected_academic_year)
        if selected_academic_year else None
    )

    context = {
        'student': student,
        'selected_academic_year': selected_academic_year,
        'academic_years': academic_years,
        'statement': statement,
        'generated_on': timezone.localtime(),
    }
    return render(request, 'student_portal/finances.html', context)


@student_required
def student_payment_receipt_download(request, pk):
    """
    Permet à l'étudiant connecté de télécharger le reçu PDF d'un de ses paiements.
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)

    payment = get_object_or_404(
        Payment.objects.select_related(
            'student', 'student__program', 'installment', 'academic_year', 'author'
        ),
        pk=pk,
        student=student,
    )

    pdf_content = build_payment_receipt_pdf(payment, request=request)
    reference = payment.transaction_id or payment.group_reference or str(payment.pk)
    filename_reference = re.sub(r'[^A-Za-z0-9_-]+', '_', reference).strip('_')

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_paiement_{filename_reference}.pdf"'
    return response


@never_cache
@csrf_protect
@student_required
def student_change_password(request):
    """
    Permet à l'étudiant connecté de modifier son mot de passe.
    Cette vue est utilisée à la fois pour le changement obligatoire à la
    première connexion (ou après réinitialisation par la scolarité) et pour
    une modification volontaire depuis le portail étudiant.
    """
    matricule = request.session.get('student_matricule')
    student = get_object_or_404(Student, matricule=matricule)
    forced = student.must_change_password

    if request.method == 'POST':
        current_password = request.POST.get('current_password') or ''
        new_password = request.POST.get('new_password') or ''
        confirm_password = request.POST.get('confirm_password') or ''

        errors = []

        if not student.check_external_password(current_password):
            errors.append("Le mot de passe actuel est incorrect.")

        if not new_password or not confirm_password:
            errors.append("Veuillez remplir tous les champs.")
        elif new_password != confirm_password:
            errors.append("Le nouveau mot de passe et sa confirmation ne correspondent pas.")
        elif new_password == current_password:
            errors.append("Le nouveau mot de passe doit être différent de l'ancien.")
        else:
            try:
                validate_password(new_password)
            except ValidationError as exc:
                errors.extend(exc.messages)

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            student.set_external_password(new_password)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
            return redirect('student_portal:dashboard')

    context = {
        'student': student,
        'forced': forced,
    }
    return render(request, 'student_portal/change_password.html', context)


def permission_denied_view(request, exception=None):
    """
    Vue personnalisée pour les erreurs 403 dans le portail étudiant
    """
    return render(request, 'student_portal/403.html', status=403)
