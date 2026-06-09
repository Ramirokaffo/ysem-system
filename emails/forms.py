from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from tinymce.widgets import TinyMCE


_INPUT_CLASS = 'form-control shadow-inset border-light bg-primary'


class ComposeEmailForm(forms.Form):
    """Formulaire universel de composition d'un email."""

    recipients = forms.CharField(
        label="Destinataires",
        help_text="Adresses email séparées par des virgules.",
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'exemple@domaine.com, autre@domaine.com',
        }),
    )
    subject = forms.CharField(
        label="Objet",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': "Objet de l'email",
        }),
    )
    body = forms.CharField(
        label="Message",
        widget=TinyMCE(attrs={'class': 'tinymce', 'cols': 80, 'rows': 20}),
    )

    def clean_recipients(self):
        raw = self.cleaned_data.get('recipients', '')
        emails = [
            email.strip()
            for email in raw.replace(';', ',').replace('\n', ',').split(',')
            if email.strip()
        ]
        if not emails:
            raise ValidationError("Veuillez saisir au moins un destinataire.")

        invalid = []
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                invalid.append(email)
        if invalid:
            raise ValidationError(
                "Adresse(s) email invalide(s) : %(emails)s",
                params={'emails': ', '.join(invalid)},
            )

        return list(dict.fromkeys(emails))
