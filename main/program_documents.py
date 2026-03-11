import os

from academic.document_requirements import (
    DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS,
    PROGRAM_DOCUMENTS,
)
from academic.models import ProgramDocumentRequirement


def get_required_program_document_field_names(program=None):
    configuration = ProgramDocumentRequirement.get_for_program(program)
    if not configuration:
        return []
    return list(configuration.get_required_document_fields())


def build_program_document_entries(program=None, metadata=None, fallback_visible_fields=None, force_optional=False):
    required_field_names = set(get_required_program_document_field_names(program))
    visible_field_names = set(required_field_names)

    if fallback_visible_fields:
        visible_field_names.update(fallback_visible_fields)

    entries = []
    for document in PROGRAM_DOCUMENTS:
        field_name = document['field_name']
        current_file = getattr(metadata, field_name, None) if metadata else None
        current_file_name = os.path.basename(current_file.name) if getattr(current_file, 'name', '') else ''
        has_file = bool(current_file_name)

        entries.append({
            **document,
            'is_required': False if force_optional else field_name in required_field_names,
            'should_display': field_name in visible_field_names or has_file,
            'current_file': current_file,
            'current_file_name': current_file_name,
            'has_file': has_file,
        })

    return entries


def build_program_document_payload(
    program=None,
    fallback_visible_fields=DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS,
    force_optional=False,
):
    return [
        {
            'field_name': entry['field_name'],
            'label': entry['label'],
            'help_text': entry['help_text'],
            'is_required': entry['is_required'],
            'should_display': entry['should_display'],
        }
        for entry in build_program_document_entries(
            program=program,
            fallback_visible_fields=fallback_visible_fields,
            force_optional=force_optional,
        )
    ]