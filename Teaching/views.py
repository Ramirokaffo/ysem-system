from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from students.models import Student
from accounts.models import BaseUser, Godfather
import json
from Teaching.models import TeachingMonitoring


from Teaching.models import Evaluation, Lecturer
from .forms import EnseignantForm

class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard"""
    template_name = 'Teaching/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'
        return context


class EnseignantsView(LoginRequiredMixin, TemplateView):
    """Vue pour la visualisationdes enseignants"""
    template_name = 'Teaching/enseignants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération de tous les enseignants
        context['enseignants'] = Lecturer.objects.all()
        context['page_title'] = 'Visualisation des enseignants'
        return context

class ajouter_enseignantView(LoginRequiredMixin, TemplateView):
    """Vue pour l'ajout d'enseignants"""
    model = Lecturer
    form_class = EnseignantForm
    template_name = 'Teaching/ajouter_enseignant.html'
    success_url = '/enseignants/'

    def ajouter_enseignant(request):
        if request.method == 'POST':
            form = EnseignantForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('teaching:enseignants')  # adapte à ton nom de vue principale
        else:
            form = EnseignantForm()
        return render(request, 'Teaching/ajouter_enseignant.html', {'form': form})
            


class EvaluationsView(LoginRequiredMixin, TemplateView):
    """Vue pour l'évaluation des enseignants"""
    template_name = 'Teaching/evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération de tous les enseignants
        context['evaluations'] = Evaluation.objects.all()
        context['page_title'] = 'Evaluation des enseignants'
        return context


class Suivi_CoursView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion du suivi des cours"""
    template_name = 'Teaching/suivi_cours.html'

    def get_context_data(self, **kwargs):
        # Récupération de tous les suivis
        context = super().get_context_data(**kwargs)
        context['suivi_cours'] = TeachingMonitoring.objects.all()
        context['avancements'] = TeachingMonitoring.objects.all()
        context['page_title'] = 'Cahier de texte'
        return context



class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques"""
    template_name = 'Teaching/statistiques.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'
        return context


class ParametresView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres"""
    template_name = 'Teaching/parametres.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paramètres'
        return context






