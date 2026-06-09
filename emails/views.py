from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache

from .forms import ComposeEmailForm
from .services import send_composed_email


@never_cache
@login_required
def compose_email(request):
    """Vue universelle de composition et d'envoi d'un email.

    Les destinataires et l'objet peuvent être pré-remplis via les paramètres
    GET ``recipients`` et ``subject``. Le paramètre ``next`` permet de revenir
    à la page d'origine après l'envoi.
    """
    next_url = request.POST.get('next') or request.GET.get('next', '')
    safe_next = next_url if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ) else ''

    if request.method == 'POST':
        form = ComposeEmailForm(request.POST)
        if form.is_valid():
            success, failure = send_composed_email(
                subject=form.cleaned_data['subject'],
                html_body=form.cleaned_data['body'],
                recipients=form.cleaned_data['recipients'],
                request=request,
                sender=request.user if request.user.is_authenticated else None,
            )
            if success:
                messages.success(request, f"Email envoyé à {success} destinataire(s).")
            if failure:
                messages.error(request, f"Échec de l'envoi pour {failure} destinataire(s).")
            return redirect(safe_next or 'emails:compose')
    else:
        form = ComposeEmailForm(initial={
            'recipients': request.GET.get('recipients', ''),
            'subject': request.GET.get('subject', ''),
        })

    context = {
        'form': form,
        'next': safe_next,
        'recipient_label': request.GET.get('recipient_label', ''),
    }
    return render(request, 'emails/compose.html', context)
