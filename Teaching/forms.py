from django import forms
from .models import Lecturer

class EnseignantForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = '__all__'
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naiss': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'lang': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
