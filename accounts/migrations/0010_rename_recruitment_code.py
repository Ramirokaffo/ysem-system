# Generated manually to rename the module code recruitment -> lecturer_management.

from django.db import migrations


OLD_CODE = 'recruitment'
NEW_CODE = 'lecturer_management'

DEFAULTS = {
    'name': 'Gestion des enseignants',
    'description': 'Recrutement, validation des dossiers et gestion des enseignants.',
    'icon_class': 'fas fa-users-cog',
    'is_active': True,
}


def _switch_code(apps, old_code, new_code):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    BaseUser = apps.get_model('accounts', 'BaseUser')

    old = AccessModule.objects.filter(code=old_code).first()
    if old is None:
        return

    new, _ = AccessModule.objects.update_or_create(code=new_code, defaults=DEFAULTS)

    for user in BaseUser.objects.filter(accessible_modules=old):
        user.accessible_modules.add(new)
        user.accessible_modules.remove(old)

    BaseUser.objects.filter(last_accessed_module=old_code).update(
        last_accessed_module=new_code
    )

    old.delete()


def forward(apps, schema_editor):
    _switch_code(apps, OLD_CODE, NEW_CODE)


def backward(apps, schema_editor):
    _switch_code(apps, NEW_CODE, OLD_CODE)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_accessmodule_code_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
