import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from django.db.models import Q

from student_portal.decorators import scholar_admin_required
from students.models import Student, StudentLevel, StudentMetaData
from accounts.models import Godfather
from schools.models import School
from academic.models import Program, Level, Speciality
from academic.document_requirements import PROGRAM_DOCUMENTS
from main.utils import queue_student_status_email, render_student_edit


MOBILE_UPLOAD_TOKEN_SALT = 'students.mobile_file_upload'
MOBILE_UPLOAD_TOKEN_MAX_AGE = 30 * 60
MOBILE_UPLOAD_MAX_FILE_SIZE = 5 * 1024 * 1024


class EtudiantsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des étudiants"""
    template_name = 'students/etudiants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des étudiants'
        students = Student.objects.filter(status='registered')

        gender = self.request.GET.get('gender')
        school_id = self.request.GET.get('school')
        program_id = self.request.GET.get('program')
        godfather_id = self.request.GET.get('godfather')
        language = self.request.GET.get('language')
        search = self.request.GET.get('search', '').strip()
        current_level_id = self.request.GET.get('current_level')
        start_level_id = self.request.GET.get('start_level')
        speciality_id = self.request.GET.get('speciality')

        if search:
            students = students.filter(
                Q(firstname__icontains=search) |
                Q(lastname__icontains=search) |
                Q(matricule__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        if gender:
            students = students.filter(gender=gender)
        if school_id:
            students = students.filter(school_id=school_id)
        if program_id:
            students = students.filter(program_id=program_id)
        if godfather_id:
            students = students.filter(godfather_id=godfather_id)
        if language:
            students = students.filter(lang=language)
        if start_level_id:
            students = students.filter(start_level_id=start_level_id)
        if current_level_id:
            student_ids = StudentLevel.objects.filter(
                is_active=True, level_id=current_level_id
            ).values_list('student_id', flat=True)
            students = students.filter(pk__in=student_ids)
        if speciality_id:
            student_ids = StudentLevel.objects.filter(
                is_active=True, speciality_id=speciality_id
            ).values_list('student_id', flat=True)
            students = students.filter(pk__in=student_ids)

        schools = School.objects.all()
        programs = Program.objects.all()
        godfathers = Godfather.objects.all()
        levels = Level.objects.all()
        specialities = Speciality.objects.all()

        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        paginator = Paginator(students, per_page)
        page_obj = paginator.get_page(page)

        context['students'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        context['schools'] = schools
        context['programs'] = programs
        context['godfathers'] = godfathers
        context['levels'] = levels
        context['specialities'] = specialities
        return context



@login_required
def etudiant_detail(request, pk):
    """
    Vue pour afficher les détails complets d'un étudiant avec toutes ses relations
    """
    # Récupération de l'étudiant avec toutes ses relations en une seule requête
    student = get_object_or_404(
        Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather',
            'start_level'
        ).prefetch_related(
            'secondary_diplomas__school',
            'student_levels__level',
            'student_levels__academic_year',
            'student_levels__speciality',
            'student_levels__official_documents',
            'university_levels__university',
        ),
        matricule=pk
    )

    # queue_student_status_email(student, 'pre_inscription')


    # Récupération des niveaux avec leurs documents officiels
    student_levels = student.student_levels.all().order_by('-academic_year__start_at', 'level__name')

    # Statistiques sur les documents
    total_documents = 0
    available_documents = 0
    withdrawn_documents = 0

    for level in student_levels:
        docs = level.official_documents.all()
        total_documents += docs.count()
        available_documents += docs.filter(status='available').count()
        withdrawn_documents += docs.filter(status='withdrawn').count()

    context = {
        'student': student,
        'student_levels': student_levels,
        'document_stats': {
            'total': total_documents,
            'available': available_documents,
            'withdrawn': withdrawn_documents,
            'lost': total_documents - available_documents - withdrawn_documents
        }
    }

    return render(request, 'students/etudiant_detail.html', context)



@login_required
@scholar_admin_required
def generate_student_external_password(request, pk):
    """
    Vue pour générer/réinitialiser le mot de passe externe d'un étudiant
    Accessible uniquement aux responsables de scolarité
    """

    student = get_object_or_404(Student, matricule=pk)

    if request.method == 'POST':
        try:
            # Génération du nouveau mot de passe
            new_password = student.generate_external_password()

            # Message de succès avec le mot de passe (à communiquer à l'étudiant)
            messages.success(
                request,
                f"Mot de passe externe généré avec succès pour {student.firstname} {student.lastname}. "
                f"Mot de passe à communiquer à l'étudiant : <strong>{new_password}</strong>"
            )

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du mot de passe : {str(e)}")

    return redirect('students:etudiant_detail', pk=pk)


@login_required
def etudiant_edit(request, pk):
    """
    Vue pour modifier les informations d'un étudiant
    """
    # Récupération de l'étudiant avec ses relations
    student = get_object_or_404(
        Student.objects.select_related('metadata', 'school', 'program', 'godfather'),
        matricule=pk
    )

    return render_student_edit(
        request=request,
        student=student,
        detail_route_name='students:etudiant_detail',
        page_title="Modifier l'étudiant",
        success_message="Les informations de l'étudiant ont été mises à jour avec succès.",
        back_link_label='Retour aux détails',
    )




def generate_mobile_upload_token(matricule):
    """Signe le matricule pour générer un jeton d'upload mobile à durée limitée."""
    return signing.dumps(matricule, salt=MOBILE_UPLOAD_TOKEN_SALT)


def _decode_mobile_upload_token(token):
    return signing.loads(token, salt=MOBILE_UPLOAD_TOKEN_SALT, max_age=MOBILE_UPLOAD_TOKEN_MAX_AGE)


def _build_mobile_upload_field_definitions(student):
    """Construit la liste des champs fichiers proposés sur la page mobile."""
    metadata = student.metadata
    fields = [{
        'field_name': 'profile_photo',
        'target': 'student',
        'label': 'Photo de profil',
        'help_text': "Formats acceptés : JPG, PNG (5 Mo max).",
        'accept': 'image/png,image/jpeg',
        'capture': 'user',
        'extensions': ('.png', '.jpg', '.jpeg'),
        'current_file': student.profile_photo or None,
        'is_image': True,
    }]
    for document in PROGRAM_DOCUMENTS:
        field_name = document['field_name']
        current_file = getattr(metadata, field_name, None) if metadata else None
        fields.append({
            'field_name': field_name,
            'target': 'metadata',
            'label': document['label'],
            'help_text': document['help_text'],
            'accept': '.png,.jpg,.jpeg,.pdf',
            'capture': 'environment',
            'extensions': ('.png', '.jpg', '.jpeg', '.pdf'),
            'current_file': current_file or None,
            'is_image': False,
        })
    return fields


def _validate_mobile_upload_file(uploaded, field_def):
    extension = os.path.splitext(uploaded.name)[1].lower()
    if extension not in field_def['extensions']:
        return f"Format non supporté ({extension or 'inconnu'}). Formats acceptés : {', '.join(field_def['extensions'])}."
    if uploaded.size > MOBILE_UPLOAD_MAX_FILE_SIZE:
        return "Le fichier dépasse la taille maximale autorisée (5 Mo)."
    return None


def mobile_file_upload(request, token):
    """
    Page d'upload de fichiers depuis un mobile, accessible via QR code.
    Authentifiée par jeton signé (matricule + durée limitée), pas de login requis.
    """
    try:
        matricule = _decode_mobile_upload_token(token)
    except signing.SignatureExpired:
        return render(request, 'students/mobile_file_upload.html', {
            'token_expired': True,
        }, status=410)
    except signing.BadSignature:
        raise Http404("Lien invalide.")

    student = get_object_or_404(
        Student.objects.select_related('metadata'),
        matricule=matricule,
    )

    if not student.metadata:
        student.metadata = StudentMetaData.objects.create(original_country='Cameroun')
        student.save()

    field_definitions = _build_mobile_upload_field_definitions(student)
    field_errors = {}

    if request.method == 'POST':
        saved_count = 0
        for field_def in field_definitions:
            uploaded = request.FILES.get(field_def['field_name'])
            if not uploaded:
                continue
            error = _validate_mobile_upload_file(uploaded, field_def)
            if error:
                field_errors[field_def['field_name']] = error
                continue
            target_obj = student if field_def['target'] == 'student' else student.metadata
            previous_file = getattr(target_obj, field_def['field_name'])
            previous_name = getattr(previous_file, 'name', '')
            setattr(target_obj, field_def['field_name'], uploaded)
            target_obj.save()
            new_name = getattr(getattr(target_obj, field_def['field_name']), 'name', '')
            if previous_name and previous_name != new_name:
                try:
                    previous_file.storage.delete(previous_name)
                except Exception:
                    pass
            saved_count += 1

        if saved_count and not field_errors:
            messages.success(request, f"{saved_count} fichier(s) enregistré(s) avec succès.")
        elif saved_count and field_errors:
            messages.warning(request, f"{saved_count} fichier(s) enregistré(s). Certains fichiers ont été refusés.")
        elif field_errors:
            messages.error(request, "Aucun fichier n'a pu être enregistré. Veuillez corriger les erreurs.")
        else:
            messages.info(request, "Aucun fichier sélectionné.")

        field_definitions = _build_mobile_upload_field_definitions(student)

    context = {
        'student': student,
        'file_fields': field_definitions,
        'token': token,
        'field_errors': field_errors,
        'token_expired': False,
        'max_file_size_mb': MOBILE_UPLOAD_MAX_FILE_SIZE // (1024 * 1024),
    }
    return render(request, 'students/mobile_file_upload.html', context)
