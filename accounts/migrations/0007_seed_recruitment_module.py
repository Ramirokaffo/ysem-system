# Generated manually to add the teacher recruitment access module.

from django.db import migrations


MODULE_CODE = 'recruitment'
MODULE_DEFAULTS = {
    'name': 'Recrutement des enseignants',
    'description': 'Suivi des candidatures, validation des dossiers et des cours proposés.',
    'icon_class': 'fas fa-user-tie',
    'is_active': True,
}


def seed_recruitment_module(apps, schema_editor):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    AccessModule.objects.update_or_create(code=MODULE_CODE, defaults=MODULE_DEFAULTS)


def remove_recruitment_module(apps, schema_editor):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    AccessModule.objects.filter(code=MODULE_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_accessmodule_code_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_recruitment_module, remove_recruitment_module),
    ]
