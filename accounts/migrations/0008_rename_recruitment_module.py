# Generated manually to rebrand the recruitment module as lecturer management.

from django.db import migrations


MODULE_CODE = 'recruitment'

NEW_DEFAULTS = {
    'name': 'Gestion des enseignants',
    'description': 'Recrutement, validation des dossiers et gestion des enseignants.',
    'icon_class': 'fas fa-users-cog',
    'is_active': True,
}

OLD_DEFAULTS = {
    'name': 'Recrutement des enseignants',
    'description': 'Suivi des candidatures, validation des dossiers et des cours proposés.',
    'icon_class': 'fas fa-user-tie',
    'is_active': True,
}


def rebrand_forward(apps, schema_editor):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    AccessModule.objects.update_or_create(code=MODULE_CODE, defaults=NEW_DEFAULTS)


def rebrand_backward(apps, schema_editor):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    AccessModule.objects.update_or_create(code=MODULE_CODE, defaults=OLD_DEFAULTS)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_seed_recruitment_module'),
    ]

    operations = [
        migrations.RunPython(rebrand_forward, rebrand_backward),
    ]
