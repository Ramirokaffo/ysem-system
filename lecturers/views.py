from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from .decorators import (
    SESSION_AUTH_KEY,
    SESSION_LECTURER_EMAIL,
    SESSION_LECTURER_ID,
    SESSION_LECTURER_NAME,
    lecturer_required,
)
from .emails import send_activation_email, send_password_reset_email
from .forms import (
    LecturerLoginForm,
    LecturerSignupForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ResendActivationForm,
)
from .models import Lecturer
from .tokens import (
    make_activation_token,
    make_password_reset_token,
    validate_activation_token,
    validate_password_reset_token,
)


def _establish_lecturer_session(request, lecturer):
    request.session[SESSION_AUTH_KEY] = True
    request.session[SESSION_LECTURER_ID] = lecturer.pk
    request.session[SESSION_LECTURER_EMAIL] = lecturer.email or ''
    request.session[SESSION_LECTURER_NAME] = (
        f"{lecturer.firstname or ''} {lecturer.lastname or ''}".strip()
    )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class LecturerLoginView(View):
    template_name = 'lecturers/login.html'

    def get(self, request):
        if request.session.get(SESSION_AUTH_KEY):
            return redirect('lecturers:dashboard')
        return render(request, self.template_name, {'form': LecturerLoginForm()})

    def post(self, request):
        form = LecturerLoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        lecturer = Lecturer.objects.filter(email__iexact=email).first()
        if not lecturer or not lecturer.check_external_password(password):
            messages.error(request, "Adresse e-mail ou mot de passe incorrect.")
            return render(request, self.template_name, {'form': form})

        if not lecturer.email_verified:
            messages.error(
                request,
                "Votre compte n'est pas encore activé. Vérifiez votre boîte "
                "mail ou demandez un nouveau lien d'activation."
            )
            return redirect('lecturers:resend_activation')

        lecturer.last_login_date = timezone.now()
        lecturer.save(update_fields=['last_login_date'])
        _establish_lecturer_session(request, lecturer)
        messages.success(request, f"Bienvenue {lecturer.firstname} !")
        return redirect('lecturers:dashboard')


@method_decorator([never_cache, csrf_protect], name='dispatch')
class LecturerSignupView(View):
    template_name = 'lecturers/signup.html'

    def get(self, request):
        if request.session.get(SESSION_AUTH_KEY):
            return redirect('lecturers:dashboard')
        return render(request, self.template_name, {'form': LecturerSignupForm()})

    def post(self, request):
        form = LecturerSignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        with transaction.atomic():
            lecturer = Lecturer(
                firstname=form.cleaned_data['firstname'],
                lastname=form.cleaned_data['lastname'],
                email=form.cleaned_data['email'],
                email_verified=False,
            )
            # Le matricule est généré automatiquement dans Lecturer.save().
            lecturer.save()
            lecturer.set_external_password(form.cleaned_data['password'])

        token = make_activation_token(lecturer)
        send_activation_email(lecturer, token, request=request)

        return render(
            request,
            'lecturers/activation_sent.html',
            {'email': lecturer.email, 'lecturer': lecturer},
        )


def lecturer_logout(request):
    for key in (
        SESSION_AUTH_KEY,
        SESSION_LECTURER_ID,
        SESSION_LECTURER_EMAIL,
        SESSION_LECTURER_NAME,
    ):
        request.session.pop(key, None)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('lecturers:login')


@method_decorator([never_cache, lecturer_required], name='dispatch')
class LecturerDashboardView(View):
    template_name = 'lecturers/dashboard.html'

    def get(self, request):
        lecturer = Lecturer.objects.filter(
            pk=request.session.get(SESSION_LECTURER_ID)
        ).first()
        if not lecturer:
            return redirect('lecturers:logout')
        return render(request, self.template_name, {'lecturer': lecturer})


@method_decorator([never_cache], name='dispatch')
class EmailActivationView(View):
    """Active le compte de l'enseignant à partir d'un token signé."""

    def get(self, request, token):
        matricule = validate_activation_token(token)
        if not matricule:
            return render(request, 'lecturers/activation_invalid.html', status=400)

        lecturer = Lecturer.objects.filter(pk=matricule).first()
        if not lecturer:
            return render(request, 'lecturers/activation_invalid.html', status=400)

        if not lecturer.email_verified:
            lecturer.email_verified = True
            lecturer.email_verified_at = timezone.now()
            lecturer.save(update_fields=['email_verified', 'email_verified_at'])

        return render(request, 'lecturers/activation_done.html', {'lecturer': lecturer})


@method_decorator([never_cache, csrf_protect], name='dispatch')
class ResendActivationView(View):
    template_name = 'lecturers/resend_activation.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ResendActivationForm()})

    def post(self, request):
        form = ResendActivationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        lecturer = Lecturer.objects.filter(email__iexact=email).first()
        if lecturer and not lecturer.email_verified:
            token = make_activation_token(lecturer)
            send_activation_email(lecturer, token, request=request)

        # Réponse uniforme pour ne pas révéler l'existence ou non du compte
        return render(
            request,
            'lecturers/activation_sent.html',
            {'email': email, 'resent': True},
        )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class PasswordResetRequestView(View):
    template_name = 'lecturers/password_reset_request.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        lecturer = Lecturer.objects.filter(email__iexact=email).first()
        if lecturer and lecturer.has_external_password():
            token = make_password_reset_token(lecturer)
            send_password_reset_email(lecturer, token, request=request)

        return render(
            request,
            'lecturers/password_reset_sent.html',
            {'email': email},
        )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class PasswordResetConfirmView(View):
    template_name = 'lecturers/password_reset_confirm.html'

    def _resolve_lecturer(self, token):
        result = validate_password_reset_token(token)
        if result is None:
            return None
        matricule, password_hash = result
        lecturer = Lecturer.objects.filter(pk=matricule).first()
        if not lecturer:
            return None
        if (lecturer.external_password_hash or '') != password_hash:
            return None
        return lecturer

    def get(self, request, token):
        lecturer = self._resolve_lecturer(token)
        if not lecturer:
            return render(request, 'lecturers/password_reset_invalid.html', status=400)
        return render(request, self.template_name, {
            'form': PasswordResetConfirmForm(),
            'token': token,
            'lecturer': lecturer,
        })

    def post(self, request, token):
        lecturer = self._resolve_lecturer(token)
        if not lecturer:
            return render(request, 'lecturers/password_reset_invalid.html', status=400)

        form = PasswordResetConfirmForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'token': token,
                'lecturer': lecturer,
            })

        lecturer.set_external_password(form.cleaned_data['password'])
        # Le reset confirme implicitement la possession de l'adresse mail.
        if not lecturer.email_verified:
            lecturer.email_verified = True
            lecturer.email_verified_at = timezone.now()
            lecturer.save(update_fields=['email_verified', 'email_verified_at'])

        return render(request, 'lecturers/password_reset_done.html', {'lecturer': lecturer})
