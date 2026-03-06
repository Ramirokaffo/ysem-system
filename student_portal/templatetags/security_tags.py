from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def is_student_session(context):
    """
    Template tag pour vérifier si la session actuelle est une session étudiant
    """
    request = context.get('request')
    if request:
        return request.session.get('student_authenticated', False)
    return False


@register.simple_tag(takes_context=True)
def is_admin_session(context):
    """
    Template tag pour vérifier si la session actuelle est une session admin
    """
    request = context.get('request')
    if request:
        return (request.user.is_authenticated and 
                not request.session.get('student_authenticated', False))
    return False


@register.inclusion_tag('student_portal/security_warning.html', takes_context=True)
def show_security_warning(context):
    """
    Template tag pour afficher un avertissement de sécurité si nécessaire
    """
    request = context.get('request')
    show_warning = False
    warning_message = ""
    
    if request:
        # Avertissement si un étudiant essaie d'accéder à une zone admin
        if (request.session.get('student_authenticated') and 
            any(request.path.startswith(path) for path in ['/admin/', '/scholar', '/etudiants/'])):
            show_warning = True
            warning_message = "Vous n'avez pas accès à cette section en tant qu'étudiant."
        
        # Avertissement si un admin accède au portail étudiant
        elif (request.user.is_authenticated and 
              request.path.startswith('/portail-etudiant/') and
              not request.session.get('student_authenticated')):
            show_warning = True
            warning_message = "Vous accédez au portail étudiant en tant qu'administrateur."
    
    return {
        'show_warning': show_warning,
        'warning_message': warning_message
    }
