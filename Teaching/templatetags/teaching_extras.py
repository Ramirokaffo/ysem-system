from django import template

register = template.Library()

@register.filter
def initials(value):
    """
    Extrait les initiales d'un nom complet.
    Exemple: "Jean Dupont" -> "JD"
    """
    if not value:
        return "??"
    
    # Diviser le nom en mots et prendre la première lettre de chaque mot
    words = value.strip().split()
    if len(words) == 0:
        return "??"
    elif len(words) == 1:
        # Si un seul mot, prendre les deux premières lettres
        return words[0][:2].upper()
    else:
        # Prendre la première lettre de chaque mot (max 2)
        initials_str = ''.join([word[0] for word in words[:2] if word])
        return initials_str.upper()

@register.filter
def evaluation_status(evaluation):
    """
    Détermine le statut global d'une évaluation.
    Retourne: 'positive', 'negative', ou 'mixed'
    """
    if not evaluation:
        return 'unknown'
    
    positive_count = 0
    total_count = 0
    
    # Compter les évaluations positives
    evaluations = [
        evaluation.support_cours_acessible,
        evaluation.bonne_explication_cours,
        evaluation.bonne_reponse_questions,
        evaluation.donne_TD,
        evaluation.donne_projet,
    ]
    
    for eval_item in evaluations:
        if eval_item is not None:
            total_count += 1
            if eval_item:
                positive_count += 1
    
    if total_count == 0:
        return 'unknown'
    
    # Calculer le pourcentage
    percentage = (positive_count / total_count) * 100
    
    if percentage >= 80:
        return 'positive'
    elif percentage >= 40:
        return 'mixed'
    else:
        return 'negative'

@register.filter
def evaluation_icon(evaluation):
    """
    Retourne l'icône appropriée pour le statut d'évaluation.
    """
    status = evaluation_status(evaluation)
    
    icons = {
        'positive': 'fas fa-thumbs-up text-success',
        'mixed': 'fas fa-minus-circle text-warning',
        'negative': 'fas fa-thumbs-down text-danger',
        'unknown': 'fas fa-question-circle text-muted'
    }
    
    return icons.get(status, icons['unknown'])

@register.filter
def evaluation_text(evaluation):
    """
    Retourne le texte approprié pour le statut d'évaluation.
    """
    status = evaluation_status(evaluation)
    
    texts = {
        'positive': 'Positive',
        'mixed': 'Mitigée',
        'negative': 'Négative',
        'unknown': 'Inconnue'
    }
    
    return texts.get(status, texts['unknown'])

@register.filter
def bool_icon(value):
    """
    Convertit une valeur booléenne en icône.
    """
    if value is True:
        return 'fas fa-check-circle text-success'
    elif value is False:
        return 'fas fa-times-circle text-danger'
    else:
        return 'fas fa-question-circle text-muted'

@register.filter
def bool_text(value):
    """
    Convertit une valeur booléenne en texte.
    """
    if value is True:
        return 'Oui'
    elif value is False:
        return 'Non'
    else:
        return 'Non renseigné'
