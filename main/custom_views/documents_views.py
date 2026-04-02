import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from main.forms import BulkDocumentCreationForm, OfficialDocumentForm
from main.pdf_exports import build_registration_certificate_pdf
from students.models import Student
from academic.models import AcademicYear, Level
from students.models import OfficialDocument, StudentLevel


class DocumentsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des documents"""
    template_name = 'main/documents/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Documents officiels'
        documents = OfficialDocument.objects.select_related('student_level__student').all()
        levels = Level.objects.all()
        academic_years = AcademicYear.objects.all().order_by('-start_at')

        document_type = self.request.GET.get('document_type')
        status = self.request.GET.get('status')
        level_id = self.request.GET.get('level')
        academic_year_id = self.request.GET.get('academic_year')
        student_id = self.request.GET.get('student')
        student_search = (self.request.GET.get('student_search') or '').strip()
        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)
        selected_student = None

        # Utiliser l'année active par défaut si aucun filtre n'est fourni
        selected_academic_year = None
        if academic_year_id:
            selected_academic_year = AcademicYear.objects.filter(pk=academic_year_id).first()
        else:
            selected_academic_year = AcademicYear.get_active_year()

        if student_id:
            selected_student = Student.objects.select_related('program').filter(
                pk=student_id,
                student_levels__academic_year__isnull=False,
                status='registered',
            ).distinct().first()

        if document_type:
            documents = documents.filter(type=document_type)
        if status:
            documents = documents.filter(status=status)
        if level_id:
            documents = documents.filter(student_level__level_id=level_id)
        if selected_academic_year:
            documents = documents.filter(student_level__academic_year=selected_academic_year)
        if student_id:
            documents = documents.filter(student_level__student_id=student_id)

        paginator = Paginator(documents, per_page)
        page_obj = paginator.get_page(page)

        context['documents'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['levels'] = levels
        context['academic_years'] = academic_years
        context['selected_academic_year'] = selected_academic_year
        context['selected_student'] = selected_student
        context['selected_student_label'] = (
            OfficialDocumentForm.get_student_label(selected_student)
            if selected_student else student_search
        )
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        return context


@login_required
def registration_certificate_download(request, pk):
    """Génère à la demande le PDF d'un certificat d'inscription."""
    document = get_object_or_404(
        OfficialDocument.objects.select_related(
            'student_level__student__program',
            'student_level__level',
            'student_level__academic_year',
        ),
        pk=pk,
        type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
    )

    pdf_content = build_registration_certificate_pdf(document)
    filename_reference = re.sub(
        r'[^A-Za-z0-9_-]+',
        '_',
        document.reference or f'certificat_inscription_{document.student_level.student.matricule}',
    ).strip('_')

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificat_inscription_{filename_reference}.pdf"'
    return response


@login_required
def document_student_search(request):
    """Endpoint JSON pour l'autocomplete étudiant du formulaire de document."""
    query = (request.GET.get('q') or '').strip()

    if not query:
        return JsonResponse({'results': []})

    students = Student.objects.select_related('program').filter(
        student_levels__academic_year__isnull=False,
        status='registered'
    ).filter(
        Q(matricule__icontains=query)
        | Q(firstname__icontains=query)
        | Q(lastname__icontains=query)
        | Q(program__name__icontains=query)
    ).distinct().order_by('matricule')[:10]

    results = [
        {
            'id': student.pk,
            'text': OfficialDocumentForm.get_student_label(student),
            'matricule': student.matricule,
            'firstname': student.firstname,
            'lastname': student.lastname,
            'program_name': student.program.name if student.program_id else '',
        }
        for student in students
    ]
    return JsonResponse({'results': results})


@login_required
def document_student_levels(request):
    """Retourne les niveaux disponibles pour l'étudiant sélectionné."""
    student_id = request.GET.get('student_id')

    if not student_id:
        return JsonResponse({'levels': [], 'message': "Sélectionnez d'abord un étudiant."})

    student_levels = StudentLevel.objects.select_related('level', 'academic_year').filter(
        student_id=student_id,
    ).order_by('-is_active', 'level__academic_order', 'level__name', '-academic_year__start_at')

    levels = []
    seen_level_ids = set()
    for student_level in student_levels:
        if not student_level.level_id or student_level.level_id in seen_level_ids:
            continue
        seen_level_ids.add(student_level.level_id)
        levels.append({
            'id': student_level.level_id,
            'label': student_level.level.name,
        })

    message = 'Sélectionnez le niveau associé à cet étudiant.' if levels else 'Aucun niveau associé à cet étudiant.'
    return JsonResponse({'levels': levels, 'message': message})


@login_required
def document_student_academic_years(request):
    """Retourne les années académiques disponibles pour un étudiant et un niveau."""
    student_id = request.GET.get('student_id')
    level_id = request.GET.get('level_id')

    if not student_id or not level_id:
        return JsonResponse({'academic_years': [], 'message': "Sélectionnez d'abord un niveau."})

    student_levels = StudentLevel.objects.select_related('academic_year').filter(
        student_id=student_id,
        level_id=level_id,
        academic_year__isnull=False,
    ).order_by('-academic_year__start_at')

    academic_years = []
    seen_academic_year_ids = set()
    for student_level in student_levels:
        if not student_level.academic_year_id or student_level.academic_year_id in seen_academic_year_ids:
            continue
        seen_academic_year_ids.add(student_level.academic_year_id)
        academic_years.append({
            'id': student_level.academic_year_id,
            'label': student_level.academic_year.name,
        })

    if len(academic_years) == 1:
        message = "L'unique année académique disponible a été sélectionnée automatiquement."
    elif academic_years:
        message = "Sélectionnez l'année académique liée à ce niveau."
    else:
        message = 'Aucune année académique associée à ce niveau pour cet étudiant.'

    return JsonResponse({'academic_years': academic_years, 'message': message})

@login_required
def document_create(request):
    """
    Vue pour créer un nouveau document officiel
    """
    if request.method == 'POST':
        form = OfficialDocumentForm(request.POST)
        if form.is_valid():
            document = form.save()
            messages.success(request, f'Le document "{document.get_type_display()}" a été créé avec succès.')
            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = OfficialDocumentForm()

    context = {
        'form': form,
        'page_title': 'Créer un document officiel',
        'action': 'create'
    }
    return render(request, 'main/documents/document_form.html', context)


@login_required
def document_edit(request, pk):
    """
    Vue pour modifier un document officiel existant
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        form = OfficialDocumentForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save()
            messages.success(request, f'Le document "{document.get_type_display()}" a été modifié avec succès.')
            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = OfficialDocumentForm(instance=document)

    context = {
        'form': form,
        'document': document,
        'page_title': f'Modifier le document - {document.get_type_display()}',
        'action': 'edit'
    }
    return render(request, 'main/documents/document_form.html', context)


@login_required
def document_delete(request, pk):
    """
    Vue pour supprimer un document officiel
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        document_type = document.get_type_display()
        document.delete()
        messages.success(request, f'Le document "{document_type}" a été supprimé avec succès.')
        return redirect('main:documents')

    context = {
        'document': document,
        'page_title': f'Supprimer le document - {document.get_type_display()}'
    }
    return render(request, 'main/documents/document_delete.html', context)


@login_required
def document_toggle_status(request, pk):
    """
    Vue pour marquer un document comme déchargé/retourné
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        if document.status == 'available':
            # Vérifier le statut de paiement avant de permettre la décharge
            can_withdraw, reason = document.student_level.student.can_withdraw_documents(
                document.student_level.academic_year
            )

            if not can_withdraw:
                messages.error(
                    request,
                    f'Impossible de décharger le document : {reason}'
                )
                return redirect('main:documents')

            # Marquer comme déchargé
            document.status = 'withdrawn'
            document.withdrawn_date = timezone.now().date()
            action_message = 'déchargé'
        elif document.status == 'withdrawn':
            # Marquer comme retourné
            document.status = 'returned'
            document.returned_at = timezone.now().date()
            action_message = 'retourné'
        elif document.status == 'returned':
            # Remettre comme déchargé (pour correction d'erreur)
            document.status = 'withdrawn'
            document.returned_at = None
            action_message = 'remis en statut déchargé'
        else:
            # Pour les documents perdus, on peut les remettre disponibles
            document.status = 'available'
            document.withdrawn_date = None
            document.returned_at = None
            action_message = 'remis disponible'

        document.save()
        messages.success(request, f'Le document "{document.get_type_display()}" a été {action_message} avec succès.')
        return redirect('main:documents')

    # Déterminer l'action qui sera effectuée
    if document.status == 'available':
        action = 'décharger'
        action_description = 'marquer ce document comme déchargé'

        # Vérifier le statut de paiement pour l'affichage
        can_withdraw, reason = document.student_level.student.can_withdraw_documents(
            document.student_level.academic_year
        )
        payment_warning = None if can_withdraw else reason
    elif document.status == 'withdrawn':
        action = 'retourner'
        action_description = 'marquer ce document comme retourné'
        payment_warning = None
    elif document.status == 'returned':
        action = 'remettre en déchargé'
        action_description = 'remettre ce document en statut déchargé (correction d\'erreur)'
        payment_warning = None
    else:
        action = 'remettre disponible'
        action_description = 'remettre ce document disponible'
        payment_warning = None

    context = {
        'document': document,
        'action': action,
        'action_description': action_description,
        'payment_warning': payment_warning,
        'page_title': f'{action.capitalize()} le document - {document.get_type_display()}'
    }
    return render(request, 'main/documents/document_toggle_status.html', context)


@login_required
def document_bulk_create(request):
    """
    Vue pour la création en masse de documents officiels
    """
    if request.method == 'POST':
        form = BulkDocumentCreationForm(request.POST)
        if form.is_valid():
            # Créer les documents
            created_count, skipped_count, errors = form.create_documents()

            if created_count > 0:
                messages.success(
                    request,
                    f'{created_count} document(s) créé(s) avec succès. '
                    f'{skipped_count} document(s) ignoré(s) (déjà existants).'
                )

            if errors:
                for error in errors[:5]:  # Limiter à 5 erreurs pour l'affichage
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.warning(request, f'... et {len(errors) - 5} autres erreurs.')

            if created_count == 0 and skipped_count == 0:
                messages.warning(request, 'Aucun document créé. Vérifiez vos critères.')

            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = BulkDocumentCreationForm()

    context = {
        'form': form,
        'page_title': 'Création en masse de documents',
    }
    return render(request, 'main/documents/document_bulk_create.html', context)


@login_required
def document_bulk_preview(request):
    """
    Vue AJAX pour prévisualiser les étudiants qui correspondent aux critères
    """
    if request.method == 'POST':
        form = BulkDocumentCreationForm(request.POST)
        if form.is_valid():
            students = form.get_matching_students()
            existing_count = form.get_existing_documents_count()

            # Préparer les données pour la réponse JSON
            students_data = []
            for student in students[:50]:  # Limiter à 50 pour la prévisualisation
                students_data.append({
                    'matricule': student.matricule,
                    'firstname': student.firstname,
                    'lastname': student.lastname,
                    'program': student.program.name if student.program else 'Non défini'
                })

            return JsonResponse({
                'success': True,
                'total_count': students.count(),
                'existing_count': existing_count,
                'new_count': students.count() - existing_count,
                'students': students_data,
                'showing_count': len(students_data)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
