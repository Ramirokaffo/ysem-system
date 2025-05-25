from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard"""
    template_name = 'main/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'
        return context


class InscriptionsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des inscriptions"""
    template_name = 'main/inscriptions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des inscriptions'
        return context


class EtudiantsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des étudiants"""
    template_name = 'main/etudiants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des étudiants'
        return context


class DocumentsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des documents"""
    template_name = 'main/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Documents officiels'
        return context


class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques"""
    template_name = 'main/statistiques.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'
        return context


class ParametresView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres"""
    template_name = 'main/parametres.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paramètres'
        return context
