from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import date, timedelta

from student_portal.decorators import scholar_admin_required
from .models import Agent, Campagne, Equipe, Prospect
from .forms import (
    AgentForm, CampagneForm, EquipeForm, ProspectForm,
    AgentSearchForm, CampagneSearchForm, EquipeSearchForm, ProspectSearchForm
)
from academic.models import AcademicYear


@method_decorator(scholar_admin_required, name='dispatch')
class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard prospection"""
    template_name = 'prospection/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard Prospection'
        
        # Statistiques générales
        context['stats'] = {
            'total_agents': Agent.objects.filter(statut='actif').count(),
            'total_campagnes': Campagne.objects.count(),
            'campagnes_actives': Campagne.objects.filter(statut='en_cours').count(),
            'total_equipes': Equipe.objects.count(),
            'total_prospects': Prospect.objects.count(),
        }
        
        # Campagnes récentes
        context['campagnes_recentes'] = Campagne.objects.order_by('-created_at')[:5]
        
        # Équipes avec meilleur taux de réalisation
        equipes = Equipe.objects.annotate(
            prospects_count=Count('prospects')
        ).filter(prospects_count__gt=0)
        
        context['meilleures_equipes'] = sorted(
            equipes, 
            key=lambda e: e.taux_realisation, 
            reverse=True
        )[:5]
        
        # Prospects récents
        context['prospects_recents'] = Prospect.objects.order_by('-date_collecte')[:10]
        
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class AgentsView(LoginRequiredMixin, ListView):
    """Vue pour la liste des agents"""
    model = Agent
    template_name = 'prospection/agents.html'
    context_object_name = 'agents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Agent.objects.all()
        form = AgentSearchForm(self.request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            type_agent = form.cleaned_data.get('type_agent')
            statut = form.cleaned_data.get('statut')
            
            if search:
                queryset = queryset.filter(
                    Q(nom__icontains=search) |
                    Q(prenom__icontains=search) |
                    Q(matricule__icontains=search) |
                    Q(telephone__icontains=search)
                )
            
            if type_agent:
                queryset = queryset.filter(type_agent=type_agent)
            
            if statut:
                queryset = queryset.filter(statut=statut)
        
        return queryset.order_by('nom', 'prenom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Agents'
        context['search_form'] = AgentSearchForm(self.request.GET)
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class AjouterAgentView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter un agent"""
    model = Agent
    form_class = AgentForm
    template_name = 'prospection/ajouter_agent.html'
    success_url = reverse_lazy('prospection:agents')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter un Agent'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Agent ajouté avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class DetailAgentView(LoginRequiredMixin, DetailView):
    """Vue pour les détails d'un agent"""
    model = Agent
    template_name = 'prospection/detail_agent.html'
    context_object_name = 'agent'
    slug_field = 'matricule'
    slug_url_kwarg = 'matricule'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Agent {self.object.nom_complet}'
        
        # Statistiques de l'agent
        context['stats'] = {
            'equipes_count': self.object.equipes.count(),
            'equipes_dirigees_count': self.object.equipes_dirigees.count(),
            'prospects_collectes_count': self.object.prospects_collectes.count(),
        }
        
        # Équipes de l'agent
        context['equipes'] = self.object.equipes.all()[:5]
        
        # Prospects récents collectés
        context['prospects_recents'] = self.object.prospects_collectes.order_by('-date_collecte')[:10]
        
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class ModifierAgentView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un agent"""
    model = Agent
    form_class = AgentForm
    template_name = 'prospection/modifier_agent.html'
    slug_field = 'matricule'
    slug_url_kwarg = 'matricule'
    
    def get_success_url(self):
        return reverse_lazy('prospection:detail_agent', kwargs={'matricule': self.object.matricule})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier {self.object.nom_complet}'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Agent modifié avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class CampagnesView(LoginRequiredMixin, ListView):
    """Vue pour la liste des campagnes"""
    model = Campagne
    template_name = 'prospection/campagnes.html'
    context_object_name = 'campagnes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Campagne.objects.all()
        form = CampagneSearchForm(self.request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            statut = form.cleaned_data.get('statut')
            annee_academique = form.cleaned_data.get('annee_academique')
            
            if search:
                queryset = queryset.filter(nom__icontains=search)
            
            if statut:
                queryset = queryset.filter(statut=statut)
            
            if annee_academique:
                queryset = queryset.filter(annee_academique=annee_academique)
        
        return queryset.order_by('-date_debut')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Campagnes'
        context['search_form'] = CampagneSearchForm(self.request.GET)
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class AjouterCampagneView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter une campagne"""
    model = Campagne
    form_class = CampagneForm
    template_name = 'prospection/ajouter_campagne.html'
    success_url = reverse_lazy('prospection:campagnes')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter une Campagne'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Campagne ajoutée avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class DetailCampagneView(LoginRequiredMixin, DetailView):
    """Vue pour les détails d'une campagne"""
    model = Campagne
    template_name = 'prospection/detail_campagne.html'
    context_object_name = 'campagne'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Campagne {self.object.nom}'
        
        # Statistiques de la campagne
        equipes = self.object.equipes.all()
        total_prospects = sum(equipe.prospects_collectes for equipe in equipes)
        
        context['stats'] = {
            'equipes_count': equipes.count(),
            'agents_count': sum(equipe.nombre_agents for equipe in equipes),
            'prospects_collectes': total_prospects,
            'taux_realisation': (total_prospects / self.object.objectif_global * 100) if self.object.objectif_global > 0 else 0,
        }
        
        # Équipes de la campagne
        context['equipes'] = equipes.annotate(prospects_count=Count('prospects'))
        
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class ModifierCampagneView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une campagne"""
    model = Campagne
    form_class = CampagneForm
    template_name = 'prospection/modifier_campagne.html'
    
    def get_success_url(self):
        return reverse_lazy('prospection:detail_campagne', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier {self.object.nom}'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Campagne modifiée avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class EquipesView(LoginRequiredMixin, ListView):
    """Vue pour la liste des équipes"""
    model = Equipe
    template_name = 'prospection/equipes.html'
    context_object_name = 'equipes'
    paginate_by = 20

    def get_queryset(self):
        queryset = Equipe.objects.select_related('campagne', 'chef_equipe').prefetch_related('agents')
        form = EquipeSearchForm(self.request.GET)

        if form.is_valid():
            search = form.cleaned_data.get('search')
            campagne = form.cleaned_data.get('campagne')

            if search:
                queryset = queryset.filter(nom__icontains=search)

            if campagne:
                queryset = queryset.filter(campagne=campagne)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Équipes'
        context['search_form'] = EquipeSearchForm(self.request.GET)
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class AjouterEquipeView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter une équipe"""
    model = Equipe
    form_class = EquipeForm
    template_name = 'prospection/ajouter_equipe.html'
    success_url = reverse_lazy('prospection:equipes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter une Équipe'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Équipe ajoutée avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class DetailEquipeView(LoginRequiredMixin, DetailView):
    """Vue pour les détails d'une équipe"""
    model = Equipe
    template_name = 'prospection/detail_equipe.html'
    context_object_name = 'equipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Équipe {self.object.nom}'

        # Prospects de l'équipe
        context['prospects'] = self.object.prospects.order_by('-date_collecte')

        return context


@method_decorator(scholar_admin_required, name='dispatch')
class ModifierEquipeView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une équipe"""
    model = Equipe
    form_class = EquipeForm
    template_name = 'prospection/modifier_equipe.html'

    def get_success_url(self):
        return reverse_lazy('prospection:detail_equipe', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier {self.object.nom}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Équipe modifiée avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class ProspectsView(LoginRequiredMixin, ListView):
    """Vue pour la liste des prospects"""
    model = Prospect
    template_name = 'prospection/prospects.html'
    context_object_name = 'prospects'
    paginate_by = 20

    def get_queryset(self):
        queryset = Prospect.objects.select_related('equipe', 'agent_collecteur', 'etablissement_origine')
        form = ProspectSearchForm(self.request.GET)

        if form.is_valid():
            search = form.cleaned_data.get('search')
            equipe = form.cleaned_data.get('equipe')
            agent_collecteur = form.cleaned_data.get('agent_collecteur')

            if search:
                queryset = queryset.filter(
                    Q(nom__icontains=search) |
                    Q(prenom__icontains=search) |
                    Q(telephone__icontains=search)
                )

            if equipe:
                queryset = queryset.filter(equipe=equipe)

            if agent_collecteur:
                queryset = queryset.filter(agent_collecteur=agent_collecteur)

        return queryset.order_by('-date_collecte')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Prospects'
        context['search_form'] = ProspectSearchForm(self.request.GET)
        return context


@method_decorator(scholar_admin_required, name='dispatch')
class AjouterProspectView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter un prospect"""
    model = Prospect
    form_class = ProspectForm
    template_name = 'prospection/ajouter_prospect.html'
    success_url = reverse_lazy('prospection:prospects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ajouter un Prospect'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Prospect ajouté avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class DetailProspectView(LoginRequiredMixin, DetailView):
    """Vue pour les détails d'un prospect"""
    model = Prospect
    template_name = 'prospection/detail_prospect.html'
    context_object_name = 'prospect'


@method_decorator(scholar_admin_required, name='dispatch')
class ModifierProspectView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un prospect"""
    model = Prospect
    form_class = ProspectForm
    template_name = 'prospection/modifier_prospect.html'

    def get_success_url(self):
        return reverse_lazy('prospection:detail_prospect', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier {self.object.nom_complet}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Prospect modifié avec succès.')
        return super().form_valid(form)


@method_decorator(scholar_admin_required, name='dispatch')
class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques de prospection"""
    template_name = 'prospection/statistiques.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques de Prospection'

        # Statistiques générales
        context['stats_generales'] = {
            'total_agents': Agent.objects.count(),
            'agents_actifs': Agent.objects.filter(statut='actif').count(),
            'total_campagnes': Campagne.objects.count(),
            'campagnes_actives': Campagne.objects.filter(statut='en_cours').count(),
            'total_equipes': Equipe.objects.count(),
            'total_prospects': Prospect.objects.count(),
        }

        # Statistiques par campagne
        campagnes = Campagne.objects.annotate(
            equipes_count=Count('equipes'),
            prospects_count=Count('equipes__prospects')
        )
        context['stats_campagnes'] = campagnes

        # Top agents collecteurs
        agents_stats = Agent.objects.annotate(
            prospects_count=Count('prospects_collectes')
        ).filter(prospects_count__gt=0).order_by('-prospects_count')[:10]
        context['top_agents'] = agents_stats

        # Équipes les plus performantes
        equipes_stats = Equipe.objects.annotate(
            prospects_count=Count('prospects')
        ).filter(prospects_count__gt=0)

        context['top_equipes'] = sorted(
            equipes_stats,
            key=lambda e: e.taux_realisation,
            reverse=True
        )[:10]

        return context
