from .models import SystemSettings


def institution_branding(request):
    try:
        system_settings = SystemSettings.get_settings()
        institution_name = system_settings.institution_name
        institution_logo_url = system_settings.get_logo_url()
        institution_logo_alt = system_settings.get_logo_alt()
    except Exception:
        system_settings = None
        institution_name = 'YSEM'
        institution_logo_url = '/static/main/images/ysemlogo.png'
        institution_logo_alt = 'Logo YSEM'

    return {
        'system_settings': system_settings,
        'institution_name': institution_name,
        'institution_logo_url': institution_logo_url,
        'institution_logo_alt': institution_logo_alt,
    }