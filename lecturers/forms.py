from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Lecturer


_INPUT_CLASS = 'form-control'


class LecturerSignupForm(forms.Form):
    """Création d'un compte enseignant (candidature)."""

    firstname = forms.CharField(
        max_length=100,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Votre prénom',
            'autocomplete': 'given-name',
        }),
    )
    lastname = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Votre nom de famille',
            'autocomplete': 'family-name',
        }),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Retapez votre mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if Lecturer.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte existe déjà avec cette adresse e-mail.")
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
            self.add_error('password_confirm', "Les deux mots de passe ne correspondent pas.")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned


class LecturerLoginForm(forms.Form):
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()


class ResendActivationForm(forms.Form):
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()


class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Retapez votre nouveau mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')

        if password and confirm and password != confirm:
            self.add_error('password_confirm', "Les deux mots de passe ne correspondent pas.")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned
