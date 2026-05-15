from django.contrib import messages
import re

from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from audit.utils import log_audit_event
from main.forms import SecondaryDiplomaFormSet, StudentLevelForm, UniversityLevelFormSet
from students.forms import StudentEditForm, StudentMetaDataEditForm
from main.program_documents import build_program_document_entries, get_required_program_document_field_names
from .emails import send_student_status_email
from schools.models import School, SecondaryDiploma, UniversityLevel
from students.models import Student, StudentLevel, OfficialDocument, StudentMetaData

from academic.document_requirements import DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS, PROGRAM_DOCUMENT_FIELD_NAMES
from main.program_documents import build_program_document_entries
from django.forms import ValidationError

from academic.models import Program


SECONDARY_DIPLOMA_FORMSET_PREFIX = 'secondary_diplomas'
UNIVERSITY_LEVEL_FORMSET_PREFIX = 'university_levels'
PRE_INSCRIPTION_STATUSES = ['pending', 'abandoned', 'approved', 'rejected']


def get_program_from_value(program_value):
    
    if isinstance(program_value, Program):
        return program_value
    if not program_value:
        return None
    return Program.objects.filter(pk=program_value).first()


def metadata_form_has_document(metadata_form, field_name):
    if metadata_form.files.get(field_name):
        return True
    if metadata_form.cleaned_data.get(f'remove_{field_name}'):
        return False

    current_file = getattr(metadata_form.instance, field_name, None)
    return bool(getattr(current_file, 'name', ''))


def validate_metadata_program_documents(metadata_form, program, force_optional=False):
    if force_optional:
        return True

    is_valid = True

    for field_name in get_required_program_document_field_names(program):
        if metadata_form_has_document(metadata_form, field_name):
            continue

        metadata_form.add_error(field_name, "Ce document est requis pour le programme sélectionné.")
        is_valid = False

    return is_valid


def build_metadata_form_document_entries(metadata_form, program=None, force_optional=False):
    entries = []
    for document_entry in build_program_document_entries(
        program=program,
        metadata=metadata_form.instance,
        fallback_visible_fields=None if force_optional else DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS,
        force_optional=force_optional,
    ):
        remove_field_name = f"remove_{document_entry['field_name']}"
        entries.append({
            **document_entry,
            'field': metadata_form[document_entry['field_name']],
            'remove_field': metadata_form[remove_field_name] if remove_field_name in metadata_form.fields else None,
        })

    return entries


# def _send_student_status_email(student, notification_type):
#     return send_student_status_email(student, notification_type)


def queue_student_status_email(student, notification_type):
    transaction.on_commit(lambda: send_student_status_email(student, notification_type))


def extract_dossier_sequence(dossier_number):
    """Extrait la séquence numérique finale d'un numéro de dossier."""
    if not dossier_number:
        return None

    match = re.search(r'([0-9]{1,4})$', str(dossier_number).strip())
    if not match:
        return None

    return int(match.group(1))


def infer_program_code(student, student_level):
    """Déduit le code programme à partir du programme ou du niveau."""
    candidates = []

    if student.program and student.program.name:
        candidates.append(student.program.name)
    if student_level.level and student_level.level.name:
        candidates.append(student_level.level.name)

    for candidate in candidates:
        normalized = candidate.strip().lower()
        if 'licence' in normalized:
            return '1'
        if 'master' in normalized:
            return '2'
        if 'doctorat' in normalized or 'phd' in normalized:
            return '3'

    raise ValidationError("Impossible de déterminer le code programme pour cet étudiant.")


def infer_cycle_code(student_level):
    """Déduit le code cycle à partir du niveau de l'étudiant."""
    level_name = student_level.level.name if student_level.level else ''
    match = re.search(r'([0-9]+)', level_name)

    if not match:
        raise ValidationError("Impossible de déterminer le code cycle à partir du niveau d'inscription.")

    return match.group(1)[-1]


def infer_dossier_prefix(student, student_level):
    """Déduit un préfixe de dossier lisible à partir du programme."""
    candidates = []

    if student.program and student.program.name:
        candidates.append(student.program.name)
    if student_level.level and student_level.level.name:
        candidates.append(student_level.level.name)

    for candidate in candidates:
        normalized = candidate.strip().lower()
        if 'licence' in normalized:
            return 'L'
        if 'master' in normalized:
            return 'M'
        if 'doctorat' in normalized or 'phd' in normalized:
            return 'D'

    return 'D'


def build_student_matricule(year_code, program_code, cycle_code, dossier_last4):
    """Construit le matricule final selon la formule métier fournie."""
    base = f"{year_code}{program_code}{cycle_code}{dossier_last4}"

    if not base.isdigit() or len(year_code) != 2 or len(program_code) != 1 or len(cycle_code) != 1 or len(dossier_last4) != 4:
        raise ValidationError("Les composants du matricule final sont invalides.")

    check_digit = (sum(int(char) for char in base) * 3) % 10
    return f"{base}{check_digit}"


def get_next_dossier_sequence():
    """Retourne la prochaine séquence de dossier disponible."""
    stored_sequences = [
        sequence
        for sequence in (
            extract_dossier_sequence(value)
            for value in Student.objects.exclude(dossier_number__isnull=True)
            .exclude(dossier_number__exact='')
            .values_list('dossier_number', flat=True)
        )
        if sequence is not None
    ]
    highest_sequence = max(stored_sequences, default=0)
    return max(highest_sequence, Student.objects.count()) + 1


def generate_final_registration_identifiers(student):
    """Génère le numéro de dossier et le matricule définitif d'une pré-inscription approuvée."""
    student_level = get_student_level_for_edit(student)
    if not student_level or not student_level.level or not student_level.academic_year:
        raise ValidationError("Impossible d'inscrire cet étudiant sans niveau et année académique actifs.")

    year_code = str(student_level.academic_year.start_at.year)[-2:]
    program_code = infer_program_code(student, student_level)
    cycle_code = infer_cycle_code(student_level)
    dossier_prefix = infer_dossier_prefix(student, student_level)
    sequence = extract_dossier_sequence(student.dossier_number) or get_next_dossier_sequence()

    for _ in range(10000):
        dossier_last4 = f"{sequence:04d}"
        dossier_number = f"{dossier_prefix}{dossier_last4}"
        matricule = build_student_matricule(year_code, program_code, cycle_code, dossier_last4)

        if not Student.objects.filter(matricule=matricule).exclude(pk=student.pk).exists():
            return dossier_number, matricule

        sequence += 1

    raise ValidationError("Aucun matricule définitif disponible n'a pu être généré.")


def build_registration_certificate_reference(student, student_level):
    """Construit la référence du certificat d'inscription."""
    if not student_level or not student_level.academic_year or not student_level.academic_year.start_at:
        raise ValidationError("Impossible de générer la référence du certificat d'inscription sans année académique active.")

    return f"CI-{student_level.academic_year.start_at.year}-{student.matricule}"


def ensure_registration_certificate(student):
    """Crée ou met à jour le certificat d'inscription rattaché à l'étudiant."""
    student_level = get_student_level_for_edit(student)
    if not student_level:
        raise ValidationError("Impossible de créer le certificat d'inscription sans niveau étudiant actif.")

    reference = build_registration_certificate_reference(student, student_level)
    document, _ = OfficialDocument.objects.get_or_create(
        student_level=student_level,
        type=OfficialDocument.TYPE_REGISTRATION_CERTIFICATE,
        defaults={
            'reference': reference,
            'status': 'available',
        },
    )

    fields_to_update = []
    if document.reference != reference:
        document.reference = reference
        fields_to_update.append('reference')
    if document.status != 'available':
        document.status = 'available'
        fields_to_update.append('status')

    if fields_to_update:
        document.save(update_fields=fields_to_update)

    return document


def replace_student_primary_key(student, new_matricule, dossier_number):
    """Met à jour le matricule et le numéro de dossier de l'étudiant sans le supprimer."""
    old_matricule = student.matricule
    old_dossier_number = student.dossier_number
    old_status = student.status

    student.matricule = new_matricule
    student.dossier_number = dossier_number
    student.status = 'registered'
    student.save(update_fields=['matricule', 'dossier_number', 'status'])

    log_audit_event(
        category='business',
        action='bulk_update',
        instance=student,
        changes={
            'matricule': {'from': old_matricule, 'to': new_matricule},
            'dossier_number': {'from': old_dossier_number, 'to': dossier_number},
            'status': {'from': old_status, 'to': 'registered'},
        },
        context={
            'operation': 'student_registration_rebinding',
        },
        message="Transformation d'une pré-inscription en inscription définitive.",
    )
    return student


def get_filtered_pre_inscriptions_queryset(params, queryset=None):
    """Construit le queryset de pré-inscriptions à partir des filtres GET."""
    students = queryset if queryset is not None else Student.objects.all()

    # Exclure les étudiants supprimés (soft delete)
    students = students.filter(deleted_at__isnull=True)

    status = params.get('status')
    is_online_registration = params.get('is_online_registration')
    is_complete = params.get('is_complete')
    gender = params.get('gender')
    school_id = params.get('school')
    program_id = params.get('program')
    godfather_id = params.get('godfather')
    language = params.get('language')

    academic_year_id = params.get('academic_year')
    date_from = params.get('date_from') or ''
    date_to = params.get('date_to') or ''
    include_rejected = params.get('include_rejected') == 'yes'

    if status:
        students = students.filter(status=status)
    else:
        allowed_statuses = PRE_INSCRIPTION_STATUSES
        if not include_rejected:
            allowed_statuses = [s for s in allowed_statuses if s != 'rejected']
        students = students.filter(status__in=allowed_statuses)

    if is_online_registration:
        students = students.filter(metadata__is_online_registration=is_online_registration)

    if is_complete:
        students = students.filter(metadata__is_complete=is_complete)

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
    if academic_year_id:
        students = students.filter(student_levels__academic_year_id=academic_year_id).distinct()
    if date_from:
        students = students.filter(created_at__date__gte=date_from)
    if date_to:
        students = students.filter(created_at__date__lte=date_to)

    return students.order_by('-created_at', 'matricule')


def build_secondary_diploma_initial_data(student):
    return [
        {
            'name': diploma.name,
            'serie': diploma.serie or '',
            'obtained_year': diploma.obtained_year,
            'mention': diploma.mention or '',
            'school_existant': diploma.school_id or '',
            'school_name': '',
        }
        for diploma in student.secondary_diplomas.select_related('school').order_by('obtained_year', 'pk')
    ]


def build_university_level_initial_data(student):
    return [
        {
            'level_name': university_level.level_name,
            'diploma_name': university_level.diploma_name or '',
            'speciality': university_level.speciality or '',
            'academic_year': university_level.academic_year or '',
            'university_existant': university_level.university_id or '',
            'university_name': '',
        }
        for university_level in student.university_levels.select_related('university').order_by('academic_year', 'pk')
    ]


def build_secondary_diploma_formset_for_student(student, data=None):
    return SecondaryDiplomaFormSet(
        data=data,
        initial=build_secondary_diploma_initial_data(student),
        prefix=SECONDARY_DIPLOMA_FORMSET_PREFIX,
    )


def build_university_level_formset_for_student(student, data=None):
    return UniversityLevelFormSet(
        data=data,
        initial=build_university_level_initial_data(student),
        prefix=UNIVERSITY_LEVEL_FORMSET_PREFIX,
    )


def get_or_create_school(name, level):
    school_name = (name or '').strip()
    if not school_name:
        return None

    school = School.objects.filter(name__iexact=school_name, level=level).first()
    if school:
        return school

    return School.objects.create(name=school_name, level=level)


def _extract_first_integer(value):
    match = re.search(r'(\d+)', value or '')
    return int(match.group(1)) if match else 0


def _extract_year(value):
    match = re.search(r'(\d{4})', value or '')
    return int(match.group(1)) if match else 0


def _secondary_diploma_rank(diploma):
    diploma_name = (getattr(diploma, 'name', '') or '').strip().lower()

    if 'baccalaur' in diploma_name or 'gce a-level' in diploma_name:
        return 30
    if 'probatoire' in diploma_name or diploma_name == 'bt':
        return 20
    if diploma_name in {'bepc', 'cap', 'gce o-level'}:
        return 10
    return 0


def _university_level_rank(university_level):
    level_name = getattr(university_level, 'level_name', '') or ''
    diploma_name = getattr(university_level, 'diploma_name', '') or ''
    normalized = f'{level_name} {diploma_name}'.strip().lower()
    numeric_rank = _extract_first_integer(level_name) or _extract_first_integer(diploma_name)

    cycle_rank = 0
    if 'doctorat' in normalized or 'phd' in normalized:
        cycle_rank = 300
    elif 'master' in normalized:
        cycle_rank = 200
    elif 'licence' in normalized or 'bachelor' in normalized:
        cycle_rank = 100
    elif any(keyword in normalized for keyword in ['deug', 'bts', 'hnd', 'dut']):
        cycle_rank = 50

    return 1000 + cycle_rank + numeric_rank


def save_secondary_diplomas(student, formset):
    secondary_diplomas = []

    for diploma_form in formset:
        if not getattr(diploma_form, 'cleaned_data', None):
            continue
        if diploma_form.cleaned_data.get('DELETE'):
            continue
        if not diploma_form.cleaned_data.get('name') or not diploma_form.cleaned_data.get('obtained_year'):
            continue

        diploma = diploma_form.save(commit=False)
        diploma.student = student
        diploma.school = diploma_form.cleaned_data.get('school_existant') or get_or_create_school(
            diploma_form.cleaned_data.get('school_name'),
            'secondary',
        )
        diploma.save()
        secondary_diplomas.append(diploma)

    return secondary_diplomas


def save_university_levels(student, formset):
    university_levels = []

    for level_form in formset:
        if not getattr(level_form, 'cleaned_data', None):
            continue
        if level_form.cleaned_data.get('DELETE'):
            continue
        if not level_form.cleaned_data.get('level_name'):
            continue

        university_level = level_form.save(commit=False)
        university_level.student = student
        university_level.university = level_form.cleaned_data.get('university_existant') or get_or_create_school(
            level_form.cleaned_data.get('university_name'),
            'higher',
        )
        university_level.save()
        university_levels.append(university_level)

    return university_levels


def resolve_student_school(secondary_diplomas, university_levels=None):
    candidates = []

    for diploma in secondary_diplomas or []:
        if not diploma.school:
            continue
        candidates.append((
            _secondary_diploma_rank(diploma),
            getattr(diploma, 'obtained_year', 0) or 0,
            getattr(diploma, 'pk', 0) or 0,
            diploma.school,
        ))

    for university_level in university_levels or []:
        if not university_level.university:
            continue
        candidates.append((
            _university_level_rank(university_level),
            _extract_year(getattr(university_level, 'academic_year', '')),
            getattr(university_level, 'pk', 0) or 0,
            university_level.university,
        ))

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate[:3])[3]




def get_student_level_for_edit(student):
    """Retourne le niveau actif de l'étudiant ou le plus récent à défaut."""
    active_level = student.student_levels.select_related('level', 'academic_year').filter(is_active=True).order_by(
        '-academic_year__start_at', 'level__name'
    ).first()
    if active_level:
        return active_level

    return student.student_levels.select_related('level', 'academic_year').order_by(
        '-academic_year__start_at', 'level__name'
    ).first()


def render_student_edit(request, student, detail_route_name, page_title, success_message, back_link_label):
    """Rendu commun des formulaires d'édition étudiant / pré-inscription."""
    documents_mode = 'admin_only_optional'
    documents_force_optional = documents_mode == 'admin_only_optional'

    if not student.metadata:
        student.metadata = StudentMetaData.objects.create(original_country='Cameroun')
        student.save()

    student_level = get_student_level_for_edit(student)
    selected_program = student.program
    secondary_diploma_formset = build_secondary_diploma_formset_for_student(student)
    university_level_formset = build_university_level_formset_for_student(student)

    if request.method == 'POST':
        student_form = StudentEditForm(request.POST, request.FILES, instance=student)
        metadata_form = StudentMetaDataEditForm(request.POST, request.FILES, instance=student.metadata)
        student_level_form = StudentLevelForm(request.POST, instance=student_level, student=student)
        secondary_diploma_formset = build_secondary_diploma_formset_for_student(student, request.POST)
        university_level_formset = build_university_level_formset_for_student(student, request.POST)
        selected_program = get_program_from_value(request.POST.get('program')) or student.program

        student_form_is_valid = student_form.is_valid()
        metadata_form_is_valid = metadata_form.is_valid()
        student_level_form_is_valid = student_level_form.is_valid()
        secondary_diploma_formset_is_valid = secondary_diploma_formset.is_valid()
        university_level_formset_is_valid = university_level_formset.is_valid()

        if (
            student_form_is_valid
            and metadata_form_is_valid
            and student_level_form_is_valid
            and secondary_diploma_formset_is_valid
            and university_level_formset_is_valid
        ):
            selected_program = student_form.cleaned_data.get('program') or selected_program

            if validate_metadata_program_documents(
                metadata_form,
                selected_program,
                force_optional=documents_force_optional,
            ):
                with transaction.atomic():
                    student_form.save()
                    metadata_form.save()

                    saved_student_level = student_level_form.save(commit=False)
                    saved_student_level.student = student
                    saved_student_level.is_active = True
                    saved_student_level.save()
                    levels_to_deactivate = list(
                        student.student_levels.exclude(pk=saved_student_level.pk).filter(is_active=True).values_list('pk', flat=True)
                    )
                    if levels_to_deactivate:
                        student.student_levels.filter(pk__in=levels_to_deactivate).update(is_active=False)
                        log_audit_event(
                            category='business',
                            action='bulk_update',
                            instance=student,
                            context={
                                'operation': 'deactivate_previous_student_levels',
                                'deactivated_student_level_ids': levels_to_deactivate,
                                'active_student_level_id': saved_student_level.pk,
                            },
                            message="Désactivation des anciens niveaux actifs de l'étudiant.",
                        )
                    if student_level_form.cleaned_data.get('level'):
                        student.start_level = student_level_form.cleaned_data['level']
                        student.save(update_fields=['start_level'])

                    SecondaryDiploma.objects.filter(student=student).delete()
                    UniversityLevel.objects.filter(student=student).delete()

                    secondary_diplomas = save_secondary_diplomas(student, secondary_diploma_formset)
                    university_levels = save_university_levels(student, university_level_formset)

                    student_school = resolve_student_school(secondary_diplomas, university_levels)
                    if student_school and student.school_id != student_school.pk:
                        student.school = student_school
                        student.save(update_fields=['school'])

                messages.success(request, success_message)
                return redirect(detail_route_name, pk=student.matricule)

        messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        student_form = StudentEditForm(instance=student)
        metadata_form = StudentMetaDataEditForm(instance=student.metadata)
        student_level_form = StudentLevelForm(instance=student_level, student=student)

    from students.views import generate_mobile_upload_token, MOBILE_UPLOAD_TOKEN_MAX_AGE

    mobile_upload_token = generate_mobile_upload_token(student.matricule)
    mobile_upload_url = request.build_absolute_uri(
        reverse('students:mobile_file_upload', kwargs={'token': mobile_upload_token})
    )

    context = {
        'student': student,
        'student_form': student_form,
        'metadata_form': metadata_form,
        'student_level_form': student_level_form,
        'secondary_diploma_formset': secondary_diploma_formset,
        'university_level_formset': university_level_formset,
        'page_title': page_title,
        'back_url': reverse(detail_route_name, kwargs={'pk': student.matricule}),
        'back_link_label': back_link_label,
        'documents_mode': documents_mode,
        'document_entries': build_metadata_form_document_entries(
            metadata_form,
            selected_program,
            force_optional=documents_force_optional,
        ),
        'mobile_upload_url': mobile_upload_url,
        'mobile_upload_token_minutes': MOBILE_UPLOAD_TOKEN_MAX_AGE // 60,
    }

    return render(request, 'students/etudiant_edit.html', context)

