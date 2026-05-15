from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from students.models import Student


class AdmissionSignupForm(forms.Form):
    """Formulaire de création d'un compte candidat sur le portail d'admission."""

    firstname = forms.CharField(
        max_length=100,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'placeholder': 'Votre prénom',
            'autocomplete': 'given-name',
        }),
    )
    lastname = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'placeholder': 'Votre nom de famille',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Retapez votre mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if Student.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Un compte existe déjà avec cette adresse e-mail."
            )
        return email

    def clean_firstname(self):
        return (self.cleaned_data.get('firstname') or '').strip()

    def clean_lastname(self):
        return (self.cleaned_data.get('lastname') or '').strip()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')

        if password and confirm and password != confirm:
            self.add_error(
                'password_confirm',
                "Les deux mots de passe ne correspondent pas."
            )

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned


class AdmissionLoginForm(forms.Form):
    """Formulaire de connexion au portail d'admission."""

    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()


class PasswordResetRequestForm(forms.Form):
    """Formulaire de demande de réinitialisation de mot de passe."""

    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()


class PasswordResetConfirmForm(forms.Form):
    """Définition d'un nouveau mot de passe via le lien de réinitialisation."""

    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Retapez votre nouveau mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')

        if password and confirm and password != confirm:
            self.add_error(
                'password_confirm',
                "Les deux mots de passe ne correspondent pas."
            )

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned


class ChangePasswordForm(forms.Form):
    """Changement de mot de passe pour un candidat connecté."""

    current_password = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Votre mot de passe actuel',
            'autocomplete': 'current-password',
        }),
    )
    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Retapez votre nouveau mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._student = student

    def clean_current_password(self):
        current = self.cleaned_data.get('current_password') or ''
        if self._student and not self._student.check_external_password(current):
            raise ValidationError("Le mot de passe actuel est incorrect.")
        return current

    def clean(self):
        cleaned = super().clean()
        current = cleaned.get('current_password')
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')

        if password and confirm and password != confirm:
            self.add_error(
                'password_confirm',
                "Les deux mots de passe ne correspondent pas.",
            )

        if password and current and password == current:
            self.add_error(
                'password',
                "Le nouveau mot de passe doit être différent de l'ancien.",
            )

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned


class ResendActivationForm(forms.Form):
    """Formulaire pour renvoyer un email d'activation."""

    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()
