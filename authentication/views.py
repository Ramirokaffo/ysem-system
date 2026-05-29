from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from accounts.access_modules import MODULE_CONFIG, get_module_dashboard, get_module_for_path
from audit.utils import log_audit_event
from .models import LoginHistory, TwoFactorChallenge
from .services import record_login, record_logout
from .two_factor import (
    consume_challenge_by_code,
    consume_challenge_by_token,
    create_challenge,
    send_challenge_email,
    should_challenge_user,
)


User = get_user_model()
PENDING_2FA_SESSION_KEY = "pending_2fa"
PENDING_2FA_TOGGLE_SESSION_KEY = "pending_2fa_toggle"
CURRENT_MODULE_SESSION_KEY = "current_module"


def _set_last_accessed_module(request, user, module_code):
    """Mémorise le dernier module consulté en session et en base."""
    if module_code not in MODULE_CONFIG:
        return
    request.session[CURRENT_MODULE_SESSION_KEY] = module_code
    if getattr(user, 'last_accessed_module', None) != module_code:
        user.last_accessed_module = module_code
        user.save(update_fields=['last_accessed_module'])


def _redirect_to_module(request, user, module_code):
    dashboard_url = get_module_dashboard(module_code)
    if not dashboard_url:
        return redirect('authentication:select_module')
    _set_last_accessed_module(request, user, module_code)
    return redirect(dashboard_url)


def _redirect_after_authentication(request, user, next_url=''):
    """Redirige après connexion selon les modules accessibles."""
    if next_url:
        if user_can_access_url(user, next_url):
            module_code = get_module_for_path(next_url)
            if module_code:
                _set_last_accessed_module(request, user, module_code)
            return redirect(next_url)
        messages.warning(
            request,
            "Redirection vers vos modules. Vous n'avez pas accès à la page demandée."
        )

    module_codes = user.get_accessible_module_codes()
    if not module_codes:
        return redirect('authentication:select_module')
    if len(module_codes) == 1:
        return _redirect_to_module(request, user, module_codes[0])
    return redirect('authentication:select_module')


@never_cache
@csrf_protect
def login_view(request):
    """
    Vue de connexion personnalisée
    """
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return _redirect_after_authentication(request, request.user, request.GET.get('next') or '')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    next_url = request.GET.get('next') or ''
                    if should_challenge_user(request, user):
                        challenge, code = create_challenge(
                            request,
                            user,
                            purpose=TwoFactorChallenge.PURPOSE_LOGIN,
                            next_url=next_url,
                        )
                        sent = send_challenge_email(request, challenge, code)
                        request.session[PENDING_2FA_SESSION_KEY] = {
                            'challenge_id': challenge.pk,
                            'user_id': user.pk,
                            'next_url': next_url,
                        }
                        log_audit_event(
                            category='auth',
                            action='login_failed',
                            actor=user,
                            instance=user,
                            context={
                                'channel': 'web',
                                'reason': 'two_factor_required',
                                'email_sent': sent,
                            },
                            message='Connexion en attente de vérification 2FA.',
                        )
                        if sent:
                            messages.info(
                                request,
                                "Un code de vérification vous a été envoyé par email."
                            )
                        else:
                            messages.warning(
                                request,
                                "Impossible d'envoyer l'email de vérification. "
                                "Contactez l'administrateur."
                            )
                        return redirect('authentication:two_factor_login_challenge')

                    return _finalize_login(request, user, request.GET.get('next') or '')
                else:
                    record_login(
                        request,
                        actor_type='user',
                        user=user,
                        actor_id=user.pk,
                        actor_identifier=username or '',
                        actor_display=user.get_full_name() or user.username,
                        channel='web',
                        status=LoginHistory.STATUS_FAILED,
                        failure_reason='inactive_account',
                    )
                    log_audit_event(
                        category='auth',
                        action='login_failed',
                        context={'channel': 'web', 'reason': 'inactive_account'},
                        message='Tentative de connexion sur un compte désactivé.',
                        actor_identifier=username or '',
                    )
                    messages.error(request, 'Votre compte est désactivé.')
            else:
                record_login(
                    request,
                    actor_type='anonymous',
                    actor_identifier=username or '',
                    channel='web',
                    status=LoginHistory.STATUS_FAILED,
                    failure_reason='invalid_credentials',
                )
                log_audit_event(
                    category='auth',
                    action='login_failed',
                    context={'channel': 'web', 'reason': 'invalid_credentials'},
                    message='Échec de connexion web.',
                    actor_identifier=username or '',
                )
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    return render(request, 'authentication/login.html')


@login_required
def logout_view(request):
    """
    Vue de déconnexion
    """
    user = request.user
    session_key = request.session.session_key or ''
    log_audit_event(
        category='auth',
        action='logout',
        actor=user,
        instance=user,
        context={'channel': 'web'},
        message='Déconnexion web.',
    )
    record_logout(session_key=session_key, user=user)
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('authentication:login')


def user_can_access_url(user, url):
    """
    Vérifie si un utilisateur peut accéder à une URL donnée via ses modules.
    """
    if not url.startswith('/'):
        return False
    if url.startswith(('/auth/', '/admin/')):
        return True
    module_code = get_module_for_path(url)
    return bool(module_code and user.has_module_access(module_code))


@never_cache
@csrf_protect
@login_required
def select_module_view(request):
    """Page de choix du module lorsque l'utilisateur a plusieurs accès."""
    module_codes = request.user.get_accessible_module_codes()
    # if not module_codes:
    #     return redirect('student_portal:login')
    if len(module_codes) == 1:
        return _redirect_to_module(request, request.user, module_codes[0])

    if request.method == 'POST':
        module_code = request.POST.get('module') or ''
        if request.user.has_module_access(module_code):
            return _redirect_to_module(request, request.user, module_code)
        messages.error(request, "Vous n'avez pas accès au module demandé.")

    modules = request.user.get_accessible_modules_data()
    return render(request, 'authentication/select_module.html', {
        'modules': modules,
        'last_accessed_module': request.user.last_accessed_module,
    })


def _finalize_login(request, user, next_url):
    """Finalise une connexion authentifiée : ouvre la session, journalise, redirige."""
    login(request, user)
    record_login(
        request,
        actor_type='user',
        user=user,
        actor_id=user.pk,
        actor_identifier=user.username,
        actor_display=user.get_full_name() or user.username,
        channel='web',
        session_key=request.session.session_key or '',
    )
    log_audit_event(
        category='auth',
        action='login',
        actor=user,
        instance=user,
        context={'channel': 'web'},
        message='Connexion web réussie.',
    )

    return _redirect_after_authentication(request, user, next_url)


def _load_pending_challenge(request, session_key, purpose):
    """Récupère le défi 2FA en cours pour la session, ou None."""
    payload = request.session.get(session_key) or {}
    challenge_id = payload.get('challenge_id')
    if not challenge_id:
        return None, None
    try:
        challenge = TwoFactorChallenge.objects.select_related('user').get(
            pk=challenge_id, purpose=purpose
        )
    except TwoFactorChallenge.DoesNotExist:
        return None, payload
    return challenge, payload


@never_cache
@csrf_protect
def two_factor_login_challenge_view(request):
    """Affiche le formulaire de saisie du code 2FA pour finaliser la connexion."""
    challenge, payload = _load_pending_challenge(
        request, PENDING_2FA_SESSION_KEY, TwoFactorChallenge.PURPOSE_LOGIN
    )
    if challenge is None:
        messages.error(request, "Aucune demande de vérification en cours.")
        return redirect('authentication:login')

    user = challenge.user
    next_url = (payload or {}).get('next_url') or ''

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')
        if action == 'resend':
            if challenge.is_consumed():
                messages.error(request, "Ce défi a déjà été utilisé.")
            else:
                new_challenge, code = create_challenge(
                    request,
                    user,
                    purpose=TwoFactorChallenge.PURPOSE_LOGIN,
                    next_url=next_url,
                )
                sent = send_challenge_email(request, new_challenge, code)
                request.session[PENDING_2FA_SESSION_KEY] = {
                    'challenge_id': new_challenge.pk,
                    'user_id': user.pk,
                    'next_url': next_url,
                }
                if sent:
                    messages.info(request, "Un nouveau code vous a été envoyé.")
                else:
                    messages.warning(request, "Impossible d'envoyer un nouveau code.")
            return redirect('authentication:two_factor_login_challenge')

        code = (request.POST.get('code') or '').strip()
        ok, reason = consume_challenge_by_code(challenge, code)
        if ok:
            request.session.pop(PENDING_2FA_SESSION_KEY, None)
            return _finalize_login(request, user, next_url)

        if reason == 'invalid_code':
            messages.error(request, "Code incorrect.")
        elif reason == 'expired':
            messages.error(request, "Ce code a expiré. Demandez-en un nouveau.")
        elif reason == 'locked':
            messages.error(request, "Trop de tentatives. Demandez un nouveau code.")
        elif reason == 'already_consumed':
            messages.error(request, "Ce code a déjà été utilisé.")
        log_audit_event(
            category='auth',
            action='login_failed',
            actor=user,
            instance=user,
            context={'channel': 'web', 'reason': f'two_factor_{reason}'},
            message='Échec de vérification 2FA.',
        )

    context = {
        'user_email': user.email,
        'expires_at': challenge.expires_at,
        'attempts_left': max(0, 5 - (challenge.attempts or 0)),
        'purpose': 'login',
    }
    return render(request, 'authentication/two_factor_verify.html', context)


@never_cache
def two_factor_login_confirm_link_view(request, token):
    """Valide la connexion via le lien direct contenu dans l'email."""
    challenge, status = consume_challenge_by_token(token, TwoFactorChallenge.PURPOSE_LOGIN)
    if challenge is None:
        messages.error(request, "Lien de vérification invalide.")
        return redirect('authentication:login')
    if status == 'expired':
        messages.error(request, "Ce lien de vérification a expiré.")
        return redirect('authentication:login')
    if status == 'already_consumed':
        messages.error(request, "Ce lien a déjà été utilisé.")
        return redirect('authentication:login')

    pending = request.session.get(PENDING_2FA_SESSION_KEY) or {}
    next_url = pending.get('next_url') or ''
    request.session.pop(PENDING_2FA_SESSION_KEY, None)
    return _finalize_login(request, challenge.user, next_url)


@login_required
def roles_info_view(request):
    """
    Vue pour afficher les informations sur les modules et permissions
    Accessible uniquement aux super administrateurs
    """
    # Vérifier que l'utilisateur est un super administrateur
    if not request.user.is_superuser:
        messages.error(
            request,
            "Accès interdit. Cette page est réservée aux super administrateurs."
        )
        return _redirect_after_authentication(request, request.user)

    context = {
        'page_title': 'Gestion des Modules et Permissions',
        'current_user_modules': request.user.get_accessible_modules_data(),
        'modules': MODULE_CONFIG,
    }

    return render(request, 'authentication/roles_info.html', context)



@never_cache
@csrf_protect
@login_required
@require_http_methods(["POST"])
def two_factor_toggle_init_view(request):
    """Initie l'activation/désactivation de la 2FA après re-saisie du mot de passe."""
    user = request.user
    if not getattr(user, 'two_factor_user_can_manage', True):
        messages.error(
            request,
            "Vous n'êtes pas autorisé à modifier votre double authentification. "
            "Contactez l'administrateur."
        )
        return redirect('main:profil')

    password = request.POST.get('password') or ''
    if not user.check_password(password):
        messages.error(request, "Mot de passe incorrect.")
        return redirect('main:profil')

    if not (getattr(user, 'email', '') or '').strip():
        messages.error(
            request,
            "Aucune adresse email n'est associée à votre compte. "
            "Impossible d'activer la double authentification."
        )
        return redirect('main:profil')

    requested_state = not bool(getattr(user, 'two_factor_enabled', False))
    challenge, code = create_challenge(
        request,
        user,
        purpose=TwoFactorChallenge.PURPOSE_TOGGLE,
        requested_state=requested_state,
    )
    sent = send_challenge_email(request, challenge, code)
    request.session[PENDING_2FA_TOGGLE_SESSION_KEY] = {
        'challenge_id': challenge.pk,
        'requested_state': requested_state,
    }
    log_audit_event(
        category='auth',
        action='update',
        actor=user,
        instance=user,
        context={
            'change': 'two_factor_toggle_requested',
            'requested_state': requested_state,
            'email_sent': sent,
        },
        message='Demande de modification du statut 2FA.',
    )
    if sent:
        messages.info(
            request,
            "Un code de confirmation vous a été envoyé par email."
        )
    else:
        messages.warning(
            request,
            "Impossible d'envoyer l'email de confirmation. Contactez l'administrateur."
        )
    return redirect('authentication:two_factor_toggle_verify')


def _apply_toggle(request, challenge):
    """Applique le changement de statut 2FA puis déconnecte l'utilisateur."""
    user = challenge.user
    new_state = bool(challenge.requested_state)
    user.two_factor_enabled = new_state
    user.save(update_fields=['two_factor_enabled'])
    log_audit_event(
        category='auth',
        action='update',
        actor=user,
        instance=user,
        context={
            'change': 'two_factor_toggle_confirmed',
            'new_state': new_state,
        },
        message='Statut 2FA mis à jour.',
    )
    session_key = request.session.session_key or ''
    record_logout(session_key=session_key, user=user)
    logout(request)
    if new_state:
        messages.success(
            request,
            "Double authentification activée. Reconnectez-vous pour appliquer le changement."
        )
    else:
        messages.success(
            request,
            "Double authentification désactivée. Reconnectez-vous pour appliquer le changement."
        )


@never_cache
@csrf_protect
@login_required
def two_factor_toggle_verify_view(request):
    """Saisie du code pour confirmer la modification du statut 2FA."""
    challenge, _payload = _load_pending_challenge(
        request, PENDING_2FA_TOGGLE_SESSION_KEY, TwoFactorChallenge.PURPOSE_TOGGLE
    )
    if challenge is None or challenge.user_id != request.user.pk:
        messages.error(request, "Aucune demande de modification en cours.")
        return redirect('main:profil')

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        ok, reason = consume_challenge_by_code(challenge, code)
        if ok:
            request.session.pop(PENDING_2FA_TOGGLE_SESSION_KEY, None)
            _apply_toggle(request, challenge)
            return redirect('authentication:login')

        if reason == 'invalid_code':
            messages.error(request, "Code incorrect.")
        elif reason == 'expired':
            messages.error(request, "Ce code a expiré. Recommencez l'opération.")
        elif reason == 'locked':
            messages.error(request, "Trop de tentatives. Recommencez l'opération.")
        elif reason == 'already_consumed':
            messages.error(request, "Ce code a déjà été utilisé.")

    context = {
        'user_email': request.user.email,
        'expires_at': challenge.expires_at,
        'attempts_left': max(0, 5 - (challenge.attempts or 0)),
        'purpose': 'toggle',
        'requested_state': bool(challenge.requested_state),
    }
    return render(request, 'authentication/two_factor_verify.html', context)


@never_cache
@login_required
def two_factor_toggle_confirm_link_view(request, token):
    """Confirme la modification 2FA via le lien direct contenu dans l'email."""
    challenge, status = consume_challenge_by_token(token, TwoFactorChallenge.PURPOSE_TOGGLE)
    if challenge is None:
        messages.error(request, "Lien de confirmation invalide.")
        return redirect('main:profil')
    if challenge.user_id != request.user.pk:
        messages.error(request, "Ce lien ne correspond pas à votre compte.")
        return redirect('main:profil')
    if status == 'expired':
        messages.error(request, "Ce lien de confirmation a expiré.")
        return redirect('main:profil')
    if status == 'already_consumed':
        messages.error(request, "Ce lien a déjà été utilisé.")
        return redirect('main:profil')

    request.session.pop(PENDING_2FA_TOGGLE_SESSION_KEY, None)
    _apply_toggle(request, challenge)
    return redirect('authentication:login')
