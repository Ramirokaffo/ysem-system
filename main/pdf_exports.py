from io import BytesIO
import os
from urllib import request
from xml.sax.saxutils import escape

from django.utils import timezone
from django.conf import settings as django_settings
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as PlatypusImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def build_registration_certificate_pdf(official_document):
    student_level = official_document.student_level
    student = student_level.student
    settings = SystemSettings.get_settings()
    issue_date = timezone.localdate()
    styles = _build_styles()
    buffer = BytesIO()

    document = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.7 * cm, bottomMargin=1.7 * cm)
    full_name = f'{student.firstname} {student.lastname}'.strip()
    contact_parts = [settings.address]
    if settings.phone:
        contact_parts.append(f"Tél. : {settings.phone}")
    if settings.email:
        contact_parts.append(f"Email : {settings.email}")
    if settings.website:
        contact_parts.append(settings.website)
    contact_line = ' · '.join(part for part in contact_parts if part)

    story = [
        Paragraph(escape(settings.institution_name), styles['title_centered']),
        Paragraph(escape(contact_line or ' '), styles['subtitle_centered']),
        Spacer(1, 0.45 * cm),
        Paragraph("CERTIFICAT D'INSCRIPTION", styles['certificate_title']),
        Paragraph(f"Référence : {escape(_display_value(official_document.reference))}", styles['certificate_reference']),
        Spacer(1, 0.35 * cm),
    ]

    story.extend(_build_section('Informations de l’inscription', [
        ('Nom complet', full_name),
        ('Matricule', student.matricule),
        ('Numéro de dossier', student.dossier_number),
        ('Programme', getattr(student.program, 'name', None)),
        ('Niveau', getattr(student_level.level, 'name', None)),
        ('Année académique', getattr(student_level.academic_year, 'name', None)),
        ('Date de délivrance', _format_date(issue_date)),
    ], styles))

    story.append(Paragraph(
        (
            f"Nous certifions que <b>{escape(_display_value(full_name))}</b>, matricule "
            f"<b>{escape(_display_value(student.matricule))}</b>, numéro de dossier "
            f"<b>{escape(_display_value(student.dossier_number))}</b>, est régulièrement inscrit(e) "
            f"en <b>{escape(_display_value(getattr(student_level.level, 'name', None)))}</b> au titre de "
            f"l'année académique <b>{escape(_display_value(getattr(student_level.academic_year, 'name', None)))}</b> "
            f"au sein de <b>{escape(settings.institution_name)}</b>."
        ),
        styles['body'],
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Le présent certificat est délivré à l'intéressé(e) pour servir et valoir ce que de droit.",
        styles['body'],
    ))
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph(f"Fait à Yaoundé, le {_format_date(issue_date)}", styles['signature']))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(escape(settings.institution_name), styles['signature']))

    document.build(
        story,
        onFirstPage=lambda pdf_canvas, doc: _draw_registration_certificate_footer(
            pdf_canvas,
            doc,
            settings.institution_name,
            official_document.reference,
        ),
        onLaterPages=lambda pdf_canvas, doc: _draw_registration_certificate_footer(
            pdf_canvas,
            doc,
            settings.institution_name,
            official_document.reference,
        ),
    )
    return buffer.getvalue()


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
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.4 * cm, bottomMargin=1.4 * cm)
    styles = _build_styles()
    story = _build_summary_header(student, styles)

    metadata = getattr(student, 'metadata', None)
    story.extend(_build_section('Informations personnelles', [
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
    ], styles))

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

    story.extend(_build_section('Informations académiques', [
        ('Programme', getattr(student.program, 'name', None)),
        ('École d\'origine', getattr(student.school, 'name', None)),
        ('Spécialités souhaitées', ' ; '.join(specialities) if specialities else None),
        ('Parrain', godfather_label),
        ('Niveaux d\'études d\'entrée', ' ; '.join(levels) if levels else None),
    ], styles))

    story.extend(_build_section(
        'Cursus scolaire et universitaire',
        _build_curriculum_rows(student),
        styles,
    ))

    family_rows = []
    address_rows = []
    dossier_rows = [('Dossier complet', 'Oui' if metadata and metadata.is_complete else 'Non')]
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

    story.extend(_build_section('Informations familiales', family_rows or [('Informations familiales', 'Non renseignées')], styles))
    story.extend(_build_section('Adresse', address_rows or [('Adresse', 'Non renseignée')], styles))

    annex_rows = []
    for annex in annex_entries:
        suffix = f" — {annex['details']}" if annex['details'] else ''
        filename = annex['filename'] or 'Aucun fichier'
        annex_rows.append((annex['label'], f"{filename} ({annex['status']}){suffix}"))

    story.extend(_build_section('Pièces jointes annexées au PDF', annex_rows, styles))
    story.extend(_build_section('État du dossier', dossier_rows, styles))

    document.build(story, onFirstPage=_draw_page_footer, onLaterPages=_draw_page_footer)
    return buffer.getvalue()


def _build_summary_header(student, styles):
    settings = SystemSettings.get_settings()
    logo_image = _build_logo_flowable(settings)

    header_elements = []
    if logo_image:
        header_elements.append(logo_image)
        header_elements.append(Spacer(1, 0.2 * cm))

    header_elements.extend([
        Paragraph('Fiche administrative de pré-inscription', styles['title']),
        Paragraph(f"Candidat : {escape(f'{student.firstname} {student.lastname}')}", styles['subtitle']),
    ])

    header_table = Table(
        [[
            header_elements,
            _build_profile_photo_cell(student, styles),
        ]],
        colWidths=[12.2 * cm, 4.2 * cm],
        hAlign='LEFT',
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [header_table, Spacer(1, 0.35 * cm)]


def _build_profile_photo_cell(student, styles):
    box_width = 3.2 * cm
    box_height = 4.0 * cm
    photo_content = _build_profile_photo_flowable(student, box_width - 0.35 * cm, box_height - 0.35 * cm)
    if photo_content is None:
        photo_content = Spacer(1, 0.1 * cm)

    photo_table = Table([[photo_content]], colWidths=[box_width], rowHeights=[box_height], hAlign='RIGHT')
    photo_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#9ca3af')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return photo_table


def _build_profile_photo_flowable(student, max_width, max_height):
    profile_photo = getattr(student, 'profile_photo', None)
    if not profile_photo:
        return None

    try:
        with profile_photo.open('rb') as image_file:
            image_bytes = image_file.read()
    except FileNotFoundError:
        return None

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size
            if not width or not height:
                return None

            scale = min(max_width / width, max_height / height)
            rendered = BytesIO()
            image.save(rendered, format='JPEG', quality=90)
            rendered.seek(0)
            return PlatypusImage(rendered, width=width * scale, height=height * scale)
    except (UnidentifiedImageError, OSError):
        return None


def _build_logo_flowable(settings, max_width=3.5 * cm, max_height=2.0 * cm):
    """Charge et redimensionne le logo de l'école pour le PDF."""
    try:
        logo_url = settings.get_logo_url()
        if not logo_url:
            return None

        # Télécharger l'image depuis l'URL
        if logo_url.startswith('http'):
            response = request.get(logo_url, timeout=5)
            response.raise_for_status()
            image_bytes = response.content
        else:
            # Si c'est un chemin local, le lire depuis le système de fichiers
            if hasattr(settings.logo, 'open'):
                with settings.logo.open('rb') as image_file:
                    image_bytes = image_file.read()
            else:
                return None

        with Image.open(BytesIO(image_bytes)) as image:
            # Convertir en RGB si nécessaire
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            width, height = image.size
            if not width or not height:
                return None

            # Redimensionner en respectant les proportions
            scale = min(max_width / width, max_height / height)
            rendered = BytesIO()
            image.save(rendered, format='JPEG', quality=90)
            rendered.seek(0)
            return PlatypusImage(rendered, width=width * scale, height=height * scale)
    except (UnidentifiedImageError, OSError, request.RequestException, Exception):
        return None


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


def _build_section(title, rows, styles):
    body_rows = [[Paragraph(f'<b>{escape(label)}</b>', styles['cell_label']), Paragraph(escape(_display_value(value)), styles['cell'])] for label, value in rows]
    table = Table(body_rows, colWidths=[5.2 * cm, 11.2 * cm], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#b5b5b5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d6d6d6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return [Paragraph(title, styles['section']), Spacer(1, 0.15 * cm), table, Spacer(1, 0.35 * cm)]


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


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='YsemTitle', parent=styles['Heading1'], fontSize=17, leading=21, textColor=colors.HexColor('#1f2937'), spaceAfter=6))
    styles.add(ParagraphStyle(name='YsemSubtitle', parent=styles['Normal'], fontSize=10, leading=13, textColor=colors.HexColor('#4b5563'), spaceAfter=4))
    styles.add(ParagraphStyle(name='YsemSection', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#111827'), spaceAfter=5, spaceBefore=6))
    styles.add(ParagraphStyle(name='YsemCell', parent=styles['Normal'], fontSize=9.2, leading=11))
    styles.add(ParagraphStyle(name='YsemCellLabel', parent=styles['Normal'], fontSize=9.2, leading=11))
    styles.add(ParagraphStyle(name='YsemTitleCentered', parent=styles['YsemTitle'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='YsemSubtitleCentered', parent=styles['YsemSubtitle'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='YsemCertificateTitle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=TA_CENTER, textColor=colors.HexColor('#111827'), spaceAfter=5))
    styles.add(ParagraphStyle(name='YsemCertificateReference', parent=styles['Normal'], fontSize=10.5, leading=13, alignment=TA_CENTER, textColor=colors.HexColor('#374151'), spaceAfter=6))
    styles.add(ParagraphStyle(name='YsemBody', parent=styles['Normal'], fontSize=11, leading=17, alignment=TA_JUSTIFY, textColor=colors.HexColor('#111827'), spaceAfter=6))
    styles.add(ParagraphStyle(name='YsemSignature', parent=styles['Normal'], fontSize=10.5, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor('#111827')))
    return {
        'title': styles['YsemTitle'],
        'title_centered': styles['YsemTitleCentered'],
        'subtitle': styles['YsemSubtitle'],
        'subtitle_centered': styles['YsemSubtitleCentered'],
        'section': styles['YsemSection'],
        'cell': styles['YsemCell'],
        'cell_label': styles['YsemCellLabel'],
        'certificate_title': styles['YsemCertificateTitle'],
        'certificate_reference': styles['YsemCertificateReference'],
        'body': styles['YsemBody'],
        'signature': styles['YsemSignature'],
    }


def _draw_page_footer(pdf_canvas, document):
    pdf_canvas.saveState()
    pdf_canvas.setFont('Helvetica', 8)
    pdf_canvas.setFillColor(colors.HexColor('#6b7280'))
    pdf_canvas.drawString(1.4 * cm, 1.0 * cm, 'YSEM — Dossier administratif de pré-inscription')
    pdf_canvas.drawRightString(A4[0] - 1.4 * cm, 1.0 * cm, f'Page {document.page}')
    pdf_canvas.restoreState()


def _draw_registration_certificate_footer(pdf_canvas, document, institution_name, reference):
    pdf_canvas.saveState()
    pdf_canvas.setFont('Helvetica', 8)
    pdf_canvas.setFillColor(colors.HexColor('#6b7280'))
    pdf_canvas.drawString(1.4 * cm, 1.0 * cm, f"{institution_name} — Certificat d'inscription généré à la demande")
    pdf_canvas.drawRightString(A4[0] - 1.4 * cm, 1.0 * cm, f"Réf. {reference or '-'} · Page {document.page}")
    pdf_canvas.restoreState()