from django.shortcuts import render, redirect, get_object_or_404
from students.models import OfficialDocument, Student, StudentMetaData, StudentLevel
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse

from academic.models import AcademicYear, Level, Program, Speciality
from .forms import InscriptionCompleteForm, InscriptionEtape2Form, InscriptionEtape3Form, InscriptionEtape4Form, StudentEditForm, StudentMetaDataEditForm, OfficialDocumentForm, BulkDocumentCreationForm
from accounts.models import BaseUser, Godfather
from students.models import Student, StudentLevel, StudentMetaData, OfficialDocument
import json
from django.core.paginator import Paginator
from student_portal.decorators import scholar_admin_required
from django.utils import timezone


class HomeView(TemplateView):
    """Vue d'accueil publique"""
    template_name = 'main/home.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard"""
    template_name = 'main/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from datetime import datetime, timedelta
        from academic.models import Program

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'

        # Année académique active
        current_year = AcademicYear.objects.filter(is_active=True).first()
        context['current_year'] = current_year

        # Statistiques générales
        total_students = Student.objects.filter(status='approved').count()
        pending_students = Student.objects.filter(status='pending').count()
        total_programs = Program.objects.count()

        # Documents en attente (disponibles non retirés)
        pending_documents = OfficialDocument.objects.filter(status='available').count()

        # Nouvelles inscriptions (derniers 30 jours)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_enrollments = Student.objects.filter(
            created_at__gte=thirty_days_ago,
            status='approved'
        ).count()

        # Activités récentes (derniers étudiants inscrits)
        recent_students = Student.objects.filter(
            status='approved'
        ).order_by('-created_at')[:5]

        # Documents récemment créés
        recent_documents = OfficialDocument.objects.select_related(
            'student_level__student',
            'student_level__level'
        ).order_by('-created_at')[:5]

        # Étudiants en attente d'approbation
        students_pending_approval = Student.objects.filter(
            status='pending'
        ).order_by('-created_at')[:3]

        # Statistiques par niveau
        level_stats = StudentLevel.objects.filter(
            is_active=True,
            student__status='approved'
        ).values('level__name').annotate(count=Count('student')).order_by('-count')[:5]

        context.update({
            'total_students': total_students,
            'pending_students': pending_students,
            'new_enrollments': new_enrollments,
            'pending_documents': pending_documents,
            'total_programs': total_programs,
            'recent_students': recent_students,
            'recent_documents': recent_documents,
            'students_pending_approval': students_pending_approval,
            'level_stats': level_stats,
        })

        return context



class InscriptionsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des inscriptions"""
    template_name = 'main/inscriptions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des inscriptions'

        # Récupération des paramètres de filtrage
        status = self.request.GET.get('status')
        gender = self.request.GET.get('gender')
        school_id = self.request.GET.get('school')
        program_id = self.request.GET.get('program')
        godfather_id = self.request.GET.get('godfather')
        language = self.request.GET.get('language')

        # Filtrage de base par statut
        if status:
            students = Student.objects.filter(status=status)
        else:
            students = Student.objects.filter(status__in=['pending', 'abandoned', 'rejected'])

        # Application des filtres additionnels
        if gender:
            students = students.filter(gender=gender)
        if school_id:
            students = students.filter(school_id=school_id)
        if program_id:
            students = students.filter(program_id=program_id)
        if godfather_id:
            students = students.filter(godfather_id=godfather_id)
        if language:
            students = students.filter(lang=language)

        # Import des modèles pour les options de filtrage
        from schools.models import School
        from academic.models import Program
        from accounts.models import Godfather

        schools = School.objects.all()
        programs = Program.objects.all()
        godfathers = Godfather.objects.all()

        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        paginator = Paginator(students, per_page)
        page_obj = paginator.get_page(page)

        context['students'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        context['status'] = status
        context['schools'] = schools
        context['programs'] = programs
        context['godfathers'] = godfathers
        return context


class EtudiantsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des étudiants"""
    template_name = 'main/etudiants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des étudiants'
        students = Student.objects.filter(status='approved')

        gender = self.request.GET.get('gender')
        school_id = self.request.GET.get('school')
        program_id = self.request.GET.get('program')
        godfather_id = self.request.GET.get('godfather')
        language = self.request.GET.get('language')


        if gender:
            students = students.filter(gender=gender)
        if school_id:
            students = students.filter(school_id=school_id)
        if program_id:
            students = students.filter(program_id=program_id)
        if godfather_id:
            students = students.filter(godfather_id=godfather_id)
        if language:
            students = students.filter(language=language)

        from schools.models import School
        from academic.models import Program
        from accounts.models import Godfather

        schools = School.objects.all()
        programs = Program.objects.all()
        godfathers = Godfather.objects.all()


        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        paginator = Paginator(students, per_page)
        page_obj = paginator.get_page(page)

        context['students'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        context['schools'] = schools
        context['programs'] = programs
        context['godfathers'] = godfathers
        return context


class DocumentsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des documents"""
    template_name = 'main/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Documents officiels'
        documents = OfficialDocument.objects.select_related('student_level__student').all()
        levels = Level.objects.all()
        academic_years = AcademicYear.objects.all()
        students = Student.objects.all()

        document_type = self.request.GET.get('document_type')
        status = self.request.GET.get('status')
        level_id = self.request.GET.get('level')
        academic_year_id = self.request.GET.get('academic_year')
        student_id = self.request.GET.get('student')
        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        if document_type:
            documents = documents.filter(type=document_type)
        if status:
            documents = documents.filter(status=status)
        if level_id:
            documents = documents.filter(student_level__level_id=level_id)
        if academic_year_id:
            documents = documents.filter(student_level__academic_year_id=academic_year_id)
        if student_id:
            documents = documents.filter(student_level__student_id=student_id)

        paginator = Paginator(documents, per_page)
        page_obj = paginator.get_page(page)

        context['documents'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['levels'] = levels
        context['academic_years'] = academic_years
        context['students'] = students
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        return context


class StatistiquesView(LoginRequiredMixin, TemplateView):
    """Vue pour les statistiques"""
    template_name = 'main/statistiques.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from academic.models import Program

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Statistiques'

        # Récupération des paramètres de filtrage
        selected_year = self.request.GET.get('year')
        selected_program = self.request.GET.get('program')

        # Années académiques disponibles
        academic_years = AcademicYear.objects.all().order_by('-start_at')
        context['academic_years'] = academic_years

        # Programmes disponibles
        programs = Program.objects.all()
        context['programs'] = programs

        # Année académique active ou sélectionnée
        if selected_year:
            try:
                current_year = AcademicYear.objects.get(id=selected_year)
            except AcademicYear.DoesNotExist:
                current_year = AcademicYear.objects.filter(is_active=True).first()
        else:
            current_year = AcademicYear.objects.filter(is_active=True).first()

        context['current_year'] = current_year
        context['selected_year'] = selected_year
        context['selected_program'] = selected_program

        # Filtrage des étudiants
        students_query = Student.objects.filter(status='approved')
        if selected_program:
            students_query = students_query.filter(program_id=selected_program)

        # Statistiques générales
        total_students = students_query.count()

        # Nouvelles inscriptions (étudiants créés cette année)
        if current_year:
            new_enrollments = students_query.filter(
                created_at__gte=current_year.start_at,
                created_at__lte=current_year.end_at
            ).count()
        else:
            new_enrollments = 0

        # Étudiants par genre
        gender_stats = students_query.values('gender').annotate(count=Count('gender'))

        # Étudiants par niveau (basé sur StudentLevel actif)
        level_stats = StudentLevel.objects.filter(
            is_active=True,
            student__status='approved'
        ).values('level__name').annotate(count=Count('student')).order_by('level__name')

        if selected_program:
            level_stats = level_stats.filter(student__program_id=selected_program)

        # Statistiques des documents
        document_stats = OfficialDocument.objects.values('status').annotate(count=Count('status'))
        total_documents = sum([stat['count'] for stat in document_stats])

        # Répartition par programme
        program_stats = students_query.values('program__name').annotate(count=Count('program')).order_by('-count')

        # Calcul des pourcentages pour les programmes
        colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#2e59d9', '#17a2b8', '#fd7e14']
        for i, stat in enumerate(program_stats):
            if total_students > 0:
                stat['percentage'] = round((stat['count'] / total_students) * 100, 1)
            else:
                stat['percentage'] = 0
            stat['color'] = colors[i % len(colors)]

        context.update({
            'total_students': total_students,
            'new_enrollments': new_enrollments,
            'gender_stats': gender_stats,
            'level_stats': level_stats,
            'document_stats': document_stats,
            'total_documents': total_documents,
            'program_stats': program_stats,
        })

        return context


class ParametresView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres"""
    template_name = 'main/parametres.html'

    def get_context_data(self, **kwargs):
        from .models import SystemSettings
        from .forms import (
            GeneralSettingsForm, AcademicSettingsForm, ProgramLevelSettingsForm,
            UserSettingsForm, DocumentSettingsForm, NotificationSettingsForm,
            DataManagementSettingsForm
        )

        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Paramètres'

        # Récupérer les paramètres système
        settings = SystemSettings.get_settings()

        # Créer les formulaires avec les données actuelles
        context['general_form'] = GeneralSettingsForm(instance=settings)
        context['academic_form'] = AcademicSettingsForm(instance=settings)
        context['program_level_form'] = ProgramLevelSettingsForm(instance=settings)
        context['user_form'] = UserSettingsForm(instance=settings)
        context['document_form'] = DocumentSettingsForm(instance=settings)
        context['notification_form'] = NotificationSettingsForm(instance=settings)
        context['data_management_form'] = DataManagementSettingsForm(instance=settings)

        # Ajouter les données pour les sélecteurs dynamiques
        context['programs'] = Program.objects.all().order_by('name')
        context['levels'] = Level.objects.all().order_by('name')

        # Ajouter les années académiques pour la sélection
        context['academic_years'] = AcademicYear.objects.all().order_by('-start_at')

        return context

    def post(self, request, *args, **kwargs):
        from .models import SystemSettings
        from .forms import (
            GeneralSettingsForm, AcademicSettingsForm, ProgramLevelSettingsForm,
            UserSettingsForm, DocumentSettingsForm, NotificationSettingsForm,
            DataManagementSettingsForm
        )
        from django.contrib import messages
        from django.shortcuts import redirect

        settings = SystemSettings.get_settings()
        form_type = request.POST.get('form_type')

        if form_type == 'general':
            form = GeneralSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres généraux mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'academic':
            form = AcademicSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres académiques mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'program_level':
            form = ProgramLevelSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres des programmes et niveaux mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'user':
            form = UserSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres utilisateurs mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'document':
            form = DocumentSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres des documents mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'notification':
            form = NotificationSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres de notification mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'data_management':
            form = DataManagementSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Paramètres de gestion des données mis à jour avec succès.')
                return redirect('main:parametres')

        elif form_type == 'academic_year':
            academic_year_id = request.POST.get('academic_year_id')
            if academic_year_id:
                try:
                    academic_year = AcademicYear.objects.get(id=academic_year_id)
                    # Mettre à jour la session avec la nouvelle année académique
                    request.session['active_academic_year_id'] = academic_year.id
                    messages.success(request, f'Année académique changée vers {academic_year.name} avec succès.')
                    return redirect('main:parametres')
                except AcademicYear.DoesNotExist:
                    messages.error(request, 'Année académique sélectionnée introuvable.')
            else:
                messages.error(request, 'Aucune année académique sélectionnée.')

        # Si on arrive ici, il y a eu une erreur
        messages.error(request, 'Erreur lors de la mise à jour des paramètres.')
        return self.get(request, *args, **kwargs)


class ProfilView(LoginRequiredMixin, TemplateView):
    """Vue pour le profil utilisateur"""
    template_name = 'main/profil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Mon Profil'

        # Informations sur l'utilisateur connecté
        user = self.request.user
        context['user'] = user

        # Statistiques personnelles si l'utilisateur est un administrateur
        if hasattr(user, 'role'):
            # Nombre d'étudiants gérés récemment
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)

            recent_approvals = Student.objects.filter(
                status='approved',
                last_updated__gte=thirty_days_ago
            ).count()

            context['recent_approvals'] = recent_approvals

            # Dernière connexion
            context['last_login'] = user.last_login

            # Date de création du compte
            context['date_joined'] = user.date_joined

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
            'progress_percentage': int((step / 3) * 100),
            'prev_step': step - 1 if step > 1 else None,
            'next_step': step + 1 if step < 3 else None,
        })
        return context

    def post(self, request, *args, **kwargs):
        step = kwargs.get('step', 1)
        form_class = self.get_form_class(step)

        if not form_class:
            return redirect('main:inscription_externe_step', step=1)

        # Pour l'étape 3 (formulaire étape 4), inclure les fichiers
        if step == 3:
            form = form_class(request.POST, request.FILES)
        else:
            form = form_class(request.POST)

        if form.is_valid():
            # Sauvegarde des données dans la session
            if 'inscription_data' not in request.session:
                request.session['inscription_data'] = {}

            # Conversion des données pour la sérialisation JSON
            cleaned_data = {}
            files_data = {}

            for key, value in form.cleaned_data.items():
                if hasattr(value, 'strftime'):  # Si c'est un objet date/datetime
                    cleaned_data[key] = value.strftime('%Y-%m-%d')
                elif hasattr(value, 'read'):  # Si c'est un fichier
                    # Stocker les fichiers séparément dans la session
                    files_data[key] = value
                else:
                    cleaned_data[key] = value

            # Ajustement pour correspondre aux vraies étapes du formulaire
            real_step = step + 1  # etape_2, etape_3, etape_4
            request.session['inscription_data'][f'etape_{real_step}'] = cleaned_data

            # Stocker les fichiers dans la session si c'est l'étape 3 (formulaire étape 4)
            if step == 3 and files_data:
                request.session['inscription_files'] = files_data

            request.session.modified = True

            # Redirection vers l'étape suivante ou confirmation
            if step < 3:  # 3 étapes au lieu de 4
                messages.success(request, f'Étape {step} complétée avec succès!')
                return redirect('main:inscription_externe_step', step=step + 1)
            else:

                session_data = request.session.get('inscription_data', {})
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

                # Creation du parrain
                godfather = Godfather.objects.create(
                    full_name=etape3_data.get('nom_tuteur', ''),
                    occupation=etape3_data.get('profession_tuteur', ''),
                    phone_number=etape3_data.get('telephone_tuteur', ''),
                    email=etape3_data.get('courriel_tuteur', ''),
                )

                # Récupération des fichiers depuis la session
                files_data = request.session.get('inscription_files', {})

                # Creation des Metadatas
                studentMetaData = StudentMetaData.objects.create(
                    mother_full_name=etape3_data.get('nom_mere', ''),
                    mother_live_city=etape3_data.get('ville_residence_mere', ''),
                    mother_email=etape3_data.get('courriel_mere', ''),
                    mother_occupation=etape3_data.get('profession_mere', ''),
                    mother_phone_number=etape3_data.get('telephone_mere', ''),
                    father_full_name=etape3_data.get('nom_pere', ''),
                    father_live_city=etape3_data.get('ville_residence_pere', ''),
                    father_email=etape3_data.get('courriel_pere', ''),
                    father_occupation=etape3_data.get('profession_pere', ''),
                    father_phone_number=etape3_data.get('telephone_pere', ''),
                    original_country=etape2_data.get('nationalite', ''),
                    original_region=etape2_data.get('region_origine', ''),
                    original_department=etape2_data.get('departement_origine', ''),
                    original_district=etape2_data.get('arrondissement_origine', ''),
                    residence_city=etape2_data.get('ville_residence', ''),
                    residence_quarter='',
                    # Ajout des fichiers d'inscription
                    preuve_baccalaureat=files_data.get('preuve_baccalaureat'),
                    acte_naissance=files_data.get('acte_naissance'),
                    releve_notes_bac=files_data.get('releve_notes_bac'),
                    bulletins_terminale=files_data.get('bulletins_terminale'),
                )

                # Création de l'étudiant
                student = Student.objects.create(
                    matricule=matricule,
                    firstname=etape2_data.get('nom', ''),
                    lastname=etape2_data.get('prenom', ''),
                    date_naiss=date_naissance,
                    status='pending',  # Statut d'inscrit
                    gender=etape2_data.get('sexe', ''),
                    phone_number=etape2_data.get('telephone', ''),
                    email=etape2_data.get('courriel', ''),
                    lang=etape2_data.get('premiere_langue_officielle', ''),
                    godfather=godfather,
                    metadata=studentMetaData
                )

                # Nettoyage de la session (données et fichiers)
                if 'inscription_data' in request.session:
                    del request.session['inscription_data']
                if 'inscription_files' in request.session:
                    del request.session['inscription_files']

                # Dernière étape, redirection vers la confirmation
                return redirect('main:inscription_externe_confirmation')
        else:
            # Formulaire invalide, affichage des erreurs
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

        # Retour à la vue avec le formulaire et les erreurs
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class NouvelleInscriptionView(LoginRequiredMixin, TemplateView):
    """Vue pour le formulaire d'inscription complet (sans étapes)"""
    template_name = 'main/nouvelle_inscription.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = InscriptionCompleteForm()

        context.update({
            'page_title': 'Nouvelle Inscription',
            'form': form,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = InscriptionCompleteForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Création de l'étudiant avec les données du formulaire
                cleaned_data = form.cleaned_data

                # Conversion de la date de naissance si nécessaire
                date_naissance = cleaned_data.get('date_naissance')
                if isinstance(date_naissance, str):
                    from datetime import datetime
                    try:
                        date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        date_naissance = None

                # Création des métadonnées de l'étudiant
                student_metadata = StudentMetaData.objects.create(
                    mother_full_name=cleaned_data.get('nom_mere', ''),
                    mother_live_city=cleaned_data.get('ville_residence_mere', ''),
                    mother_email=cleaned_data.get('courriel_mere', ''),
                    mother_occupation=cleaned_data.get('profession_mere', ''),
                    mother_phone_number=cleaned_data.get('telephone_mere', ''),
                    father_full_name=cleaned_data.get('nom_pere', ''),
                    father_live_city=cleaned_data.get('ville_residence_pere', ''),
                    father_email=cleaned_data.get('courriel_pere', ''),
                    father_occupation=cleaned_data.get('profession_pere', ''),
                    father_phone_number=cleaned_data.get('telephone_pere', ''),
                    original_country=cleaned_data.get('nationalite', 'Cameroun'),
                    original_region=cleaned_data.get('region_origine', ''),
                    original_department=cleaned_data.get('departement_origine', ''),
                    original_district=cleaned_data.get('arrondissement_origine', ''),
                    residence_city=cleaned_data.get('ville_residence', ''),
                    residence_quarter=cleaned_data.get('quartier_residence', ''),
                    # Ajout des fichiers d'inscription
                    acte_naissance=request.FILES.get('acte_naissance'),
                    certificat_nationalite=request.FILES.get('certificat_nationalite'),
                    diplome_bac=request.FILES.get('diplome_bac'),
                    releve_notes_bac=request.FILES.get('releve_notes_bac'),
                    bulletins_terminale=request.FILES.get('bulletins_terminale'),
                )

                # Création du parrain si les informations sont fournies
                godfather = None
                if cleaned_data.get('nom_tuteur') or cleaned_data.get('telephone_tuteur'):
                    godfather = Godfather.objects.create(
                        full_name=cleaned_data.get('nom_tuteur', ''),
                        occupation=cleaned_data.get('profession_tuteur', ''),
                        phone_number=cleaned_data.get('telephone_tuteur', ''),
                        email=cleaned_data.get('courriel_tuteur', ''),
                    )

                # Création de l'étudiant
                student = Student.objects.create(
                    firstname=cleaned_data.get('prenom'),
                    lastname=cleaned_data.get('nom'),
                    date_naiss=date_naissance,
                    gender='M' if cleaned_data.get('sexe') == 'M' else 'F',
                    lang='fr' if cleaned_data.get('premiere_langue_officielle') == 'francais' else 'en',
                    phone_number=cleaned_data.get('telephone'),
                    email=cleaned_data.get('courriel'),
                    status='approved',  # Statut approuvé pour les inscriptions internes
                    program=cleaned_data.get('programme'),
                    metadata=student_metadata,
                    godfather=godfather,
                )

                # Création du StudentLevel
                if cleaned_data.get('annee_academique') and cleaned_data.get('niveau'):
                    StudentLevel.objects.create(
                        student=student,
                        level=cleaned_data.get('niveau'),
                        academic_year=cleaned_data.get('annee_academique'),
                        is_active=True
                    )

                # Redirection vers la page de succès
                messages.success(request, 'Inscription éffectuée avec succès!')
                return redirect('main:etudiant_detail', pk=student.pk)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création de l\'inscription: {str(e)}')

        # Si le formulaire n'est pas valide, on le renvoie avec les erreurs
        context = self.get_context_data()
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
            'session_data': session_data,
        })

        # Nettoyage de la session
        if 'inscription_data' in self.request.session:
            del self.request.session['inscription_data']
        return context

    # def post(self, request, *args, **kwargs):
    #     """Finalisation de l'inscription"""
    #     session_data = request.session.get('inscription_data', {})

    #     if not session_data:
    #         messages.error(request, 'Aucune donnée d\'inscription trouvée. Veuillez recommencer.')
    #         return redirect('main:inscription_externe')

    #     try:
    #         # Création de l'étudiant avec les données collectées
    #         etape2_data = session_data.get('etape_2', {})
    #         etape3_data = session_data.get('etape_3', {})
    #         etape4_data = session_data.get('etape_4', {})

    #         # Conversion de la date de naissance si elle est en chaîne
    #         date_naissance = etape2_data.get('date_naissance')
    #         if isinstance(date_naissance, str):
    #             from datetime import datetime
    #             try:
    #                 date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
    #             except (ValueError, TypeError):
    #                 date_naissance = None

    #         # Génération d'un matricule temporaire
    #         import uuid
    #         matricule = f"EXT_{uuid.uuid4().hex[:8].upper()}"

    #         # Création de l'étudiant
    #         student = Student.objects.create(
    #             matricule=matricule,
    #             firstname=etape2_data.get('prenom', ''),
    #             lastname=etape2_data.get('nom', ''),
    #             date_naiss=date_naissance,
    #             status='inscrit',  # Statut d'inscrit
    #             gender=etape2_data.get('sexe', ''),
    #             phone_number=etape2_data.get('telephone', ''),
    #             email=etape2_data.get('courriel', ''),
    #         )

    #         # Nettoyage de la session
    #         if 'inscription_data' in request.session:
    #             del request.session['inscription_data']

    #         messages.success(
    #             request,
    #             f'Votre inscription a été enregistrée avec succès! '
    #             f'Votre numéro de matricule temporaire est: {matricule}. '
    #             f'Vous recevrez un email de confirmation sous peu.'
    #         )

    #         # Redirection vers une page de succès
    #         return redirect('main:inscription_externe')

    #     except Exception as e:
    #         messages.error(request, f'Une erreur est survenue lors de l\'enregistrement: {str(e)}')
    #         return self.render_to_response(self.get_context_data(**kwargs))


def etudiant_detail(request, pk):
    """
    Vue pour afficher les détails complets d'un étudiant avec toutes ses relations
    """
    # Récupération de l'étudiant avec toutes ses relations en une seule requête
    student = get_object_or_404(
        Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather'
        ).prefetch_related(
            'student_levels__level',
            'student_levels__academic_year',
            'student_levels__official_documents'
        ),
        pk=pk
    )

    # Récupération des niveaux avec leurs documents officiels
    student_levels = student.student_levels.all().order_by('-academic_year__start_at', 'level__name')

    # Statistiques sur les documents
    total_documents = 0
    available_documents = 0
    withdrawn_documents = 0

    for level in student_levels:
        docs = level.official_documents.all()
        total_documents += docs.count()
        available_documents += docs.filter(status='available').count()
        withdrawn_documents += docs.filter(status='withdrawn').count()

    context = {
        'student': student,
        'student_levels': student_levels,
        'document_stats': {
            'total': total_documents,
            'available': available_documents,
            'withdrawn': withdrawn_documents,
            'lost': total_documents - available_documents - withdrawn_documents
        }
    }

    return render(request, 'main/etudiant_detail.html', context)


@login_required
@scholar_admin_required
def generate_student_external_password(request, pk):
    """
    Vue pour générer/réinitialiser le mot de passe externe d'un étudiant
    Accessible uniquement aux responsables de scolarité
    """

    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        try:
            # Génération du nouveau mot de passe
            new_password = student.generate_external_password()

            # Message de succès avec le mot de passe (à communiquer à l'étudiant)
            messages.success(
                request,
                f"Mot de passe externe généré avec succès pour {student.firstname} {student.lastname}. "
                f"Mot de passe à communiquer à l'étudiant : <strong>{new_password}</strong>"
            )

        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du mot de passe : {str(e)}")

    return redirect('main:etudiant_detail', pk=pk)


@login_required
def etudiant_edit(request, pk):
    """
    Vue pour modifier les informations d'un étudiant
    """
    # Récupération de l'étudiant avec ses relations
    student = get_object_or_404(
        Student.objects.select_related('metadata', 'school', 'program', 'godfather'),
        pk=pk
    )

    # Créer les métadonnées si elles n'existent pas
    if not student.metadata:
        student.metadata = StudentMetaData.objects.create(original_country='Cameroun')
        student.save()

    if request.method == 'POST':
        # Traitement des formulaires
        student_form = StudentEditForm(request.POST, instance=student)
        metadata_form = StudentMetaDataEditForm(request.POST, instance=student.metadata)

        if student_form.is_valid() and metadata_form.is_valid():
            # Sauvegarder les modifications
            student_form.save()
            metadata_form.save()

            messages.success(request, 'Les informations de l\'étudiant ont été mises à jour avec succès.')
            return redirect('main:etudiant_detail', pk=student.matricule)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        # Affichage des formulaires pré-remplis
        student_form = StudentEditForm(instance=student)
        metadata_form = StudentMetaDataEditForm(instance=student.metadata)

    context = {
        'student': student,
        'student_form': student_form,
        'metadata_form': metadata_form,
    }

    return render(request, 'main/etudiant_edit.html', context)


@login_required
def document_create(request):
    """
    Vue pour créer un nouveau document officiel
    """
    if request.method == 'POST':
        form = OfficialDocumentForm(request.POST)
        if form.is_valid():
            document = form.save()
            messages.success(request, f'Le document "{document.get_type_display()}" a été créé avec succès.')
            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = OfficialDocumentForm()

    context = {
        'form': form,
        'page_title': 'Créer un document officiel',
        'action': 'create'
    }
    return render(request, 'main/document_form.html', context)


@login_required
def document_edit(request, pk):
    """
    Vue pour modifier un document officiel existant
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        form = OfficialDocumentForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save()
            messages.success(request, f'Le document "{document.get_type_display()}" a été modifié avec succès.')
            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = OfficialDocumentForm(instance=document)

    context = {
        'form': form,
        'document': document,
        'page_title': f'Modifier le document - {document.get_type_display()}',
        'action': 'edit'
    }
    return render(request, 'main/document_form.html', context)


@login_required
def document_delete(request, pk):
    """
    Vue pour supprimer un document officiel
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        document_type = document.get_type_display()
        document.delete()
        messages.success(request, f'Le document "{document_type}" a été supprimé avec succès.')
        return redirect('main:documents')

    context = {
        'document': document,
        'page_title': f'Supprimer le document - {document.get_type_display()}'
    }
    return render(request, 'main/document_delete.html', context)


@login_required
def document_toggle_status(request, pk):
    """
    Vue pour marquer un document comme déchargé/retourné
    """
    document = get_object_or_404(OfficialDocument, pk=pk)

    if request.method == 'POST':
        if document.status == 'available':
            # Marquer comme déchargé
            document.status = 'withdrawn'
            document.withdrawn_date = timezone.now().date()
            action_message = 'déchargé'
        elif document.status == 'withdrawn':
            # Marquer comme retourné
            document.status = 'returned'
            document.returned_at = timezone.now().date()
            action_message = 'retourné'
        elif document.status == 'returned':
            # Remettre comme déchargé (pour correction d'erreur)
            document.status = 'withdrawn'
            document.returned_at = None
            action_message = 'remis en statut déchargé'
        else:
            # Pour les documents perdus, on peut les remettre disponibles
            document.status = 'available'
            document.withdrawn_date = None
            document.returned_at = None
            action_message = 'remis disponible'

        document.save()
        messages.success(request, f'Le document "{document.get_type_display()}" a été {action_message} avec succès.')
        return redirect('main:documents')

    # Déterminer l'action qui sera effectuée
    if document.status == 'available':
        action = 'décharger'
        action_description = 'marquer ce document comme déchargé'
    elif document.status == 'withdrawn':
        action = 'retourner'
        action_description = 'marquer ce document comme retourné'
    elif document.status == 'returned':
        action = 'remettre en déchargé'
        action_description = 'remettre ce document en statut déchargé (correction d\'erreur)'
    else:
        action = 'remettre disponible'
        action_description = 'remettre ce document disponible'

    context = {
        'document': document,
        'action': action,
        'action_description': action_description,
        'page_title': f'{action.capitalize()} le document - {document.get_type_display()}'
    }
    return render(request, 'main/document_toggle_status.html', context)


@login_required
def document_bulk_create(request):
    """
    Vue pour la création en masse de documents officiels
    """
    if request.method == 'POST':
        form = BulkDocumentCreationForm(request.POST)
        if form.is_valid():
            # Créer les documents
            created_count, skipped_count, errors = form.create_documents()

            if created_count > 0:
                messages.success(
                    request,
                    f'{created_count} document(s) créé(s) avec succès. '
                    f'{skipped_count} document(s) ignoré(s) (déjà existants).'
                )

            if errors:
                for error in errors[:5]:  # Limiter à 5 erreurs pour l'affichage
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.warning(request, f'... et {len(errors) - 5} autres erreurs.')

            if created_count == 0 and skipped_count == 0:
                messages.warning(request, 'Aucun document créé. Vérifiez vos critères.')

            return redirect('main:documents')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = BulkDocumentCreationForm()

    context = {
        'form': form,
        'page_title': 'Création en masse de documents',
    }
    return render(request, 'main/document_bulk_create.html', context)


@login_required
def document_bulk_preview(request):
    """
    Vue AJAX pour prévisualiser les étudiants qui correspondent aux critères
    """
    if request.method == 'POST':
        form = BulkDocumentCreationForm(request.POST)
        if form.is_valid():
            students = form.get_matching_students()
            existing_count = form.get_existing_documents_count()

            # Préparer les données pour la réponse JSON
            students_data = []
            for student in students[:50]:  # Limiter à 50 pour la prévisualisation
                students_data.append({
                    'matricule': student.matricule,
                    'firstname': student.firstname,
                    'lastname': student.lastname,
                    'program': student.program.name if student.program else 'Non défini'
                })

            return JsonResponse({
                'success': True,
                'total_count': students.count(),
                'existing_count': existing_count,
                'new_count': students.count() - existing_count,
                'students': students_data,
                'showing_count': len(students_data)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def inscription_detail(request, pk):
    """
    Vue pour afficher les détails d'une inscription
    """
    student = get_object_or_404(
        Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather'
        ).prefetch_related(
            'student_levels__level',
            'student_levels__academic_year'
        ),
        pk=pk
    )

    context = {
        'student': student,
        'page_title': f'Inscription - {student.firstname} {student.lastname}'
    }

    return render(request, 'main/inscription_detail.html', context)


@login_required
def inscription_approve(request, pk):
    """
    Vue pour approuver une inscription
    """
    if request.method == 'POST':
        student = get_object_or_404(Student, pk=pk)
        student.status = 'approved'
        student.save()

        messages.success(request, f'Inscription de {student.firstname} {student.lastname} approuvée avec succès.')
        return redirect('main:inscription_detail', pk=pk)

    return redirect('main:inscriptions')


@login_required
def inscription_reject(request, pk):
    """
    Vue pour rejeter une inscription
    """
    if request.method == 'POST':
        student = get_object_or_404(Student, pk=pk)
        student.status = 'rejected'
        student.save()

        messages.warning(request, f'Inscription de {student.firstname} {student.lastname} rejetée.')
        return redirect('main:inscription_detail', pk=pk)

    return redirect('main:inscriptions')


def get_specialities_by_program(request):
    """
    Vue AJAX pour récupérer les spécialités d'un programme donné
    """
    program_id = request.GET.get('program_id')

    if not program_id:
        return JsonResponse({'specialities': []})

    try:
        # Récupérer les spécialités du programme
        specialities = Speciality.objects.filter(program_id=program_id).values('id', 'name')
        specialities_list = list(specialities)

        return JsonResponse({
            'success': True,
            'specialities': specialities_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
