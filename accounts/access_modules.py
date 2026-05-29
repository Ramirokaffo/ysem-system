"""Configuration centralisée des modules applicatifs internes."""

MODULE_SCHOLAR = 'scholar'
MODULE_TEACHING = 'teaching'
MODULE_PLANNING = 'planning'
MODULE_PROSPECTION = 'prospection'
MODULE_PAYMENTS = 'payments'
MODULE_LECTURER_MANAGEMENT = 'lecturer_management'

MODULE_CONFIG = {
    MODULE_SCHOLAR: {
        'label': 'Scolarité',
        'description': 'Gestion des inscriptions, étudiants et documents officiels.',
        'icon': 'fas fa-graduation-cap',
        'dashboard_url': 'main:dashboard',
        'path_prefixes': ['/scholar/', '/etudiants/'],
    },
    MODULE_TEACHING: {
        'label': 'Suivi des enseignements',
        'description': 'Gestion des enseignants, suivis de cours et évaluations.',
        'icon': 'fas fa-chalkboard-teacher',
        'dashboard_url': 'teaching:Teaching',
        'path_prefixes': ['/teach/'],
    },
    MODULE_PLANNING: {
        'label': 'Planification',
        'description': 'Gestion des salles, emplois du temps et séances.',
        'icon': 'fas fa-calendar-alt',
        'dashboard_url': 'planification:dashboard',
        'path_prefixes': ['/planning/'],
    },
    MODULE_PROSPECTION: {
        'label': 'Prospection',
        'description': 'Gestion des campagnes, agents et prospects.',
        'icon': 'fas fa-bullhorn',
        'dashboard_url': 'prospection:dashboard',
        'path_prefixes': ['/prospection/'],
    },
    # MODULE_PAYMENTS: {
    #     'label': 'Paiements',
    #     'description': 'Gestion des paiements, reçus et statuts financiers.',
    #     'icon': 'fas fa-money-check-alt',
    #     'dashboard_url': 'payments:payments_list',
    #     'path_prefixes': ['/paiements/'],
    # },
    MODULE_LECTURER_MANAGEMENT: {
        'label': 'Gestion des enseignants',
        'description': 'Recrutement, validation des dossiers et gestion des enseignants.',
        'icon': 'fas fa-users-cog',
        'dashboard_url': 'lecturers:home',
        'path_prefixes': ['/gestion-enseignants/'],
    },
}

MODULE_CHOICES = tuple((code, config['label']) for code, config in MODULE_CONFIG.items())
ALL_MODULE_CODES = tuple(MODULE_CONFIG.keys())

ROLE_MODULES_MAP = {
    'scholar': [MODULE_SCHOLAR],
    'teaching': [MODULE_TEACHING],
    'planning': [MODULE_PLANNING],
    'super_admin': list(ALL_MODULE_CODES),
    'student': [],
}


def get_module_for_path(path):
    """Retourne le code du module correspondant au chemin, ou None."""
    for code, config in MODULE_CONFIG.items():
        if any(path.startswith(prefix) for prefix in config['path_prefixes']):
            return code
    return None


def get_module_dashboard(code):
    config = MODULE_CONFIG.get(code) or {}
    return config.get('dashboard_url')


def get_module_label(code):
    config = MODULE_CONFIG.get(code) or {}
    return config.get('label', code)
