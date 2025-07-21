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
from .models import Agent, Campagne, Equipe, Prospect, SeanceProspection
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
        queryset = Equipe.objects.select_related('seance__campagne', 'chef_equipe').prefetch_related('agents')
        form = EquipeSearchForm(self.request.GET)

        if form.is_valid():
            search = form.cleaned_data.get('search')
            seance = form.cleaned_data.get('seance')

            if search:
                queryset = queryset.filter(nom__icontains=search)

            if seance:
                queryset = queryset.filter(seance=seance)

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

        # Vérifier si une séance d'aujourd'hui existe pour une campagne active
        aujourd_hui = timezone.now().date()
        context['seance_aujourd_hui_existe'] = SeanceProspection.objects.filter(
            date_seance=aujourd_hui,
            campagne__statut__in=['planifiee', 'en_cours']
        ).exists()
        context['date_aujourd_hui'] = aujourd_hui

        # Récupérer les campagnes actives pour la création de séance
        context['campagnes_actives'] = Campagne.objects.filter(
            statut__in=['planifiee', 'en_cours']
        ).order_by('-date_debut')

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Équipe ajoutée avec succès.')
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """Gérer la création de séance si demandée"""
        if 'creer_seance' in request.POST:
            campagne_id = request.POST.get('campagne_id')
            if campagne_id:
                try:
                    campagne = Campagne.objects.get(id=campagne_id, statut__in=['planifiee', 'en_cours'])
                    # Créer la séance du jour pour cette campagne
                    seance, created = SeanceProspection.creer_seance_aujourd_hui(
                        campagne=campagne,
                        created_by=request.user
                    )

                    if created:
                        messages.success(request, f'Séance du {seance.date_seance.strftime("%d/%m/%Y")} créée avec succès pour la campagne "{campagne.nom}".')
                    else:
                        messages.info(request, f'La séance du {seance.date_seance.strftime("%d/%m/%Y")} existe déjà pour la campagne "{campagne.nom}".')
                except Campagne.DoesNotExist:
                    messages.error(request, 'Campagne non trouvée ou inactive.')
            else:
                messages.error(request, 'Veuillez sélectionner une campagne.')

            # Rediriger vers la même page pour rafraîchir le formulaire
            return redirect('prospection:ajouter_equipe')

        # Traitement normal du formulaire
        return super().post(request, *args, **kwargs)


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
            equipes_count=Count('seances__equipes'),
            prospects_count=Count('seances__equipes__prospects')
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

        # Données pour les graphiques
        import json
        from datetime import datetime, timedelta
        from django.db.models.functions import TruncMonth

        # 1. Répartition des prospects par campagne
        campagnes_prospects = []
        for campagne in campagnes:
            campagnes_prospects.append({
                'nom': campagne.nom,
                'prospects': campagne.prospects_count,
                'objectif': campagne.objectif_global
            })
        context['campagnes_prospects_data'] = json.dumps(campagnes_prospects)

        # 2. Évolution des prospects par mois (derniers 6 mois)
        six_months_ago = datetime.now() - timedelta(days=180)
        prospects_par_mois = Prospect.objects.filter(
            date_collecte__gte=six_months_ago
        ).annotate(
            mois=TruncMonth('date_collecte')
        ).values('mois').annotate(
            count=Count('id')
        ).order_by('mois')

        # Convertir les dates en chaînes pour JSON
        evolution_data = []
        for item in prospects_par_mois:
            evolution_data.append({
                'mois': item['mois'].isoformat() if item['mois'] else '',
                'count': item['count']
            })
        context['prospects_evolution_data'] = json.dumps(evolution_data)

        # 3. Répartition des agents par type
        agents_par_type = Agent.objects.values('type_agent').annotate(
            count=Count('id')
        ).order_by('type_agent')
        context['agents_type_data'] = json.dumps(list(agents_par_type))

        # 4. Performance des équipes (top 10)
        equipes_performance = []
        for equipe in context['top_equipes']:
            equipes_performance.append({
                'nom': equipe.nom,
                'taux': float(equipe.taux_realisation),
                'prospects': equipe.prospects_count,
                'objectif': equipe.objectif_prospects or 0
            })
        context['equipes_performance_data'] = json.dumps(equipes_performance)

        return context


# ===== NOUVELLES VUES POUR LES SÉANCES DE PROSPECTION =====

@method_decorator(scholar_admin_required, name='dispatch')
class SeancesView(LoginRequiredMixin, ListView):
    """Vue pour la liste des séances de prospection"""
    model = SeanceProspection
    template_name = 'prospection/seances.html'
    context_object_name = 'seances'
    paginate_by = 20

    def get_queryset(self):
        queryset = SeanceProspection.objects.all()

        # Filtres
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset.order_by('-date_seance')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Séances de Prospection'
        context['statuts'] = SeanceProspection.STATUS_CHOICES

        # Vérifier si la séance d'aujourd'hui existe
        from django.utils import timezone
        aujourd_hui = timezone.now().date()
        context['seance_aujourd_hui_existe'] = SeanceProspection.objects.filter(
            date_seance=aujourd_hui
        ).exists()

        return context

    def post(self, request, *args, **kwargs):
        """Créer automatiquement la séance du jour"""
        seance, created = SeanceProspection.creer_seance_aujourd_hui(
            created_by=request.user
        )

        if created:
            messages.success(request, f'Séance du {seance.date_seance.strftime("%d/%m/%Y")} créée avec succès.')
        else:
            messages.info(request, f'La séance du {seance.date_seance.strftime("%d/%m/%Y")} existe déjà.')

        return redirect('prospection:seances')


@method_decorator(scholar_admin_required, name='dispatch')
class ModifierStatutSeanceView(LoginRequiredMixin, TemplateView):
    """Vue pour modifier le statut d'une séance"""
    template_name = 'prospection/modifier_statut_seance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seance = get_object_or_404(SeanceProspection, pk=kwargs['pk'])
        context['seance'] = seance
        context['page_title'] = f'Modifier le statut - {seance.nom}'
        context['statuts'] = SeanceProspection.STATUS_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        seance = get_object_or_404(SeanceProspection, pk=kwargs['pk'])
        nouveau_statut = request.POST.get('statut')

        if nouveau_statut in dict(SeanceProspection.STATUS_CHOICES):
            ancien_statut = seance.get_statut_display()
            seance.statut = nouveau_statut
            seance.save()

            nouveau_statut_display = seance.get_statut_display()
            messages.success(
                request,
                f'Statut modifié de "{ancien_statut}" vers "{nouveau_statut_display}"'
            )
        else:
            messages.error(request, 'Statut invalide.')

        return redirect('prospection:detail_seance', pk=seance.pk)


@method_decorator(scholar_admin_required, name='dispatch')
class DetailSeanceView(LoginRequiredMixin, DetailView):
    """Vue pour les détails d'une séance"""
    model = SeanceProspection
    template_name = 'prospection/detail_seance.html'
    context_object_name = 'seance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Séance {self.object.nom}'

        # Équipes de la séance
        equipes = self.object.equipes.all()
        context['equipes'] = equipes

        # Statistiques
        context['stats'] = {
            'nombre_equipes': equipes.count(),
            'nombre_agents_total': sum(equipe.nombre_agents for equipe in equipes),
            'objectif_total': sum(equipe.objectif_equipe for equipe in equipes),
        }

        return context





# ===== VUES POUR LA GESTION DES AGENTS (ACTIVATION) =====

@method_decorator(scholar_admin_required, name='dispatch')
class GestionAgentsView(LoginRequiredMixin, ListView):
    """Vue pour la gestion des agents (activation/désactivation)"""
    model = Agent
    template_name = 'prospection/gestion_agents.html'
    context_object_name = 'agents'
    paginate_by = 20

    def get_queryset(self):
        queryset = Agent.objects.all()

        # Filtres
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        type_agent = self.request.GET.get('type_agent')
        if type_agent:
            queryset = queryset.filter(type_agent=type_agent)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(matricule__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by('statut', 'nom', 'prenom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Agents'

        # Statistiques
        context['stats'] = {
            'total_agents': Agent.objects.count(),
            'agents_actifs': Agent.objects.filter(statut='actif').count(),
            'agents_pending': Agent.objects.filter(statut='pending').count(),
            'agents_inactifs': Agent.objects.filter(statut='inactif').count(),
            'agents_suspendus': Agent.objects.filter(statut='suspendu').count(),
        }

        context['statuts'] = Agent.STATUS_CHOICES
        context['types'] = Agent.TYPE_CHOICES

        return context


@method_decorator(scholar_admin_required, name='dispatch')
class ActiverAgentView(LoginRequiredMixin, TemplateView):
    """Vue pour activer/désactiver un agent"""
    template_name = 'prospection/activer_agent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = get_object_or_404(Agent, pk=kwargs['pk'])
        context['agent'] = agent
        context['page_title'] = f'Gestion de {agent.nom_complet}'
        return context

    def post(self, request, *args, **kwargs):
        agent = get_object_or_404(Agent, pk=kwargs['pk'])
        action = request.POST.get('action')
        motif = request.POST.get('motif', '')

        if action == 'activer':
            agent.statut = 'actif'
            agent.is_active = True
            messages.success(request, f'Agent {agent.nom_complet} activé avec succès.')
        elif action == 'desactiver':
            agent.statut = 'inactif'
            agent.is_active = False
            messages.success(request, f'Agent {agent.nom_complet} désactivé avec succès.')
        elif action == 'suspendre':
            agent.statut = 'suspendu'
            agent.is_active = False
            messages.warning(request, f'Agent {agent.nom_complet} suspendu.')

        agent.save()

        # TODO: Envoyer une notification par email à l'agent

        return redirect('prospection:gestion_agents')
