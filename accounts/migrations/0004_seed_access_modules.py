# Generated manually to initialize module-based access.

from django.db import migrations


MODULES = {
    'scholar': {
        'name': 'Scolarité',
        'description': 'Gestion des inscriptions, étudiants et documents officiels.',
        'icon_class': 'fas fa-graduation-cap',
    },
    'teaching': {
        'name': 'Suivi des enseignements',
        'description': 'Gestion des enseignants, suivis de cours et évaluations.',
        'icon_class': 'fas fa-chalkboard-teacher',
    },
    'planning': {
        'name': 'Planification',
        'description': 'Gestion des salles, emplois du temps et séances.',
        'icon_class': 'fas fa-calendar-alt',
    },
    'prospection': {
        'name': 'Prospection',
        'description': 'Gestion des campagnes, agents et prospects.',
        'icon_class': 'fas fa-bullhorn',
    },
    'payments': {
        'name': 'Paiements',
        'description': 'Gestion des paiements, reçus et statuts financiers.',
        'icon_class': 'fas fa-money-check-alt',
    },
}

ROLE_MODULES = {
    'scholar': ['scholar'],
    'teaching': ['teaching'],
    'planning': ['planning'],
    'super_admin': list(MODULES.keys()),
    'student': [],
}


def seed_modules_and_migrate_roles(apps, schema_editor):
    AccessModule = apps.get_model('accounts', 'AccessModule')
    BaseUser = apps.get_model('accounts', 'BaseUser')

    module_objects = {}
    for code, payload in MODULES.items():
        module, _ = AccessModule.objects.update_or_create(
            code=code,
            defaults={**payload, 'is_active': True},
        )
        module_objects[code] = module

    for user in BaseUser.objects.all():
        codes = ROLE_MODULES.get(user.role or 'student', [])
        if not codes:
            continue
        user.accessible_modules.add(*(module_objects[code] for code in codes))
        if not user.last_accessed_module or user.last_accessed_module not in codes:
            user.last_accessed_module = codes[0]
            user.save(update_fields=['last_accessed_module'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_accessmodule_baseuser_last_accessed_module_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_modules_and_migrate_roles, migrations.RunPython.noop),
    ]
