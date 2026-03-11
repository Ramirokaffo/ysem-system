from django.db.models.signals import post_save
from django.dispatch import receiver

from academic.models import Program, ProgramDocumentRequirement


@receiver(post_save, sender=Program)
def create_program_document_requirement(sender, instance, created, **kwargs):
    if not created:
        return

    ProgramDocumentRequirement.objects.get_or_create(
        program=instance,
        defaults=ProgramDocumentRequirement.default_flags(),
    )