from io import BytesIO
import os
from xml.sax.saxutils import escape

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ANNEX_FIELD_DEFINITIONS = [
    ('student', 'profile_photo'),
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
    story = [
        Paragraph('Fiche administrative de pré-inscription', styles['title']),
        Paragraph(f"Candidat : {escape(f'{student.firstname} {student.lastname}')}", styles['subtitle']),
        Spacer(1, 0.35 * cm),
    ]

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
        ('Date d\'inscription', _format_datetime(student.created_at)),
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
        ('Parrain', godfather_label),
        ('Niveaux d\'études', ' ; '.join(levels) if levels else None),
        ('Spécialités souhaitées', ' ; '.join(specialities) if specialities else None),
    ], styles))

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
    return {
        'title': styles['YsemTitle'],
        'subtitle': styles['YsemSubtitle'],
        'section': styles['YsemSection'],
        'cell': styles['YsemCell'],
        'cell_label': styles['YsemCellLabel'],
    }


def _draw_page_footer(pdf_canvas, document):
    pdf_canvas.saveState()
    pdf_canvas.setFont('Helvetica', 8)
    pdf_canvas.setFillColor(colors.HexColor('#6b7280'))
    pdf_canvas.drawString(1.4 * cm, 1.0 * cm, 'YSEM — Dossier administratif de pré-inscription')
    pdf_canvas.drawRightString(A4[0] - 1.4 * cm, 1.0 * cm, f'Page {document.page}')
    pdf_canvas.restoreState()