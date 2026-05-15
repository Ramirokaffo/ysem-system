from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from students.models import Student, StudentMetaData

from .decorators import (
    SESSION_AUTH_KEY,
    SESSION_STUDENT_EMAIL,
    SESSION_STUDENT_ID,
    SESSION_STUDENT_NAME,
    candidate_required,
)
from .emails import send_activation_email, send_password_reset_email
from .forms import (
    AdmissionLoginForm,
    AdmissionSignupForm,
    ChangePasswordForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ResendActivationForm,
)
from .tokens import (
    make_activation_token,
    make_password_reset_token,
    validate_activation_token,
    validate_password_reset_token,
)


def _generate_candidate_matricule():
    """Génère un matricule unique pour un candidat du portail d'admission."""
    year = timezone.now().year
    prefix = f"CAND-{year}-"
    last = (
        Student.objects.filter(matricule__startswith=prefix)
        .order_by('-matricule')
        .values_list('matricule', flat=True)
        .first()
    )
    try:
        last_number = int(last.split('-')[-1]) if last else 0
    except (ValueError, AttributeError):
        last_number = 0
    return f"{prefix}{last_number + 1:05d}"


def _establish_candidate_session(request, student):
    request.session[SESSION_AUTH_KEY] = True
    request.session[SESSION_STUDENT_ID] = student.pk
    request.session[SESSION_STUDENT_EMAIL] = student.email or ''
    request.session[SESSION_STUDENT_NAME] = f"{student.firstname} {student.lastname}".strip()


@method_decorator([never_cache, csrf_protect], name='dispatch')
class AdmissionLoginView(View):
    template_name = 'admissions/login.html'

    def get(self, request):
        if request.session.get(SESSION_AUTH_KEY):
            return redirect('admissions:dashboard')
        return render(request, self.template_name, {'form': AdmissionLoginForm()})

    def post(self, request):
        form = AdmissionLoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        student = Student.objects.filter(email__iexact=email).first()
        if not student or not student.check_external_password(password):
            messages.error(request, "Adresse e-mail ou mot de passe incorrect.")
            return render(request, self.template_name, {'form': form})

        if not student.email_verified:
            messages.error(
                request,
                "Votre compte n'est pas encore activé. Vérifiez votre boîte "
                "mail ou demandez un nouveau lien d'activation."
            )
            return redirect('admissions:resend_activation')

        student.last_login_date = timezone.now()
        student.save(update_fields=['last_login_date'])
        _establish_candidate_session(request, student)
        messages.success(request, f"Bienvenue {student.firstname} !")
        return redirect('admissions:dashboard')


@method_decorator([never_cache, csrf_protect], name='dispatch')
class AdmissionSignupView(View):
    template_name = 'admissions/signup.html'

    def get(self, request):
        if request.session.get(SESSION_AUTH_KEY):
            return redirect('admissions:dashboard')
        return render(request, self.template_name, {'form': AdmissionSignupForm()})

    def post(self, request):
        form = AdmissionSignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        with transaction.atomic():
            metadata = StudentMetaData.objects.create(
                original_country='',
                is_online_registration=True,
            )
            student = Student.objects.create(
                matricule=_generate_candidate_matricule(),
                firstname=form.cleaned_data['firstname'],
                lastname=form.cleaned_data['lastname'],
                email=form.cleaned_data['email'],
                status='pending',
                metadata=metadata,
                email_verified=False,
            )
            student.set_external_password(form.cleaned_data['password'])

        token = make_activation_token(student)
        send_activation_email(student, token, request=request)

        return render(
            request,
            'admissions/activation_sent.html',
            {'email': student.email, 'student': student},
        )


def admission_logout(request):
    for key in (
        SESSION_AUTH_KEY,
        SESSION_STUDENT_ID,
        SESSION_STUDENT_EMAIL,
        SESSION_STUDENT_NAME,
    ):
        request.session.pop(key, None)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('admissions:login')


@method_decorator([never_cache, csrf_protect, candidate_required], name='dispatch')
class ChangePasswordView(View):
    """Permet à un candidat connecté de changer son mot de passe."""
    template_name = 'admissions/change_password.html'

    def _get_student(self, request):
        return Student.objects.filter(pk=request.session.get(SESSION_STUDENT_ID)).first()

    def get(self, request):
        student = self._get_student(request)
        if not student:
            return redirect('admissions:logout')
        return render(request, self.template_name, {
            'form': ChangePasswordForm(student=student),
            'student': student,
        })

    def post(self, request):
        student = self._get_student(request)
        if not student:
            return redirect('admissions:logout')

        form = ChangePasswordForm(request.POST, student=student)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'student': student,
            })

        student.set_external_password(form.cleaned_data['password'])
        messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
        return redirect('admissions:dashboard')


@method_decorator([never_cache, candidate_required], name='dispatch')
class AdmissionDashboardView(View):
    template_name = 'admissions/dashboard.html'

    # Étapes du wizard, alignées sur preinscription_views.TOTAL_STEPS
    TOTAL_PREINSCRIPTION_STEPS = 4
    STEP_TITLES = {
        1: "Identification du candidat",
        2: "Informations familiales",
        3: "Cursus et programme",
        3: "Pièces justificatives",

    }

    def get(self, request):
        student = (
            Student.objects
            .filter(pk=request.session.get(SESSION_STUDENT_ID))
            .select_related('metadata')
            .first()
        )
        if not student:
            return redirect('admissions:logout')

        is_submitted = bool(student.metadata and student.metadata.is_complete)
        current_step = student.preinscription_step or 0
        next_step = min(current_step + 1, self.TOTAL_PREINSCRIPTION_STEPS)
        percent = int(round(100 * current_step / self.TOTAL_PREINSCRIPTION_STEPS)) if not is_submitted else 100

        context = {
            'student': student,
            'preinscription': {
                'is_submitted': is_submitted,
                'is_started': current_step > 0,
                'current_step': current_step,
                'next_step': next_step,
                'total_steps': self.TOTAL_PREINSCRIPTION_STEPS,
                'percent': percent,
                'next_step_title': self.STEP_TITLES.get(next_step, ''),
            },
        }
        return render(request, self.template_name, context)



@method_decorator([never_cache], name='dispatch')
class EmailActivationView(View):
    """Active le compte du candidat à partir d'un token signé."""

    def get(self, request, token):
        student_id = validate_activation_token(token)
        if student_id is None:
            return render(request, 'admissions/activation_invalid.html', status=400)

        student = Student.objects.filter(pk=student_id).first()
        if not student:
            return render(request, 'admissions/activation_invalid.html', status=400)

        if not student.email_verified:
            student.email_verified = True
            student.email_verified_at = timezone.now()
            student.save(update_fields=['email_verified', 'email_verified_at'])

        return render(request, 'admissions/activation_done.html', {'student': student})


@method_decorator([never_cache, csrf_protect], name='dispatch')
class ResendActivationView(View):
    """Permet de renvoyer un email d'activation."""
    template_name = 'admissions/resend_activation.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ResendActivationForm()})

    def post(self, request):
        form = ResendActivationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        student = Student.objects.filter(email__iexact=email).first()
        if student and not student.email_verified:
            token = make_activation_token(student)
            send_activation_email(student, token, request=request)

        # Réponse uniforme pour ne pas révéler l'existence ou non du compte
        return render(
            request,
            'admissions/activation_sent.html',
            {'email': email, 'resent': True},
        )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class PasswordResetRequestView(View):
    """Demande un email de réinitialisation du mot de passe."""
    template_name = 'admissions/password_reset_request.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        student = Student.objects.filter(email__iexact=email).first()
        if student and student.has_external_password():
            token = make_password_reset_token(student)
            send_password_reset_email(student, token, request=request)

        # Réponse uniforme : on ne révèle pas si l'email existe en base
        return render(
            request,
            'admissions/password_reset_sent.html',
            {'email': email},
        )


@method_decorator([never_cache, csrf_protect], name='dispatch')
class PasswordResetConfirmView(View):
    """Définit un nouveau mot de passe à partir d'un token signé."""
    template_name = 'admissions/password_reset_confirm.html'

    def _resolve_student(self, token):
        result = validate_password_reset_token(token)
        if result is None:
            return None
        student_id, password_hash = result
        student = Student.objects.filter(pk=student_id).first()
        if not student:
            return None
        # Le hash courant doit toujours correspondre à celui du token : tout
        # changement de mot de passe entre temps invalide le lien.
        if (student.external_password_hash or '') != password_hash:
            return None
        return student

    def get(self, request, token):
        student = self._resolve_student(token)
        if not student:
            return render(request, 'admissions/password_reset_invalid.html', status=400)
        return render(request, self.template_name, {
            'form': PasswordResetConfirmForm(),
            'token': token,
            'student': student,
        })

    def post(self, request, token):
        student = self._resolve_student(token)
        if not student:
            return render(request, 'admissions/password_reset_invalid.html', status=400)

        form = PasswordResetConfirmForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'token': token,
                'student': student,
            })

        student.set_external_password(form.cleaned_data['password'])
        # Le reset confirme implicitement la possession de l'adresse mail.
        if not student.email_verified:
            student.email_verified = True
            student.email_verified_at = timezone.now()
            student.save(update_fields=['email_verified', 'email_verified_at'])

        return render(request, 'admissions/password_reset_done.html', {'student': student})
