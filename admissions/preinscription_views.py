"""Wizard de pré-inscription du portail d'admission (3 étapes).

Chaque étape est sauvegardée dans la base : le candidat peut quitter et revenir
à tout moment poursuivre son dossier. Deux actions sont disponibles sur chaque
étape :
    * ``save_draft`` — sauvegarde partielle (validation relâchée)
    * ``next``       — validation stricte puis passage à l'étape suivante
                       (à l'étape 3, équivaut à la soumission finale)
"""
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET

from academic.document_requirements import (
    PROGRAM_DOCUMENT_FIELD_NAMES,
    PROGRAM_DOCUMENTS_BY_FIELD,
)
from academic.models import AcademicYear, Program, Speciality
from main.program_documents import (
    build_program_document_entries,
    get_required_program_document_field_names,
)
from main.utils import (
    get_or_create_school,
    queue_student_status_email,
    resolve_student_school,
    save_secondary_diplomas,
    save_university_levels,
)
from students.models import Student, StudentLevel, StudentMetaData

from .decorators import SESSION_STUDENT_ID, candidate_required
from .preinscription_forms import (
    SecondaryDiplomaPortalFormSet,
    Step1IdentificationForm,
    Step2FamilyForm,
    Step3CursusForm,
    Step4DocumentsForm,
    UniversityLevelPortalFormSet,
)


SECONDARY_DIPLOMA_PREFIX = 'secondary_diplomas'
UNIVERSITY_LEVEL_PREFIX = 'university_levels'

STEP_TITLES = {
    1: "Identification du candidat",
    2: "Informations familiales",
    3: "Cursus et programme",
    4: "Pièces justificatives",
}
STEP_SUBTITLES = {
    1: "Renseignez vos informations personnelles et coordonnées.",
    2: "Informations sur vos parents.",
    3: "Choisissez votre programme et renseignez votre cursus académique.",
    4: "Déposez vos pièces justificatives puis soumettez votre pré-inscription.",
}
TOTAL_STEPS = 4


def _get_student_or_logout(request):
    student_id = request.session.get(SESSION_STUDENT_ID)
    if not student_id:
        return None
    return Student.objects.filter(pk=student_id).select_related('metadata').first()


def _ensure_metadata(student):
    if student.metadata_id:
        return student.metadata
    metadata = StudentMetaData.objects.create(
        original_country='',
        is_online_registration=True,
    )
    student.metadata = metadata
    student.save(update_fields=['metadata'])
    return metadata


def _step_url(step):
    from django.urls import reverse
    return reverse('admissions:preinscription_step', args=[step])


def _build_step_context(step, student, **extra):
    context = {
        'student': student,
        'step': step,
        'total_steps': TOTAL_STEPS,
        'steps': [
            {
                'index': i,
                'title': STEP_TITLES[i],
                'reached': student.preinscription_step >= i,
                'current': i == step,
                'accessible': i <= student.preinscription_step + 1,
                'url': _step_url(i),
            }
            for i in range(1, TOTAL_STEPS + 1)
        ],
        'step_title': STEP_TITLES[step],
        'step_subtitle': STEP_SUBTITLES[step],
        'is_submitted': bool(student.metadata and student.metadata.is_complete),
    }
    context.update(extra)
    return context


@method_decorator([never_cache, csrf_protect, candidate_required], name='dispatch')
class PreinscriptionStepView(View):
    """Vue unifiée du wizard : dispatch sur ``step`` (1, 2, 3)."""

    template_name = 'admissions/preinscription_step.html'

    def dispatch(self, request, step, *args, **kwargs):
        try:
            step = int(step)
        except (TypeError, ValueError):
            return redirect('admissions:preinscription_step', step=1)

        if step < 1 or step > TOTAL_STEPS:
            return redirect('admissions:preinscription_step', step=1)

        student = _get_student_or_logout(request)
        if not student:
            return redirect('admissions:logout')

        # Une fois la pré-inscription soumise (is_complete=True), on bascule sur le récap.
        if student.metadata and student.metadata.is_complete:
            return redirect('admissions:preinscription_recap')

        # Le candidat ne peut accéder qu'aux étapes déjà atteintes + la suivante.
        max_allowed = min(student.preinscription_step + 1, TOTAL_STEPS)
        if step > max_allowed:
            messages.info(
                request,
                f"Veuillez d'abord compléter l'étape {max_allowed} avant de continuer."
            )
            return redirect('admissions:preinscription_step', step=max_allowed)

        self.student = student
        self.metadata = _ensure_metadata(student)
        return super().dispatch(request, step, *args, **kwargs)

    def get(self, request, step):
        handler = getattr(self, f'_render_step{step}')
        return handler(request)

    def post(self, request, step):
        handler = getattr(self, f'_handle_step{step}')
        return handler(request)

    # ------------------------------------------------------------------ Step 1
    def _initial_step1(self):
        s, m = self.student, self.metadata
        return {
            'nom': s.lastname or '',
            'prenom': s.firstname or '',
            'date_naissance': s.date_naiss,
            'sexe': s.gender or '',
            'premiere_langue_officielle': 'francais' if (s.lang or 'fr') == 'fr' else 'anglais',
            'telephone': s.phone_number or '',
            'pays_origine': m.original_country or 'Cameroun',
            'region_origine': m.original_region or '',
            'departement_origine': m.original_department or '',
            'arrondissement_origine': m.original_district or '',
            'ville_residence': m.residence_city or '',
            'quartier_residence': m.residence_quarter or '',
        }

    def _render_step1(self, request, form=None):
        if form is None:
            form = Step1IdentificationForm(initial=self._initial_step1())
        return render(request, self.template_name, _build_step_context(
            1, self.student, form=form,
        ))

    def _handle_step1(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        form = Step1IdentificationForm(request.POST, request.FILES, partial=partial)
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step1(request, form=form)

        cd = form.cleaned_data
        s, m = self.student, self.metadata
        s.lastname = cd.get('nom') or s.lastname
        s.firstname = cd.get('prenom') or s.firstname
        if cd.get('date_naissance'):
            s.date_naiss = cd['date_naissance']
        if cd.get('sexe'):
            s.gender = cd['sexe']
        langue = cd.get('premiere_langue_officielle')
        if langue:
            s.lang = 'fr' if langue == 'francais' else 'en'
        if cd.get('telephone'):
            s.phone_number = cd['telephone']
        if cd.get('profile_photo'):
            s.profile_photo = cd['profile_photo']

        m.original_country = cd.get('pays_origine') or m.original_country
        m.original_region = cd.get('region_origine') or m.original_region
        m.original_department = cd.get('departement_origine') or m.original_department
        m.original_district = cd.get('arrondissement_origine') or m.original_district
        m.residence_city = cd.get('ville_residence') or m.residence_city
        m.residence_quarter = cd.get('quartier_residence') or m.residence_quarter

        with transaction.atomic():
            m.save()
            if not partial and s.preinscription_step < 1:
                s.preinscription_step = 1
            s.save()

        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('admissions:preinscription_step', step=1)

        messages.success(request, "Étape 1 enregistrée.")
        return redirect('admissions:preinscription_step', step=2)

    # ------------------------------------------------------------------ Step 2
    def _initial_step2(self):
        m = self.metadata
        return {
            'nom_pere': m.father_full_name or '',
            'profession_pere': m.father_occupation or '',
            'telephone_pere': m.father_phone_number or '',
            'courriel_pere': m.father_email or '',
            'ville_residence_pere': m.father_live_city or '',
            'nom_mere': m.mother_full_name or '',
            'profession_mere': m.mother_occupation or '',
            'telephone_mere': m.mother_phone_number or '',
            'courriel_mere': m.mother_email or '',
            'ville_residence_mere': m.mother_live_city or '',
        }

    def _render_step2(self, request, form=None):
        if form is None:
            form = Step2FamilyForm(initial=self._initial_step2())
        return render(request, self.template_name, _build_step_context(
            2, self.student, form=form,
        ))

    def _handle_step2(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        form = Step2FamilyForm(request.POST, partial=partial)
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step2(request, form=form)

        cd = form.cleaned_data
        m = self.metadata
        m.father_full_name = cd.get('nom_pere') or ''
        m.father_occupation = cd.get('profession_pere') or ''
        m.father_phone_number = cd.get('telephone_pere') or ''
        m.father_email = cd.get('courriel_pere') or ''
        m.father_live_city = cd.get('ville_residence_pere') or ''
        m.mother_full_name = cd.get('nom_mere') or ''
        m.mother_occupation = cd.get('profession_mere') or ''
        m.mother_phone_number = cd.get('telephone_mere') or ''
        m.mother_email = cd.get('courriel_mere') or ''
        m.mother_live_city = cd.get('ville_residence_mere') or ''

        with transaction.atomic():
            m.save()
            if not partial and self.student.preinscription_step < 2:
                self.student.preinscription_step = 2
                self.student.save(update_fields=['preinscription_step'])

        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('admissions:preinscription_step', step=2)

        messages.success(request, "Étape 2 enregistrée.")
        return redirect('admissions:preinscription_step', step=3)

    # ------------------------------------------------------------------ Step 3
    def _initial_step3(self):
        s = self.student
        return {
            'programme': s.program_id,
            'niveau': s.start_level_id,
            'specialite_souhaitee_1': self._speciality_id(s.program_id, s.specialite_souhaitee_1),
            'specialite_souhaitee_2': self._speciality_id(s.program_id, s.specialite_souhaitee_2),
            'specialite_souhaitee_3': self._speciality_id(s.program_id, s.specialite_souhaitee_3),
        }

    @staticmethod
    def _speciality_id(program_id, speciality_name):
        if not (program_id and speciality_name):
            return None
        from academic.models import Speciality
        sp = Speciality.objects.filter(program_id=program_id, name=speciality_name).first()
        return sp.pk if sp else None

    def _build_step3_formsets(self, data=None, partial=False):
        sd_initial = [
            {
                'name': d.name, 'serie': d.serie or '', 'obtained_year': d.obtained_year,
                'mention': d.mention or '', 'school_existant': d.school_id,
            }
            for d in self.student.secondary_diplomas.all().order_by('obtained_year')
        ] if data is None else None
        ul_initial = [
            {
                'level_name': u.level_name, 'diploma_name': u.diploma_name or '',
                'speciality': u.speciality or '', 'academic_year': u.academic_year or '',
                'university_existant': u.university_id,
            }
            for u in self.student.university_levels.all().order_by('academic_year')
        ] if data is None else None

        sd_formset_cls = type(
            'SecondaryDiplomaPortalFormSetExtra',
            (SecondaryDiplomaPortalFormSet,),
            {'extra': 1 if data is None and not sd_initial else 0},
        )
        ul_formset_cls = type(
            'UniversityLevelPortalFormSetExtra',
            (UniversityLevelPortalFormSet,),
            {'extra': 0},
        )
        sd_formset = sd_formset_cls(
            data=data, prefix=SECONDARY_DIPLOMA_PREFIX, initial=sd_initial or None,
            form_kwargs={'partial': partial},
        )
        ul_formset = ul_formset_cls(
            data=data, prefix=UNIVERSITY_LEVEL_PREFIX, initial=ul_initial or None,
            form_kwargs={'partial': partial},
        )
        return sd_formset, ul_formset

    def _resolve_program(self, data):
        program_value = data.get('programme') if data else None
        if not program_value:
            return self.student.program
        try:
            return Program.objects.filter(pk=int(program_value)).first()
        except (TypeError, ValueError):
            return self.student.program

    def _render_step3(self, request, form=None, sd_formset=None, ul_formset=None):
        if form is None:
            form = Step3CursusForm(
                initial=self._initial_step3(),
                program=self.student.program,
            )
        if sd_formset is None or ul_formset is None:
            sd_formset, ul_formset = self._build_step3_formsets()
        return render(request, self.template_name, _build_step_context(
            3, self.student,
            form=form, sd_formset=sd_formset, ul_formset=ul_formset,
        ))

    def _handle_step3(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        program = self._resolve_program(request.POST)
        form = Step3CursusForm(
            request.POST, partial=partial, program=program,
        )
        sd_formset, ul_formset = self._build_step3_formsets(data=request.POST, partial=partial)

        form_ok = form.is_valid()
        sd_ok = sd_formset.is_valid()
        ul_ok = ul_formset.is_valid()

        if not (form_ok and sd_ok and ul_ok):
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step3(request, form=form, sd_formset=sd_formset, ul_formset=ul_formset)

        cd = form.cleaned_data
        s = self.student

        with transaction.atomic():
            if cd.get('programme'):
                s.program = cd['programme']
            if cd.get('niveau'):
                s.start_level = cd['niveau']
            s.specialite_souhaitee_1 = cd['specialite_souhaitee_1'].name if cd.get('specialite_souhaitee_1') else ''
            s.specialite_souhaitee_2 = cd['specialite_souhaitee_2'].name if cd.get('specialite_souhaitee_2') else ''
            s.specialite_souhaitee_3 = cd['specialite_souhaitee_3'].name if cd.get('specialite_souhaitee_3') else ''

            # Diplômes & cursus : on réécrit l'ensemble à partir des formsets,
            # même en mode brouillon (les lignes incomplètes sont ignorées).
            s.secondary_diplomas.all().delete()
            s.university_levels.all().delete()
            secondary = save_secondary_diplomas(s, sd_formset)
            university = save_university_levels(s, ul_formset)
            school = resolve_student_school(secondary, university)
            if school and s.school_id != school.pk:
                s.school = school

            if not partial:
                # StudentLevel : créer/mettre à jour pour l'année académique active.
                annee = AcademicYear.get_active_year()
                niveau = cd.get('niveau')
                if annee and niveau:
                    StudentLevel.objects.update_or_create(
                        student=s, level=niveau, academic_year=annee,
                        defaults={'is_active': True},
                    )

                if s.preinscription_step < 3:
                    s.preinscription_step = 3

            s.save()

        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('admissions:preinscription_step', step=3)

        messages.success(request, "Étape 3 enregistrée.")
        return redirect('admissions:preinscription_step', step=4)

    # ------------------------------------------------------------------ Step 4
    def _render_step4(self, request, form=None):
        if form is None:
            form = Step4DocumentsForm(
                program=self.student.program,
                metadata=self.metadata,
            )
        return render(request, self.template_name, _build_step_context(
            4, self.student, form=form,
        ))

    def _handle_step4(self, request):
        action = request.POST.get('save_action', 'next')
        partial = (action == 'save_draft')
        form = Step4DocumentsForm(
            request.POST, request.FILES,
            partial=partial,
            program=self.student.program,
            metadata=self.metadata,
        )
        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            return self._render_step4(request, form=form)

        s, m = self.student, self.metadata

        with transaction.atomic():
            # Documents : on n'écrase pas un fichier existant par un champ vide.
            for field_name in PROGRAM_DOCUMENT_FIELD_NAMES:
                uploaded = request.FILES.get(field_name)
                if uploaded:
                    setattr(m, field_name, uploaded)

            if not partial and s.preinscription_step < 4:
                s.preinscription_step = 4
                s.save(update_fields=['preinscription_step'])
            m.save()

        if partial:
            messages.success(request, "Brouillon enregistré.")
            return redirect('admissions:preinscription_step', step=4)

        messages.success(
            request,
            "Documents enregistrés. Vérifiez votre dossier avant la soumission définitive.",
        )
        return redirect('admissions:preinscription_review')


@method_decorator([never_cache, csrf_protect, candidate_required], name='dispatch')
class PreinscriptionReviewView(View):
    """Récapitulatif avant soumission définitive du dossier."""
    template_name = 'admissions/preinscription_review.html'

    def dispatch(self, request, *args, **kwargs):
        student = _get_student_or_logout(request)
        if not student:
            return redirect('admissions:logout')

        # Si déjà soumis, on bascule sur le récap post-soumission.
        if student.metadata and student.metadata.is_complete:
            return redirect('admissions:preinscription_recap')

        # Accessible uniquement après avoir validé l'étape 4.
        if student.preinscription_step < TOTAL_STEPS:
            messages.info(
                request,
                "Veuillez d'abord compléter toutes les étapes du formulaire.",
            )
            next_step = min(student.preinscription_step + 1, TOTAL_STEPS)
            return redirect('admissions:preinscription_step', step=next_step)

        self.student = student
        self.metadata = _ensure_metadata(student)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, self._context())

    def post(self, request):
        s, m = self.student, self.metadata

        # Re-vérification serveur des documents obligatoires avant l'envoi.
        required_fields = get_required_program_document_field_names(s.program)
        missing = [
            PROGRAM_DOCUMENTS_BY_FIELD[fn]['label']
            for fn in required_fields
            if not getattr(m, fn, None)
        ]
        if missing:
            messages.error(
                request,
                "Pièces obligatoires manquantes : " + ", ".join(missing) + ".",
            )
            return redirect('admissions:preinscription_step', step=4)

        with transaction.atomic():
            m.is_complete = True
            m.save(update_fields=['is_complete'])
            queue_student_status_email(s, 'pre_inscription')

        messages.success(request, "Votre pré-inscription a été soumise avec succès.")
        return redirect('admissions:preinscription_recap')

    def _context(self):
        s = self.student
        document_entries = [
            entry
            for entry in build_program_document_entries(
                program=s.program, metadata=self.metadata, force_optional=False,
            )
            if entry['should_display']
        ]
        missing_documents = [
            entry['label']
            for entry in document_entries
            if entry['is_required'] and not entry['has_file']
        ]
        return {
            'student': s,
            'metadata': self.metadata,
            'secondary_diplomas': s.secondary_diplomas.all(),
            'university_levels': s.university_levels.all(),
            'document_entries': document_entries,
            'missing_documents': missing_documents,
            'step4_url': _step_url(4),
            'step1_url': _step_url(1),
        }


@method_decorator([never_cache, candidate_required], name='dispatch')
class PreinscriptionRecapView(View):
    """Récapitulatif après soumission finale."""
    template_name = 'admissions/preinscription_recap.html'

    def get(self, request):
        student = _get_student_or_logout(request)
        if not student:
            return redirect('admissions:logout')
        return render(request, self.template_name, {
            'student': student,
            'metadata': student.metadata,
            'secondary_diplomas': student.secondary_diplomas.all(),
            'university_levels': student.university_levels.all(),
        })


@require_GET
@candidate_required
def preinscription_specialities(request):
    """Retourne en JSON les spécialités liées à un programme donné.

    Utilisé par l'étape 3 du wizard pour filtrer dynamiquement les listes de
    spécialités selon le programme visé sélectionné côté client.
    """
    programme_id = request.GET.get('programme')
    items = []
    if programme_id:
        try:
            programme_pk = int(programme_id)
        except (TypeError, ValueError):
            programme_pk = None
        if programme_pk:
            items = list(
                Speciality.objects.filter(program_id=programme_pk)
                .order_by('name')
                .values('id', 'name')
            )
    return JsonResponse({'items': items})
