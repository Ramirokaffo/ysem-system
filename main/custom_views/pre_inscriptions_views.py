from urllib.parse import urlencode

import threading
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404, reverse
from main.program_documents import build_program_document_entries
from main.utils import ensure_registration_certificate, generate_final_registration_identifiers, get_filtered_pre_inscriptions_queryset, render_student_edit, replace_student_primary_key, resolve_student_school
from students.models import Student, StudentMetaData, StudentLevel
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError

from academic.document_requirements import DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS, PROGRAM_DOCUMENT_FIELD_NAMES
from academic.models import AcademicYear, Program, Speciality
from audit.utils import log_audit_event

from accounts.models import Godfather
from schools.models import School
from students.models import Student, StudentLevel, StudentMetaData
from django.core.paginator import Paginator
from academic.models import Level

from django.contrib import messages
from django.shortcuts import redirect
from main.utils import queue_student_status_email

from main.forms import InscriptionCompleteForm, SecondaryDiplomaFormSet, UniversityLevelFormSet, InscriptionEtape2Form, InscriptionEtape3Form, InscriptionEtape4Form
from main.pdf_exports import build_pre_inscription_pdf, build_pre_inscriptions_pdf
from payments.utils import get_first_installment_for_student, get_installment_paid_amount


class PreInscriptionsView(LoginRequiredMixin, TemplateView):
    """Vue pour la gestion des pré-inscriptions"""
    template_name = 'main/preinscription/inscriptions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Pré-inscriptions'

        # Si aucun filtre academic_year n'est fourni, utiliser l'année active par défaut
        params = self.request.GET.copy()
        if not params.get('academic_year'):
            active_year = AcademicYear.get_active_year()
            if active_year:
                params['academic_year'] = str(active_year.pk)

        students = get_filtered_pre_inscriptions_queryset(
            params,
            queryset=Student.objects.select_related('school', 'program', 'godfather', 'start_level').prefetch_related('program__specialities').filter(deleted_at__isnull=True)
        )
        filtered_students_count = students.count()

        schools = School.objects.all()
        programs = Program.objects.all()
        godfathers = Godfather.objects.all()
        levels = Level.objects.all()
        academic_years = AcademicYear.objects.all().order_by('-start_at')

        per_page = self.request.GET.get('per_page', 10)
        page = self.request.GET.get('page', 1)

        paginator = Paginator(students, per_page)
        page_obj = paginator.get_page(page)

        has_filter = any(value for key, value in self.request.GET.items() if key != 'page' and key != 'per_page')
        context['students'] = page_obj.object_list
        context['filtered_students_count'] = filtered_students_count
        context['page_obj'] = page_obj
        context['has_filter'] = has_filter
        context['per_page'] = int(per_page)
        per_page_choices = [5, 10, 25, 50, 100]
        context['per_page_choices'] = per_page_choices
        context['status'] = self.request.GET.get('status')
        context['schools'] = schools
        context['programs'] = programs
        context['godfathers'] = godfathers
        context['levels'] = levels
        context['academic_years'] = academic_years
        context['selected_academic_year'] = AcademicYear.objects.filter(pk=self.request.GET.get('academic_year')).first()
        return context




class PreInscriptionExterneView(TemplateView):
    """Vue d'accueil pour l'inscription externe"""
    template_name = 'main/inscription_externe/accueil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inscription - YSEM'
        return context


class PreInscriptionExterneStepView(TemplateView):
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
                    releve_notes_last_class=files_data.get('releve_notes_last_class'),
                    justificatif_dernier_diplome=files_data.get('justificatif_dernier_diplome'),
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

                queue_student_status_email(student, 'pre_inscription')

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


class NouvellePreInscriptionView(LoginRequiredMixin, TemplateView):
    """Vue pour le formulaire d'inscription complet (sans étapes) - PUBLIQUE"""
    template_name = 'main/preinscription/nouvelle_inscription.html'

    secondary_diploma_prefix = 'secondary_diplomas'
    university_level_prefix = 'university_levels'

    def _build_secondary_diploma_formset(self, data=None):
        return SecondaryDiplomaFormSet(data=data, prefix=self.secondary_diploma_prefix)

    def _build_university_level_formset(self, data=None):
        return UniversityLevelFormSet(data=data, prefix=self.university_level_prefix)

    @staticmethod
    def _get_or_create_school(name, level):
        school_name = (name or '').strip()
        if not school_name:
            return None

        school = School.objects.filter(name__iexact=school_name, level=level).first()
        if school:
            return school

        return School.objects.create(name=school_name, level=level)

    def _save_secondary_diplomas(self, student, formset):
        secondary_diplomas = []

        for diploma_form in formset:
            if not getattr(diploma_form, 'cleaned_data', None):
                continue
            if diploma_form.cleaned_data.get('DELETE'):
                continue

            diploma = diploma_form.save(commit=False)
            diploma.student = student
            diploma.school = diploma_form.cleaned_data.get('school_existant') or self._get_or_create_school(
                diploma_form.cleaned_data.get('school_name'),
                'secondary',
            )
            diploma.save()
            secondary_diplomas.append(diploma)

        return secondary_diplomas

    def _save_university_levels(self, student, formset):
        university_levels = []

        for level_form in formset:
            if not getattr(level_form, 'cleaned_data', None):
                continue
            if level_form.cleaned_data.get('DELETE'):
                continue

            university_level = level_form.save(commit=False)
            university_level.student = student
            university_level.university = level_form.cleaned_data.get('university_existant') or self._get_or_create_school(
                level_form.cleaned_data.get('university_name'),
                'higher',
            )
            university_level.save()
            university_levels.append(university_level)

        return university_levels

    @staticmethod
    def _resolve_student_school(secondary_diplomas, university_levels=None):
        return resolve_student_school(secondary_diplomas, university_levels)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form')
        secondary_diploma_formset = kwargs.get('secondary_diploma_formset')
        university_level_formset = kwargs.get('university_level_formset')

        if form is None:
            form = InscriptionCompleteForm()
        if secondary_diploma_formset is None:
            secondary_diploma_formset = self._build_secondary_diploma_formset()
        if university_level_formset is None:
            university_level_formset = self._build_university_level_formset()

        context.update({
            'page_title': 'Nouvelle Pré-Inscription',
            'form': form,
            'secondary_diploma_formset': secondary_diploma_formset,
            'university_level_formset': university_level_formset,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = InscriptionCompleteForm(request.POST, request.FILES)
        secondary_diploma_formset = self._build_secondary_diploma_formset(request.POST)
        university_level_formset = self._build_university_level_formset(request.POST)

        form_is_valid = form.is_valid()
        secondary_diploma_formset_is_valid = secondary_diploma_formset.is_valid()
        university_level_formset_is_valid = university_level_formset.is_valid()

        if form_is_valid and secondary_diploma_formset_is_valid and university_level_formset_is_valid:
            # try:
                with transaction.atomic():
                    # Création de l'étudiant avec les données du formulaire
                    cleaned_data = form.cleaned_data
                    save_action = request.POST.get('save_action', 'save')

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
                        is_complete=cleaned_data.get('is_complete', False),
                        **{
                            field_name: request.FILES.get(field_name)
                            for field_name in PROGRAM_DOCUMENT_FIELD_NAMES
                        },
                    )

                    # Réutilisation d'un parrain existant ou création manuelle si nécessaire
                    godfather = cleaned_data.get('parrain_existant')
                    if not godfather and any(
                        cleaned_data.get(field_name)
                        for field_name in ['nom_tuteur', 'profession_tuteur', 'telephone_tuteur', 'courriel_tuteur']
                    ):
                        godfather = Godfather.objects.create(
                            full_name=cleaned_data.get('nom_tuteur', ''),
                            occupation=cleaned_data.get('profession_tuteur', ''),
                            phone_number=cleaned_data.get('telephone_tuteur', ''),
                            email=cleaned_data.get('courriel_tuteur', ''),
                        )

                    # Génération d'un matricule pour l'étudiant interne
                    import uuid
                    matricule = f"INT_{uuid.uuid4().hex[:8].upper()}"

                    # Création de l'étudiant
                    student = Student.objects.create(
                        matricule=matricule,
                        firstname=cleaned_data.get('prenom'),
                        lastname=cleaned_data.get('nom'),
                        date_naiss=date_naissance,
                        gender='M' if cleaned_data.get('sexe') == 'M' else 'F',
                        lang='fr' if cleaned_data.get('premiere_langue_officielle') == 'francais' else 'en',
                        phone_number=cleaned_data.get('telephone'),
                        email=cleaned_data.get('courriel'),
                        status='pending',  # Statut en attente pour les inscriptions internes
                        program=cleaned_data.get('programme'),
                        metadata=student_metadata,
                        godfather=godfather,
                        specialite_souhaitee_1=(
                            cleaned_data['specialite_souhaitee_1'].name
                            if cleaned_data.get('specialite_souhaitee_1') else ''
                        ),
                        specialite_souhaitee_2=(
                            cleaned_data['specialite_souhaitee_2'].name
                            if cleaned_data.get('specialite_souhaitee_2') else ''
                        ),
                        specialite_souhaitee_3=(
                            cleaned_data['specialite_souhaitee_3'].name
                            if cleaned_data.get('specialite_souhaitee_3') else ''
                        ),
                        profile_photo=cleaned_data.get('profile_photo'),
                        start_level=cleaned_data.get('niveau')
                    )

                    # Création du StudentLevel
                    if cleaned_data.get('annee_academique') and cleaned_data.get('niveau'):
                        StudentLevel.objects.create(
                            student=student,
                            level=cleaned_data.get('niveau'),
                            academic_year=cleaned_data.get('annee_academique'),
                            is_active=True
                        )

                    secondary_diplomas = self._save_secondary_diplomas(student, secondary_diploma_formset)
                    university_levels = self._save_university_levels(student, university_level_formset)

                    student_school = self._resolve_student_school(secondary_diplomas, university_levels)
                    if student_school:
                        student.school = student_school
                        student.save(update_fields=['school'])

                    # queue_student_status_email(student, 'pre_inscription')

                threading.Thread(target=queue_student_status_email, args=(student, 'pre_inscription', ), daemon=True).start()
                # Redirection vers la page de succès
                messages.success(request, 'Pré-Inscription éffectuée avec succès!')
                if save_action == 'save_and_new':
                    return redirect('main:nouvelle_inscription')
                return redirect('main:inscription_detail', pk=student.matricule)

            # except Exception as e:
            #     messages.error(request, f'Erreur lors de la pré-inscription: {str(e)}')

        # Si le formulaire n'est pas valide, on le renvoie avec les erreurs
        messages.error(request, 'Veuillez corriger les erreurs du formulaire avant de continuer.')
        context = self.get_context_data(
            form=form,
            secondary_diploma_formset=secondary_diploma_formset,
            university_level_formset=university_level_formset,
        )
        return self.render_to_response(context)


class PreInscriptionExterneConfirmationView(TemplateView):
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



@login_required
def pre_inscription_detail(request, pk):
    """
    Vue pour afficher les détails d'une pré-inscription
    """
    student = get_object_or_404(
        Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather'
        ).prefetch_related(
            'secondary_diplomas__school',
            'student_levels__level',
            'student_levels__academic_year',
            'student_levels__speciality',
            'university_levels__university',
            'program__specialities',
        ),
        matricule=pk
    )

    active_student_level = student.student_levels.select_related('speciality').filter(is_active=True).first()
    program_specialities = []
    if student.program_id:
        program_specialities = sorted(student.program.specialities.all(), key=lambda speciality: speciality.name.lower())

    # _send_student_status_email(student, "pre_inscription")

    context = {
        'student': student,
        'active_student_level': active_student_level,
        'program_specialities': program_specialities,
        'page_title': f'Pré-Inscription - {student.firstname} {student.lastname}',
        'document_entries': build_program_document_entries(
            program=student.program,
            metadata=student.metadata,
            fallback_visible_fields=DEFAULT_REQUIRED_PROGRAM_DOCUMENT_FIELDS,
        ),
    }

    return render(request, 'main/preinscription/inscription_detail.html', context)


@login_required
def pre_inscription_print_pdf(request, pk):
    """Génère un PDF administratif combiné pour une pré-inscription."""
    student = get_object_or_404(
        Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather'
        ).prefetch_related(
            'secondary_diplomas__school',
            'student_levels__level',
            'student_levels__academic_year',
            'university_levels__university',
        ),
        matricule=pk
    )

    pdf_content = build_pre_inscription_pdf(student)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="preinscription_{student.matricule}.pdf"'
    return response


@login_required
def pre_inscriptions_print_pdf(request):
    """Génère un PDF combiné pour toutes les pré-inscriptions filtrées."""
    students = get_filtered_pre_inscriptions_queryset(
        request.GET,
        queryset=Student.objects.select_related(
            'metadata',
            'school',
            'program',
            'godfather'
        ).prefetch_related(
            'secondary_diplomas__school',
            'student_levels__level',
            'student_levels__academic_year',
            'university_levels__university',
        )
    )

    pdf_content = build_pre_inscriptions_pdf(students)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="preinscriptions_filtrees.pdf"'
    return response


@login_required
def pre_inscription_edit(request, pk):
    """Vue pour modifier entièrement une pré-inscription."""
    student = get_object_or_404(
        Student.objects.select_related('metadata', 'school', 'program', 'godfather'),
        matricule=pk
    )

    return render_student_edit(
        request=request,
        student=student,
        detail_route_name='main:inscription_detail',
        page_title='Modifier la pré-inscription',
        success_message='La pré-inscription a été mise à jour avec succès.',
        back_link_label='Retour à la pré-inscription',
    )


@login_required
def pre_inscription_approve(request, pk):
    """
    Vue pour approuver une inscription
    """
    if request.method != 'POST':
        return redirect('main:inscriptions')

    student = get_object_or_404(Student.objects.select_related('program'), matricule=pk)
    student_level = student.get_active_level()

    if not student_level:
        messages.error(request, "Impossible d'approuver cette pré-inscription : aucun niveau actif n'est défini.")
        return redirect('main:inscription_detail', pk=pk)

    speciality_id = request.POST.get('speciality')
    program_specialities = Speciality.objects.filter(program_id=student.program_id).order_by('name') if student.program_id else Speciality.objects.none()
    requires_speciality = program_specialities.exists()

    selected_speciality = None
    if requires_speciality:
        if not speciality_id:
            messages.error(request, "Veuillez sélectionner une spécialité avant d'approuver la pré-inscription.")
            return redirect('main:inscription_detail', pk=pk)

        selected_speciality = program_specialities.filter(pk=speciality_id).first()
        if not selected_speciality:
            messages.error(request, "La spécialité sélectionnée ne correspond pas au programme de l'étudiant.")
            return redirect('main:inscription_detail', pk=pk)
    elif speciality_id:
        selected_speciality = Speciality.objects.filter(pk=speciality_id, program_id=student.program_id).first()
        if not selected_speciality:
            messages.error(request, "La spécialité sélectionnée ne correspond pas au programme de l'étudiant.")
            return redirect('main:inscription_detail', pk=pk)

    with transaction.atomic():
        if selected_speciality:
            student_level.speciality = selected_speciality
            student_level.save()

        student.status = 'approved'
        student.save(update_fields=['status'])

    queue_student_status_email(student, 'pre_inscription_approved')

    messages.success(request, f'Pré-inscription de {student.firstname} {student.lastname} approuvée avec succès.')
    return redirect('main:inscription_detail', pk=pk)


@login_required
def pre_inscription_mark_complete(request, pk):
    """Marque le dossier d'une pré-inscription comme complet."""
    if request.method != 'POST':
        return redirect('main:inscriptions')

    student = get_object_or_404(Student.objects.select_related('metadata'), matricule=pk)

    if not student.metadata_id:
        messages.error(request, "Aucune métadonnée n'est associée à cette pré-inscription.")
        return redirect('main:inscription_detail', pk=pk)

    if student.metadata.is_complete:
        messages.info(request, 'Ce dossier est déjà marqué comme complet.')
        return redirect('main:inscription_detail', pk=pk)

    student.metadata.is_complete = True
    student.metadata.save(update_fields=['is_complete'])

    log_audit_event(
        category='business',
        action='update',
        actor=request.user,
        instance=student,
        changes={
            'is_complete': {'from': False, 'to': True},
        },
        context={
            'operation': 'mark_pre_inscription_complete',
            'metadata_id': student.metadata_id,
        },
        message="Le dossier de pré-inscription a été marqué comme complet.",
    )

    messages.success(request, f'Le dossier de {student.firstname} {student.lastname} a été marqué comme complet.')
    return redirect('main:inscription_detail', pk=pk)


@login_required
def pre_inscription_reject(request, pk):
    """
    Vue pour rejeter une pré-inscription
    """
    if request.method == 'POST':
        student = get_object_or_404(Student, matricule=pk)
        student.status = 'rejected'
        student.save()

        messages.warning(request, f'Inscription de {student.firstname} {student.lastname} rejetée.')
        return redirect('main:inscription_detail', pk=pk)

    return redirect('main:inscriptions')


@login_required
def pre_inscription_delete(request, pk):
    """
    Vue pour supprimer une pré-inscription (soft delete)
    Marque le champ deleted_at à la date actuelle
    """
    if request.method == 'POST':
        student = get_object_or_404(Student, matricule=pk)
        from django.utils import timezone
        student.deleted_at = timezone.now()
        student.save()

        messages.success(request, f'Pré-inscription de {student.firstname} {student.lastname} supprimée.')
        return redirect('main:inscriptions')

    return redirect('main:inscriptions')


@login_required
def pre_inscription_register(request, pk):
    """Transforme une pré-inscription approuvée en étudiant inscrit avec matricule définitif."""
    if request.method != 'POST':
        return redirect('main:inscriptions')

    student = get_object_or_404(
        Student.objects.select_related('metadata', 'school', 'program', 'godfather').prefetch_related(
            'student_levels__level',
            'student_levels__academic_year',
        ),
        matricule=pk,
    )

    if student.status != 'approved':
        messages.error(request, "Seules les pré-inscriptions approuvées peuvent être inscrites définitivement.")
        return redirect('main:inscription_detail', pk=pk)

    student_level = student.get_active_level()
    if not student_level:
        messages.error(request, "Impossible d'inscrire cet étudiant : aucun niveau actif n'est défini.")
        return redirect('main:inscription_detail', pk=pk)

    if not student.program_id:
        messages.error(request, "Impossible d'inscrire cet étudiant : aucun programme n'est défini.")
        return redirect('main:inscription_detail', pk=pk)

    first_installment = get_first_installment_for_student(
        student=student,
        academic_year=student_level.academic_year,
    )
    if not first_installment:
        messages.error(
            request,
            "Impossible d'inscrire cet étudiant : aucune première tranche de frais de scolarité n'est configurée pour son programme et son niveau actif.",
        )
        return redirect('main:inscription_detail', pk=pk)

    paid_amount = get_installment_paid_amount(
        student=student,
        installment=first_installment,
        academic_year=student_level.academic_year,
    )
    installment_amount = (first_installment.amount or Decimal('0.00')).quantize(Decimal('0.01'))

    if paid_amount < installment_amount:
        query_string = urlencode({
            'student': student.pk,
            'academic_year': student_level.academic_year_id,
            'category': 'frais_scolarite',
            'installment': first_installment.pk,
            'registration_flow': 1,
            'registration_student_id': student.pk,
            'registration_academic_year_id': student_level.academic_year_id,
            'registration_installment_id': first_installment.pk,
            'return_url': reverse('main:inscription_detail', kwargs={'pk': pk}),
        })
        messages.warning(
            request,
            "L'inscription définitive exige que la première tranche des frais de scolarité soit soldée. Veuillez enregistrer ce paiement pour poursuivre.",
        )
        return redirect(f"{reverse('payments:payment_create')}?{query_string}")

    try:
        with transaction.atomic():
            dossier_number, final_matricule = generate_final_registration_identifiers(student)
            registered_student = replace_student_primary_key(student, final_matricule, dossier_number)
            registered_student_level = registered_student.get_active_level()
            if registered_student_level:
                registered_student_level.mark_as_registered()
            ensure_registration_certificate(registered_student)
            # queue_student_status_email(registered_student, 'registration')
            threading.Thread(target=queue_student_status_email, args=(registered_student, 'registration', ), daemon=True).start()
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if exc.messages else str(exc))
        return redirect('main:inscription_detail', pk=pk)

    messages.success(
        request,
        f"L'étudiant {student.firstname} {student.lastname} a été inscrit avec succès sous le matricule {final_matricule}.",
    )
    return redirect('students:etudiant_detail', pk=final_matricule)

