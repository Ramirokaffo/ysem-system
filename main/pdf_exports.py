from io import BytesIO
import os
from pathlib import Path
from django.template.loader import render_to_string

from django.utils import timezone
from django.conf import settings as django_settings
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import weasyprint

from .models import SystemSettings


ANNEX_FIELD_DEFINITIONS = [
    ('metadata', 'acte_naissance'),
    ('metadata', 'preuve_baccalaureat'),
    ('metadata', 'certificat_nationalite'),
    ('metadata', 'releve_notes_last_class'),
    ('metadata', 'justificatif_dernier_diplome'),
    ('metadata', 'bulletins_terminale'),
]


def build_pre_inscription_pdf(student):
    annex_entries = _prepare_annex_entries(student)
    writer = PdfWriter()

    _append_pdf_bytes(writer, _build_summary_pdf(student, annex_entries))

    for annex in annex_entries:
        if not annex['pdf_bytes']:
            continue
        _append_pdf_bytes(writer, _build_annex_cover_pdf(annex))
        _append_pdf_bytes(writer, annex['pdf_bytes'])

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_pre_inscriptions_pdf(students):
    writer = PdfWriter()
    student_count = 0

    for student in students:
        _append_pdf_bytes(writer, build_pre_inscription_pdf(student))
        student_count += 1

    if student_count == 0:
        _append_pdf_bytes(writer, _build_empty_batch_pdf())

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_registration_certificate_pdf(official_document, request=None):
    html = render_to_string(
        'main/pdf/registration_certificate.html',
        _build_registration_certificate_context(official_document),
        request=request
    )
    return weasyprint.HTML(string=html).write_pdf()


def build_payment_receipt_pdf(payment, request=None):
    """Génère un reçu de paiement (PDF) pour un paiement donné, en réutilisant le template HTML."""
    from decimal import Decimal
    from payments.models import Payment
    from payments.utils import amount_to_french_words

    settings = SystemSettings.get_settings()

    group_payments = []
    if payment.group_reference:
        group_payments = list(
            Payment.objects.select_related('installment').filter(
                group_reference=payment.group_reference,
            ).order_by('installment__order_number', 'installment__name', 'pk')
        )

    is_group = len(group_payments) > 1
    if is_group:
        total_amount = sum((p.amount_paid or Decimal('0.00') for p in group_payments), Decimal('0.00'))
    else:
        total_amount = payment.amount_paid or Decimal('0.00')

    formatted = f"{total_amount:,.2f}".replace(',', ' ')
    amount_display = formatted[:-3] if formatted.endswith('.00') else formatted

    amount_in_words = amount_to_french_words(total_amount).strip()
    if amount_in_words:
        amount_in_words = f'{amount_in_words[0].upper()}{amount_in_words[1:]} francs CFA'

    context = {
        'payment': payment,
        'settings': settings,
        'is_group': is_group,
        'group_payments': group_payments,
        'amount_display': amount_display,
        'amount_in_words': amount_in_words,
        'generated_on': timezone.localtime(),
        'auto_print': False,
        'pdf': True,
    }
    html = render_to_string('payments/payment_receipt.html', context, request=request)
    return weasyprint.HTML(string=html).write_pdf()


def _build_registration_certificate_context(official_document):
    student_level = official_document.student_level
    student = student_level.student
    settings = SystemSettings.get_settings()
    issue_date = timezone.localdate()
    full_name = f'{student.firstname} {student.lastname}'.strip()
        # system_settings = SystemSettings.get_settings()

    return {
        'official_document': official_document,
        'logo_uri': _build_logo_uri(settings),
        'logo_alt': settings.get_logo_alt(),
        'institution_name': _display_value(settings.institution_name),
        'institution_code': _display_value(settings.institution_code),
        'system_settings': settings,
        'address': _display_value(settings.address),
        'phone': _display_value(settings.phone),
        'email': _display_value(settings.email),
        'website': _display_value(settings.website),
        'reference': _display_value(official_document.reference),
        'full_name': _display_value(full_name),
        'birth_date': _format_date(student.date_naiss),
        'matricule': _display_value(student.matricule),
        'dossier_number': _display_value(student.dossier_number),
        'program_name': _display_value(getattr(student.program, 'name', None)),
        'level_name': _display_value(getattr(student_level.level, 'name', None)),
        'academic_year_name': _display_value(getattr(student_level.academic_year, 'name', None)),
        'signature_city': 'Yaoundé',
        'issue_date': _format_date(issue_date),
        'issue_date_short': _format_date(issue_date),
    }


def _build_logo_uri(settings):
    candidate_paths = []

    if settings.logo and getattr(settings.logo, 'name', None):
        logo_path = getattr(settings.logo, 'path', None)
        if logo_path:
            candidate_paths.append(logo_path)

    static_root = getattr(django_settings, 'STATIC_ROOT', None)
    if static_root:
        candidate_paths.append(os.path.join(static_root, 'main', 'images', 'ysemlogo.png'))
    candidate_paths.append(
        os.path.join(django_settings.BASE_DIR, 'main', 'static', 'main', 'images', 'ysemlogo.png')
    )

    for candidate_path in candidate_paths:
        if candidate_path and os.path.exists(candidate_path):
            return Path(candidate_path).resolve().as_uri()

    return None


def _build_profile_photo_uri(student):
    profile_photo = getattr(student, 'profile_photo', None)
    if not profile_photo:
        return None
    photo_path = getattr(profile_photo, 'path', None)
    if photo_path and os.path.exists(photo_path):
        return Path(photo_path).resolve().as_uri()
    return None


def _prepare_annex_entries(student):
    entries = []
    for source_name, field_name in ANNEX_FIELD_DEFINITIONS:
        source = student if source_name == 'student' else getattr(student, source_name, None)
        label = _get_field_label(source, field_name)
        entry = {
            'label': label,
            'filename': '',
            'status': 'Non fourni',
            'details': '',
            'pdf_bytes': None,
        }
        file_field = getattr(source, field_name, None) if source else None
        if not file_field:
            entries.append(entry)
            continue

        entry['filename'] = os.path.basename(file_field.name)
        try:
            with file_field.open('rb') as stored_file:
                file_bytes = stored_file.read()
        except FileNotFoundError:
            entry['status'] = 'Introuvable'
            entry['details'] = 'Fichier absent du stockage'
            entries.append(entry)
            continue

        extension = os.path.splitext(file_field.name)[1].lower()
        if extension == '.pdf':
            entry['status'] = 'Inclus'
            entry['pdf_bytes'] = file_bytes
        elif extension in {'.png', '.jpg', '.jpeg'}:
            try:
                entry['status'] = 'Inclus'
                entry['pdf_bytes'] = _image_to_pdf(file_bytes)
            except (UnidentifiedImageError, OSError):
                entry['status'] = 'Erreur'
                entry['details'] = 'Image illisible ou corrompue'
        else:
            entry['status'] = 'Ignoré'
            entry['details'] = f'Format non pris en charge ({extension or "inconnu"})'

        entries.append(entry)

    return entries


def _build_summary_pdf(student, annex_entries):
    context = _build_summary_context(student, annex_entries)
    html = render_to_string('main/pdf/pre_inscription_summary.html', context)
    return weasyprint.HTML(string=html).write_pdf()


def _build_summary_context(student, annex_entries):
    settings = SystemSettings.get_settings()
    metadata = getattr(student, 'metadata', None)

    levels = []
    for student_level in student.student_levels.all():
        level_label = f"{student_level.level.name} - {student_level.academic_year.name}"
        if student_level.is_active:
            level_label += ' (actuel)'
        levels.append(level_label)

    godfather = student.godfather
    godfather_label = 'Aucun parrain'
    if godfather:
        godfather_parts = [godfather.full_name]
        if godfather.phone_number:
            godfather_parts.append(godfather.phone_number)
        if godfather.email:
            godfather_parts.append(godfather.email)
        godfather_label = ' · '.join(godfather_parts)

    specialities = [
        speciality for speciality in [
            student.specialite_souhaitee_1,
            student.specialite_souhaitee_2,
            student.specialite_souhaitee_3,
        ] if speciality
    ]

    family_rows = []
    address_rows = []
    if metadata:
        family_rows = [
            ('Mère - nom complet', metadata.mother_full_name),
            ('Mère - ville', metadata.mother_live_city),
            ('Mère - profession', metadata.mother_occupation),
            ('Mère - téléphone', metadata.mother_phone_number),
            ('Mère - email', metadata.mother_email),
            ('Père - nom complet', metadata.father_full_name),
            ('Père - ville', metadata.father_live_city),
            ('Père - profession', metadata.father_occupation),
            ('Père - téléphone', metadata.father_phone_number),
            ('Père - email', metadata.father_email),
        ]
        address_rows = [
            ('Pays d\'origine', metadata.original_country),
            ('Région d\'origine', metadata.original_region),
            ('Département d\'origine', metadata.original_department),
            ('District d\'origine', metadata.original_district),
            ('Ville de résidence', metadata.residence_city),
            ('Quartier de résidence', metadata.residence_quarter),
        ]

    annex_rows = []
    for annex in annex_entries:
        suffix = f" — {annex['details']}" if annex['details'] else ''
        filename = annex['filename'] or 'Aucun fichier'
        annex_rows.append((annex['label'], f"{filename} ({annex['status']}){suffix}"))

    dossier_rows = [('Dossier complet', 'Oui' if metadata and metadata.is_complete else 'Non')]

    sections = [
        {
            'title': 'Informations personnelles',
            'rows': _normalize_rows([
                ('Matricule', student.matricule),
                ('Nom complet', f'{student.firstname} {student.lastname}'),
                ('Date de naissance', _format_date(student.date_naiss)),
                ('Genre', getattr(student, 'get_gender_display', lambda: 'Non renseigné')()),
                ('Téléphone', student.phone_number),
                ('Email', student.email),
                ('Langue', getattr(student, 'get_lang_display', lambda: 'Non renseigné')()),
                ('Statut', student.get_status_display()),
                ('Date de pré-inscription', _format_datetime(student.created_at)),
                ('Dernière modification', _format_datetime(student.last_updated)),
            ]),
        },
        {
            'title': 'Informations académiques',
            'rows': _normalize_rows([
                ('Programme', getattr(student.program, 'name', None)),
                ('École d\'origine', getattr(student.school, 'name', None)),
                ('Spécialités souhaitées', ' ; '.join(specialities) if specialities else None),
                ('Parrain', godfather_label),
                ('Niveaux d\'études d\'entrée', ' ; '.join(levels) if levels else None),
            ]),
        },
        {
            'title': 'Cursus scolaire et universitaire',
            'rows': _normalize_rows(_build_curriculum_rows(student)),
        },
        {
            'title': 'Informations familiales',
            'rows': _normalize_rows(family_rows or [('Informations familiales', 'Non renseignées')]),
        },
        {
            'title': 'Adresse',
            'rows': _normalize_rows(address_rows or [('Adresse', 'Non renseignée')]),
        },
        {
            'title': 'Pièces jointes annexées au PDF',
            'rows': _normalize_rows(annex_rows),
        },
        {
            'title': 'État du dossier',
            'rows': _normalize_rows(dossier_rows),
        },
    ]

    return {
        'logo_uri': _build_logo_uri(settings),
        'logo_alt': settings.get_logo_alt(),
        'profile_photo_uri': _build_profile_photo_uri(student),
        'full_name': f'{student.firstname} {student.lastname}',
        'sections': sections,
    }


def _normalize_rows(rows):
    return [(label, _display_value(value)) for label, value in rows]


def _build_curriculum_rows(student):
    rows = []

    secondary_diplomas = sorted(
        student.secondary_diplomas.all(),
        key=lambda diploma: (diploma.obtained_year or 0, diploma.pk or 0),
    )
    for index, diploma in enumerate(secondary_diplomas, start=1):
        rows.append((f'Cursus scolaire {index}', _format_secondary_diploma(diploma)))

    university_levels = sorted(
        student.university_levels.all(),
        key=lambda level: (level.academic_year or '', level.pk or 0),
    )
    for index, university_level in enumerate(university_levels, start=1):
        rows.append((f'Cursus universitaire {index}', _format_university_level(university_level)))

    return rows or [('Cursus', 'Non renseigné')]


def _format_secondary_diploma(diploma):
    details = [diploma.name]
    if diploma.serie:
        details.append(f'Série / spécialité : {diploma.serie}')
    if diploma.obtained_year:
        details.append(f'Année d\'obtention : {diploma.obtained_year}')
    if diploma.mention:
        details.append(f'Mention : {diploma.mention}')
    if diploma.school:
        details.append(f'Établissement : {diploma.school.name}')
    return ' ; '.join(details)


def _format_university_level(university_level):
    details = [f'Niveau : {university_level.level_name}']
    if university_level.diploma_name:
        details.append(f'Diplôme obtenu : {university_level.diploma_name}')
    if university_level.speciality:
        details.append(f'Spécialité : {university_level.speciality}')
    if university_level.academic_year:
        details.append(f'Année académique : {university_level.academic_year}')
    if university_level.university:
        details.append(f'Université : {university_level.university.name}')
    return ' ; '.join(details)


def _build_annex_cover_pdf(annex):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf_canvas.setTitle(f"Annexe - {annex['label']}")
    pdf_canvas.setFont('Helvetica-Bold', 18)
    pdf_canvas.drawCentredString(width / 2, height - 5 * cm, 'Annexe du dossier de pré-inscription')
    pdf_canvas.setFont('Helvetica-Bold', 14)
    pdf_canvas.drawCentredString(width / 2, height - 7 * cm, annex['label'])
    pdf_canvas.setFont('Helvetica', 11)
    pdf_canvas.drawCentredString(width / 2, height - 8.3 * cm, annex['filename'])
    pdf_canvas.showPage()
    pdf_canvas.save()
    return buffer.getvalue()


def _build_empty_batch_pdf():
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf_canvas.setTitle('Export des pré-inscriptions filtrées')
    pdf_canvas.setFont('Helvetica-Bold', 18)
    pdf_canvas.drawCentredString(width / 2, height - 5 * cm, 'Export des pré-inscriptions filtrées')
    pdf_canvas.setFont('Helvetica', 12)
    pdf_canvas.drawCentredString(width / 2, height - 7 * cm, 'Aucune pré-inscription ne correspond aux filtres fournis.')
    pdf_canvas.showPage()
    pdf_canvas.save()
    return buffer.getvalue()


def _append_pdf_bytes(writer, pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    for page in reader.pages:
        writer.add_page(page)


def _image_to_pdf(image_bytes):
    with Image.open(BytesIO(image_bytes)) as image:
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        output = BytesIO()
        image.save(output, format='PDF', resolution=150.0)
        return output.getvalue()


def _get_field_label(source, field_name):
    if not source:
        return field_name.replace('_', ' ').capitalize()
    return str(source._meta.get_field(field_name).verbose_name).capitalize()


def _display_value(value):
    if value in (None, ''):
        return 'Non renseigné'
    return str(value)


def _format_date(value):
    return value.strftime('%d/%m/%Y') if value else 'Non renseigné'


def _format_datetime(value):
    return value.strftime('%d/%m/%Y à %H:%M') if value else 'Non renseigné'
