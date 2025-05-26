from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from .forms import InscriptionEtape1Form, InscriptionEtape2Form, InscriptionEtape3Form, InscriptionEtape4Form
from students.models import Student
from accounts.models import BaseUser, Godfather
import json


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


class InscriptionExterneView(TemplateView):
    """Vue d'accueil pour l'inscription externe"""
    template_name = 'main/inscription_externe/accueil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inscription - YSEM'
        return context


class InscriptionExterneStepView(TemplateView):
    """Vue pour gérer les étapes du formulaire d'inscription"""
    template_name = 'main/inscription_externe/formulaire.html'

    def get_form_class(self, step):
        """Retourne la classe de formulaire pour l'étape donnée"""
        # L'étape 1 (Informations administratives) est réservée à l'administration
        # Le formulaire commence donc à l'étape 2
        forms = {
            1: InscriptionEtape2Form,  # Étape 1 du formulaire = Identification du candidat
            2: InscriptionEtape3Form,  # Étape 2 du formulaire = Informations familiales
            3: InscriptionEtape4Form,  # Étape 3 du formulaire = Cursus et spécialité
        }
        return forms.get(step)

    def get_step_title(self, step):
        """Retourne le titre de l'étape"""
        # Titres ajustés car l'étape 1 administrative n'existe plus pour les étudiants
        titles = {
            1: "Identification du candidat",
            2: "Informations familiales",
            3: "Cursus et spécialité",
        }
        return titles.get(step, "Étape inconnue")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = kwargs.get('step', 1)

        # Validation de l'étape (maintenant 3 étapes au lieu de 4)
        if step not in [1, 2, 3]:
            step = 1

        form_class = self.get_form_class(step)

        # Récupération des données de session
        session_data = self.request.session.get('inscription_data', {})
        # Ajustement pour correspondre aux vraies étapes du formulaire
        step_data = session_data.get(f'etape_{step + 1}', {})  # etape_2, etape_3, etape_4

        # Conversion des chaînes de dates en objets date pour le formulaire
        if step_data:
            from datetime import datetime
            converted_data = {}
            for key, value in step_data.items():
                if isinstance(value, str) and key in ['date_naissance']:  # Champs de date connus
                    try:
                        converted_data[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        converted_data[key] = value
                else:
                    converted_data[key] = value
            step_data = converted_data

        # Création du formulaire avec les données existantes
        form = form_class(initial=step_data) if form_class else None

        context.update({
            'page_title': f'Inscription - Étape {step}',
            'step': step,
            'step_title': self.get_step_title(step),
            'form': form,
            'total_steps': 3,  # 3 étapes au lieu de 4
            'progress_percentage': (step / 3) * 100,
            'prev_step': step - 1 if step > 1 else None,
            'next_step': step + 1 if step < 3 else None,
        })
        return context

    def post(self, request, *args, **kwargs):
        step = kwargs.get('step', 1)
        form_class = self.get_form_class(step)

        if not form_class:
            return redirect('main:inscription_externe_step', step=1)

        form = form_class(request.POST)

        if form.is_valid():
            # Sauvegarde des données dans la session
            if 'inscription_data' not in request.session:
                request.session['inscription_data'] = {}

            # Conversion des données pour la sérialisation JSON
            cleaned_data = {}
            for key, value in form.cleaned_data.items():
                if hasattr(value, 'strftime'):  # Si c'est un objet date/datetime
                    cleaned_data[key] = value.strftime('%Y-%m-%d')
                else:
                    cleaned_data[key] = value

            # Ajustement pour correspondre aux vraies étapes du formulaire
            real_step = step + 1  # etape_2, etape_3, etape_4
            request.session['inscription_data'][f'etape_{real_step}'] = cleaned_data
            request.session.modified = True

            # Redirection vers l'étape suivante ou confirmation
            if step < 3:  # 3 étapes au lieu de 4
                messages.success(request, f'Étape {step} complétée avec succès!')
                return redirect('main:inscription_externe_step', step=step + 1)
            else:
                # Dernière étape, redirection vers la confirmation
                return redirect('main:inscription_externe_confirmation')
        else:
            # Formulaire invalide, affichage des erreurs
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

        # Retour à la vue avec le formulaire et les erreurs
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class InscriptionExterneConfirmationView(TemplateView):
    """Vue de confirmation et finalisation de l'inscription"""
    template_name = 'main/inscription_externe/confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupération de toutes les données de session
        session_data = self.request.session.get('inscription_data', {})

        context.update({
            'page_title': 'Confirmation d\'inscription',
            'inscription_data': session_data,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Finalisation de l'inscription"""
        session_data = request.session.get('inscription_data', {})

        if not session_data:
            messages.error(request, 'Aucune donnée d\'inscription trouvée. Veuillez recommencer.')
            return redirect('main:inscription_externe')

        try:
            # Création de l'étudiant avec les données collectées
            etape2_data = session_data.get('etape_2', {})
            etape3_data = session_data.get('etape_3', {})
            etape4_data = session_data.get('etape_4', {})

            # Conversion de la date de naissance si elle est en chaîne
            date_naissance = etape2_data.get('date_naissance')
            if isinstance(date_naissance, str):
                from datetime import datetime
                try:
                    date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    date_naissance = None

            # Génération d'un matricule temporaire
            import uuid
            matricule = f"EXT_{uuid.uuid4().hex[:8].upper()}"

            # Création de l'étudiant
            student = Student.objects.create(
                matricule=matricule,
                firstname=etape2_data.get('prenom', ''),
                lastname=etape2_data.get('nom', ''),
                date_naiss=date_naissance,
                status='inscrit',  # Statut d'inscrit
                gender=etape2_data.get('sexe', ''),
                phone_number=etape2_data.get('telephone', ''),
                email=etape2_data.get('courriel', ''),
            )

            # Nettoyage de la session
            if 'inscription_data' in request.session:
                del request.session['inscription_data']

            messages.success(
                request,
                f'Votre inscription a été enregistrée avec succès! '
                f'Votre numéro de matricule temporaire est: {matricule}. '
                f'Vous recevrez un email de confirmation sous peu.'
            )

            # Redirection vers une page de succès
            return redirect('main:inscription_externe')

        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'enregistrement: {str(e)}')
            return self.render_to_response(self.get_context_data(**kwargs))
