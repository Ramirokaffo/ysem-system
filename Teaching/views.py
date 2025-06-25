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

from Teaching.models import Lecturer


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


class EvaluationsView(LoginRequiredMixin, TemplateView):
    """Vue pour l'évaluation des enseignants"""
    template_name = 'Teaching/evaluation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Evaluation des enseignants'
        return context


class Suivi_CoursView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion du suivi des cours"""
    template_name = 'Teaching/suivi_cours.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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






